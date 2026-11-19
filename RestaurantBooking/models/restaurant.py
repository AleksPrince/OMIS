from dataclasses import dataclass

@dataclass
class Restaurant:
    id: int
    name: str
    address: str
    phone: str
    working_hours: str
    admin_id: int

@dataclass
class Table:
    id: int
    restaurant_id: int
    number: int
    seats: int
    status: str  # "Свободен", "Забронирован", "Выбран"