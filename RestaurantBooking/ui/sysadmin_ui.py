import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import secrets
from repositories.database import get_connection


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()


def _generate_hours():
    """Список часов от 00:00 до 23:00 с шагом 30 минут."""
    hours = []
    for h in range(24):
        hours.append(f"{h:02d}:00")
        hours.append(f"{h:02d}:30")
    return hours


class SysAdminUI:
    def __init__(self, root, sysadmin: dict, on_logout):
        self.root = root
        self.sysadmin = sysadmin
        self.on_logout = on_logout

        self.root.title(f"Системный администратор — {sysadmin['name']}")
        self.root.geometry("1000x650")
        self.root.resizable(True, True)

        # ---------- Шапка ----------
        header = tk.Frame(self.root, bg="#f0f0f0", height=50)
        header.pack(fill="x")
        tk.Label(header, text="Системный администратор",
                 font=("Arial", 13, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=15, pady=10)
        tk.Button(header, text="Выйти", command=self.on_logout).pack(side=tk.RIGHT, padx=15, pady=10)

        # ---------- Основной контейнер: две колонки ----------
        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=15, pady=10)

        # Левая колонка — форма регистрации
        left = tk.Frame(body)
        left.pack(side=tk.LEFT, fill="y", padx=(0, 20))

        # Правая колонка — таблица существующих ресторанов
        right = tk.Frame(body)
        right.pack(side=tk.RIGHT, fill="both", expand=True)

        # =============== ЛЕВАЯ КОЛОНКА ===============
        tk.Label(left, text="Регистрация ресторана",
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2,
                                                  pady=(0, 15), sticky="w")

        fields = [
            ("Название", "name"),
            ("Адрес", "address"),
            ("Телефон", "phone"),
            ("Email администратора", "admin_email"),
            ("Пароль администратора", "admin_password"),
        ]
        self.entries = {}
        row = 1
        for label, key in fields:
            tk.Label(left, text=label, anchor="w", width=22).grid(row=row, column=0, pady=6, sticky="w")
            show = "*" if "password" in key else ""
            e = ttk.Entry(left, width=32, show=show)
            e.grid(row=row, column=1, pady=6, sticky="w")
            self.entries[key] = e
            row += 1

        # Часы работы — два Combobox
        tk.Label(left, text="Часы работы", anchor="w", width=22).grid(row=row, column=0, pady=6, sticky="w")
        hours_frame = tk.Frame(left)
        hours_frame.grid(row=row, column=1, pady=6, sticky="w")
        row += 1

        hours = _generate_hours()
        tk.Label(hours_frame, text="с").pack(side=tk.LEFT)
        self.hours_open = ttk.Combobox(hours_frame, values=hours, state="readonly", width=7)
        self.hours_open.set("10:00")
        self.hours_open.pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(hours_frame, text="по").pack(side=tk.LEFT)
        self.hours_close = ttk.Combobox(hours_frame, values=hours, state="readonly", width=7)
        self.hours_close.set("23:00")
        self.hours_close.pack(side=tk.LEFT, padx=(5, 0))

        # Кнопка регистрации
        tk.Button(left, text="Зарегистрировать", width=25,
                  command=self.register_restaurant).grid(row=row, column=1, pady=25, sticky="w")

        # =============== ПРАВАЯ КОЛОНКА ===============
        tk.Label(right, text="Существующие рестораны",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        tree_frame = tk.Frame(right)
        tree_frame.pack(fill="both", expand=True)

        columns = ("id", "name", "address", "hours")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Название")
        self.tree.heading("address", text="Адрес")
        self.tree.heading("hours", text="Часы работы")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("address", width=250)
        self.tree.column("hours", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        self.refresh_restaurants()

    def refresh_restaurants(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, address, working_hours FROM restaurants ORDER BY id")
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=(
                row["id"], row["name"], row["address"], row["working_hours"] or ""
            ))
        conn.close()

    def register_restaurant(self):
        name = self.entries["name"].get().strip()
        address = self.entries["address"].get().strip()
        phone = self.entries["phone"].get().strip()
        admin_email = self.entries["admin_email"].get().strip()
        admin_password = self.entries["admin_password"].get().strip()
        hours_open = self.hours_open.get()
        hours_close = self.hours_close.get()

        if not all([name, address, admin_email, admin_password]):
            messagebox.showwarning("Внимание", "Заполните название, адрес, email и пароль администратора")
            return
        if len(admin_password) < 8:
            messagebox.showerror("Ошибка", "Пароль администратора — не менее 8 символов")
            return
        if hours_open >= hours_close:
            messagebox.showerror("Ошибка", "Время закрытия должно быть позже времени открытия")
            return

        working_hours = f"{hours_open} - {hours_close}"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE email = ?", (admin_email,))
        if cursor.fetchone():
            conn.close()
            messagebox.showerror("Ошибка", "Администратор с таким email уже существует")
            return

        cursor.execute(
            "INSERT INTO restaurants (name, address, phone, working_hours) VALUES (?, ?, ?, ?)",
            (name, address, phone, working_hours),
        )
        rest_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO admins (restaurant_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (rest_id, f"Админ {name}", admin_email, _hash_password(admin_password)),
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Готово", f"Ресторан «{name}» зарегистрирован.\n"
                                       f"Администратор: {admin_email}")
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.hours_open.set("10:00")
        self.hours_close.set("23:00")
        self.refresh_restaurants()