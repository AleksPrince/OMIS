from dataclasses import dataclass
from datetime import datetime, date, time

@dataclass
class Booking:
    id: int
    client_id: int
    table_id: int
    date: date
    time: time
    guests: int
    status: str  # "Создана", "Подтверждена", "Отменена"

@dataclass
class SearchCriteria:
    restaurant_id: int
    date: date
    time: time
    guests: int