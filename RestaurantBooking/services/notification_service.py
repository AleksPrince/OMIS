import threading
import time

class NotificationService:
    def send_confirmation(self, booking_id: int, email: str, phone: str):
        # Имитация отправки (в реальности здесь smtplib)
        print(f"[NotificationService] Отправка подтверждения для брони #{booking_id} на {email} и {phone}")
        # Можно добавить time.sleep для имитации задержки, но мы сделаем это в потоке
        time.sleep(1)
        print(f"[NotificationService] Подтверждение для брони #{booking_id} отправлено.")