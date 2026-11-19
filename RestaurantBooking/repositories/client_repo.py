from repositories.database import get_connection
from models.client import Client
from datetime import datetime

class ClientRepository:
    def find_by_email(self, email: str) -> Client | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Client(
                id=row["id"],
                name=row["name"],
                phone=row["phone"],
                email=row["email"],
                password_hash=row["password_hash"],
                registration_date=datetime.fromisoformat(row["registration_date"])
            )
        return None

    def save(self, name: str, phone: str, email: str, password_hash: str) -> Client:
        conn = get_connection()
        cursor = conn.cursor()
        reg_date = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO clients (name, phone, email, password_hash, registration_date) VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, password_hash, reg_date)
        )
        conn.commit()
        client_id = cursor.lastrowid
        conn.close()
        return Client(client_id, name, phone, email, password_hash, datetime.fromisoformat(reg_date))