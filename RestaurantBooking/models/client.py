from dataclasses import dataclass
from datetime import datetime

@dataclass
class Client:
    id: int
    name: str
    phone: str
    email: str
    password_hash: str
    registration_date: datetime

@dataclass
class RegistrationData:
    name: str
    phone: str
    email: str
    password: str
    password_confirm: str