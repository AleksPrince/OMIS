from repositories.database import get_connection
from models.booking import Booking, SearchCriteria
from models.restaurant import Table
from services.notification_service import NotificationService
import threading
from datetime import datetime, timedelta


class BookingService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    @staticmethod
    def _safe_parse_time(time_str: str) -> datetime.time:
        """Парсит время в формате ЧЧ:ММ или ЧЧ:ММ:СС."""
        if not time_str:
            return datetime.strptime("00:00", "%H:%M").time()
        if len(time_str) > 5:
            time_str = time_str[:5]
        return datetime.strptime(time_str, "%H:%M").time()

    def find_tables(self, criteria: SearchCriteria) -> list[Table]:
        conn = get_connection()
        cursor = conn.cursor()

        requested_start = criteria.time
        requested_end = (datetime.combine(datetime.today(), requested_start) + timedelta(minutes=40)).time()

        cursor.execute("""
            SELECT t.* FROM tables t
            WHERE t.restaurant_id = ? AND t.seats >= ?
        """, (criteria.restaurant_id, criteria.guests))
        all_tables = cursor.fetchall()

        available_tables = []
        for table in all_tables:
            cursor.execute("""
                SELECT time FROM bookings
                WHERE table_id = ? AND date = ? AND status != 'Отменена'
            """, (table["id"], str(criteria.date)))

            is_free = True
            for row in cursor.fetchall():
                try:
                    existing_start = self._safe_parse_time(row["time"])
                except ValueError:
                    continue
                existing_end = (datetime.combine(datetime.today(), existing_start) + timedelta(minutes=40)).time()

                if requested_start < existing_end and existing_start < requested_end:
                    is_free = False
                    break

            if is_free:
                available_tables.append(table)

        conn.close()

        return [
            Table(
                id=r["id"],
                restaurant_id=r["restaurant_id"],
                number=r["number"],
                seats=r["seats"],
                status=r["status"]
            ) for r in available_tables
        ]

    def book_table(self, client_id: int, table_id: int, criteria: SearchCriteria, email: str, phone: str) -> Booking:
        conn = get_connection()
        cursor = conn.cursor()

        time_str = criteria.time.strftime("%H:%M")

        cursor.execute("""
            INSERT INTO bookings (client_id, table_id, date, time, guests, status)
            VALUES (?, ?, ?, ?, ?, 'Создана')
        """, (client_id, table_id, str(criteria.date), time_str, criteria.guests))
        booking_id = cursor.lastrowid

        cursor.execute("UPDATE tables SET status = 'Забронирован' WHERE id = ?", (table_id,))
        conn.commit()
        conn.close()

        thread = threading.Thread(target=self.notification_service.send_confirmation, args=(booking_id, email, phone))
        thread.start()

        return Booking(booking_id, client_id, table_id, criteria.date, criteria.time, criteria.guests, "Создана")