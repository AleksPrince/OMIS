import hashlib
import secrets
import hmac
import re
from repositories.client_repo import ClientRepository
from repositories.database import get_connection
from models.client import RegistrationData, Client


class AuthService:
    def __init__(self, client_repo: ClientRepository):
        self.client_repo = client_repo

    def _hash_password(self, password: str, salt: bytes = None) -> str:
        if salt is None:
            salt = secrets.token_bytes(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + ":" + pwd_hash.hex()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt_hex, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(pwd_hash.hex(), hash_hex)
        except ValueError:
            return False

    # ---- Клиент ----
    def register(self, data: RegistrationData) -> tuple[bool, str]:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data.email):
            return False, "Некорректный формат email"
        if data.password != data.password_confirm:
            return False, "Пароли не совпадают"
        if len(data.password) < 8:
            return False, "Пароль должен быть не менее 8 символов"
        if self.client_repo.find_by_email(data.email):
            return False, "Email уже занят"

        pwd_hash = self._hash_password(data.password)
        self.client_repo.save(data.name, data.phone, data.email, pwd_hash)
        return True, "Регистрация успешна"

    def login(self, email: str, password: str) -> tuple[bool, str | Client]:
        client = self.client_repo.find_by_email(email)
        if not client:
            return False, "Пользователь не найден"
        if self._verify_password(password, client.password_hash):
            return True, client
        return False, "Неверный пароль"

    # ---- Администратор ресторана ----
    def login_admin(self, email: str, password: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False, "Администратор не найден"
        if not self._verify_password(password, row["password_hash"]):
            return False, "Неверный пароль"
        return True, {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "restaurant_id": row["restaurant_id"],
            "role": "admin",
        }

    # ---- Системный администратор ----
    def login_system_admin(self, email: str, password: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_admins WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False, "Системный администратор не найден"
        if not self._verify_password(password, row["password_hash"]):
            return False, "Неверный пароль"
        return True, {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": "system",
        }

    # ---- Универсальный вход с выбором роли ----
    def login_by_role(self, email: str, password: str, role: str):
        if role == "client":
            return self.login(email, password)
        if role == "admin":
            return self.login_admin(email, password)
        if role == "system":
            return self.login_system_admin(email, password)
        return False, "Неизвестная роль"