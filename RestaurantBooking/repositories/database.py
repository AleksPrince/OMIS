import sqlite3
import hashlib
import secrets

DB_NAME = "booking.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            registration_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            working_hours TEXT,
            admin_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            seats INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Свободен',
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            guests INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Создана',
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (table_id) REFERENCES tables(id)
        )
    """)

    # Новое: администраторы ресторанов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """)

    # Новое: системные администраторы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conn.commit()

    # Тестовые данные
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO restaurants (name, address, phone, working_hours) VALUES (?, ?, ?, ?)",
            ("Ресторан «Название»", "ул. Примерная, 1",
             "+375 (29) 123-45-67", "10:00 - 23:00"),
        )
        rest_id = cursor.lastrowid
        for i in range(1, 9):
            seats = 4 if i <= 6 else 6
            cursor.execute(
                "INSERT INTO tables (restaurant_id, number, seats) VALUES (?, ?, ?)",
                (rest_id, i, seats),
            )
        conn.commit()

    # Тестовый админ ресторана: admin@rest.com / admin123
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM restaurants LIMIT 1")
        rest_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO admins (restaurant_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (rest_id, "Администратор", "admin@rest.com", _hash_password("admin123")),
        )

    # Тестовый системный админ: sys@rest.com / sys123
    cursor.execute("SELECT COUNT(*) FROM system_admins")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO system_admins (name, email, password_hash) VALUES (?, ?, ?)",
            ("Системный администратор", "sys@rest.com", _hash_password("sys123")),
        )

    conn.commit()
    conn.close()