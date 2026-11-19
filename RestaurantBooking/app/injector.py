from repositories.client_repo import ClientRepository
from services.auth_service import AuthService
from services.notification_service import NotificationService
from services.booking_service import BookingService


class AppInjector:
    def __init__(self):
        # Инициализация репозиториев
        self.client_repo = ClientRepository()

        # Инициализация сервисов
        self.notification_service = NotificationService()
        self.auth_service = AuthService(self.client_repo)
        self.booking_service = BookingService(self.notification_service)

    def get_auth_service(self) -> AuthService:
        return self.auth_service

    def get_booking_service(self) -> BookingService:
        return self.booking_service