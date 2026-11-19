from dataclasses import dataclass
from datetime import datetime

@dataclass
class Notification:
    id: int
    client_id: int
    type: str  # "SMS" или "Email"
    message: str
    sent_date: datetime