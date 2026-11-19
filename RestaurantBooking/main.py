import tkinter as tk
from app.injector import AppInjector
from repositories.database import init_db
from ui.auth_ui import AuthUI
from ui.client_ui import ClientUI
from ui.admin_ui import AdminUI
from ui.sysadmin_ui import SysAdminUI


class Main:
    def __init__(self):
        self.root = tk.Tk()
        self._apply_theme()
        self.injector = AppInjector()
        self.current_window = None

    def _apply_theme(self):
        # Единый стиль
        style = tk.ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TEntry", padding=4)
        style.configure("TNotebook.Tab", padding=(12, 6))
        self.root.option_add("*Font", "Arial 10")

    def run(self):
        init_db()
        self.show_auth()
        self.root.mainloop()

    def show_auth(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.current_window = AuthUI(
            self.root,
            self.injector.get_auth_service(),
            self.on_login_success,
        )

    def on_login_success(self, user, role):
        for w in self.root.winfo_children():
            w.destroy()

        if role == "client":
            self.current_window = ClientUI(
                self.root, user, self.injector.get_booking_service(), self.show_auth
            )
        elif role == "admin":
            self.current_window = AdminUI(self.root, user, self.show_auth)
        elif role == "system":
            self.current_window = SysAdminUI(self.root, user, self.show_auth)


if __name__ == "__main__":
    main_app = Main()
    main_app.run()