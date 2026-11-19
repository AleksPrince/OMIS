import tkinter as tk
from tkinter import ttk, messagebox
from services.auth_service import AuthService
from models.client import RegistrationData


class AuthUI:
    def __init__(self, root, auth_service: AuthService, on_login_success):
        self.root = root
        self.auth_service = auth_service
        self.on_login_success = on_login_success
        self.root.title("Вход / Регистрация — Бронирование столиков")
        self.root.geometry("420x560")
        self.root.resizable(False, False)
        self.show_login_form()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_form(self):
        self.clear_window()

        header = tk.Frame(self.root)
        header.pack(pady=(20, 5))
        tk.Label(header, text="🍽", font=("Arial", 32)).pack()
        tk.Label(header, text="Бронирование столиков",
                 font=("Arial", 14, "bold")).pack()
        tk.Label(header, text="Войдите в личный кабинет",
                 font=("Arial", 10), fg="gray").pack(pady=(0, 15))

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="Роль").grid(row=0, column=0, sticky="w", pady=5)
        self.role_combo = ttk.Combobox(
            frame,
            values=["Клиент", "Администратор ресторана", "Системный администратор"],
            state="readonly",
            width=28,
        )
        self.role_combo.current(0)
        self.role_combo.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Email").grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Пароль").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        self.password_entry.bind("<Return>", lambda e: self.login())

        tk.Button(self.root, text="Войти", width=20,
                  command=self.login).pack(pady=15)

        tk.Label(self.root, text="Нет учетной записи?",
                 fg="gray").pack(pady=(10, 0))
        tk.Button(self.root, text="Зарегистрироваться", width=20,
                  command=self.show_register_form).pack(pady=5)

        # Подсказка с тестовыми учётками
        tk.Label(
            self.root,
            text="Тест: admin@rest.com / admin123 (админ ресторана)\n"
                 "sys@rest.com / sys123 (системный админ)",
            font=("Arial", 8), fg="gray", justify="center",
        ).pack(side=tk.BOTTOM, pady=10)

    def show_register_form(self):
        self.clear_window()
        tk.Label(self.root, text="Регистрация клиента",
                 font=("Arial", 14, "bold")).pack(pady=20)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        fields = [
            ("Имя", "name", False),
            ("Телефон", "phone", False),
            ("Email", "email", False),
            ("Пароль", "password", True),
            ("Повтор пароля", "password_confirm", True),
        ]

        self.reg_entries = {}
        for i, (label_text, key, is_password) in enumerate(fields):
            tk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if is_password else "")
            entry.grid(row=i, column=1, pady=5)
            self.reg_entries[key] = entry

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Зарегистрироваться",
                  command=self.register).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Назад",
                  command=self.show_login_form).pack(side=tk.LEFT, padx=5)

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role_label = self.role_combo.get()

        if not email or not password:
            messagebox.showwarning("Внимание", "Заполните все поля")
            return

        role_map = {
            "Клиент": "client",
            "Администратор ресторана": "admin",
            "Системный администратор": "system",
        }
        role = role_map[role_label]

        success, result = self.auth_service.login_by_role(email, password, role)
        if success:
            self.on_login_success(result, role)
        else:
            messagebox.showerror("Ошибка входа", result)

    def register(self):
        data = RegistrationData(
            name=self.reg_entries["name"].get().strip(),
            phone=self.reg_entries["phone"].get().strip(),
            email=self.reg_entries["email"].get().strip(),
            password=self.reg_entries["password"].get().strip(),
            password_confirm=self.reg_entries["password_confirm"].get().strip(),
        )
        success, message = self.auth_service.register(data)
        if success:
            messagebox.showinfo("Успех", message)
            self.show_login_form()
        else:
            messagebox.showerror("Ошибка регистрации", message)