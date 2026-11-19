import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from repositories.database import get_connection


class AdminUI:
    def __init__(self, root, admin: dict, on_logout):
        self.root = root
        self.admin = admin
        self.on_logout = on_logout
        self.restaurant_id = admin["restaurant_id"]

        self.root.title(f"Панель администратора — {admin['name']}")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self._build_header()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_bookings_tab()
        self._build_hall_tab()
        self._build_info_tab()

        self._schedule_refresh()

    def _build_header(self):
        header = tk.Frame(self.root, bg="#f0f0f0", height=50)
        header.pack(fill="x")
        tk.Label(header, text="Панель администратора ресторана",
                 font=("Arial", 13, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=15, pady=10)
        tk.Button(header, text="Выйти", command=self.on_logout).pack(side=tk.RIGHT, padx=15, pady=10)

    # =========================================================
    #  ВКЛАДКА 1: БРОНИРОВАНИЯ
    # =========================================================
    def _build_bookings_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Бронирования")

        filter_frame = tk.Frame(tab)
        filter_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(filter_frame, text="Дата:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_date = ttk.Entry(filter_frame, width=12)
        self.filter_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.filter_date.pack(side=tk.LEFT, padx=5)

        tk.Button(filter_frame, text="Показать за день",
                  command=self.refresh_bookings).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Показать все",
                  command=self.refresh_bookings_all).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(btn_frame, text="Подтвердить",
                  command=lambda: self.change_status("Подтверждена")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отменить",
                  command=lambda: self.change_status("Отменена")).pack(side=tk.LEFT, padx=5)

        columns = ("id", "client", "date", "time", "guests", "table", "status")
        self.tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)
        headers = ["№", "Клиент", "Дата", "Время", "Гостей", "Столик", "Статус"]
        widths = [40, 180, 100, 80, 70, 80, 130]
        for col, h, w in zip(columns, headers, widths):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

    def _schedule_refresh(self):
        try:
            self.refresh_bookings()
            self.load_hall()
            self.root.after(15000, self._schedule_refresh)
        except tk.TclError:
            pass

    def refresh_bookings(self):
        date_str = self.filter_date.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_str = date.today().strftime("%Y-%m-%d")
            self.filter_date.delete(0, tk.END)
            self.filter_date.insert(0, date_str)
        self._load_bookings(date_str)

    def refresh_bookings_all(self):
        self._load_bookings(None)

    def _load_bookings(self, date_str):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_connection()
        cursor = conn.cursor()
        if date_str:
            cursor.execute("""
                SELECT b.id, c.name AS client_name, b.date, b.time, b.guests,
                       t.number AS table_number, b.status
                FROM bookings b
                JOIN clients c ON c.id = b.client_id
                JOIN tables t ON t.id = b.table_id
                WHERE t.restaurant_id = ? AND b.date = ?
                ORDER BY b.time
            """, (self.restaurant_id, date_str))
        else:
            cursor.execute("""
                SELECT b.id, c.name AS client_name, b.date, b.time, b.guests,
                       t.number AS table_number, b.status
                FROM bookings b
                JOIN clients c ON c.id = b.client_id
                JOIN tables t ON t.id = b.table_id
                WHERE t.restaurant_id = ?
                ORDER BY b.date DESC, b.time DESC
            """, (self.restaurant_id,))

        for row in cursor.fetchall():
            # Безопасно обрезаем секунды для отображения (на случай старых записей)
            display_time = row["time"][:5] if row["time"] and len(row["time"]) > 5 else row["time"]
            self.tree.insert("", "end", values=(
                row["id"], row["client_name"], row["date"], display_time,
                row["guests"], row["table_number"], row["status"],
            ))
        conn.close()

    def _selected_booking_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите бронирование")
            return None
        return self.tree.item(sel[0])["values"][0]

    def change_status(self, new_status):
        bid = self._selected_booking_id()
        if not bid:
            return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, bid))
        conn.commit()
        conn.close()
        self.refresh_bookings()
        self.load_hall()
        messagebox.showinfo("Готово", f"Статус изменён на «{new_status}»")

    # =========================================================
    #  ВКЛАДКА 2: СХЕМА ЗАЛА
    # =========================================================
    def _build_hall_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Схема зала")

        top = tk.Frame(tab)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Дата:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.hall_date = ttk.Entry(top, width=12)
        self.hall_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.hall_date.pack(side=tk.LEFT, padx=5)

        tk.Label(top, text="Время:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(15, 5))
        time_slots = self._generate_time_slots()
        self.hall_time = ttk.Combobox(top, values=time_slots, state="readonly", width=8)
        self.hall_time.set("19:00")
        self.hall_time.pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="Показать зал", command=self.load_hall).pack(side=tk.LEFT, padx=15)
        tk.Button(top, text="Сбросить (все столики)",
                  command=self.load_hall_all).pack(side=tk.LEFT, padx=5)

        body = tk.Frame(tab)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(body)
        left.pack(side=tk.LEFT, fill="both", expand=True)

        self.hall_canvas = tk.Canvas(left, bg="white", highlightthickness=1,
                                     highlightbackground="gray")
        self.hall_canvas.pack(fill="both", expand=True)

        legend = tk.Frame(left)
        legend.pack(pady=5)
        tk.Label(legend, text="🟢 Свободен", bg="lightgreen", padx=8, pady=2).pack(side=tk.LEFT, padx=5)
        tk.Label(legend, text="🔴 Забронирован", bg="salmon", padx=8, pady=2).pack(side=tk.LEFT, padx=5)

        right = tk.Frame(body, width=200)
        right.pack(side=tk.RIGHT, fill="y", padx=5)
        right.pack_propagate(False)

        tk.Label(right, text="Номер столика", font=("Arial", 10, "bold")).pack(pady=(15, 0))
        self.hall_number = ttk.Entry(right, width=15)
        self.hall_number.pack(pady=3)

        tk.Label(right, text="Количество мест", font=("Arial", 10, "bold")).pack(pady=(15, 0))
        self.hall_seats = ttk.Entry(right, width=15)
        self.hall_seats.insert(0, "4")
        self.hall_seats.pack(pady=3)

        tk.Button(right, text="Добавить столик", width=15,
                  command=self.add_table).pack(pady=(20, 5))
        tk.Button(right, text="Удалить столик", width=15,
                  command=self.remove_table).pack(pady=5)

    @staticmethod
    def _generate_time_slots():
        slots = []
        current = datetime.strptime("10:00", "%H:%M")
        end = datetime.strptime("23:00", "%H:%M")
        while current <= end:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=20)
        return slots

    @staticmethod
    def _safe_parse_time(time_str: str) -> datetime.time:
        """Парсит время в формате ЧЧ:ММ или ЧЧ:ММ:СС."""
        if not time_str:
            return datetime.strptime("00:00", "%H:%M").time()
        # Берём только первые 5 символов (ЧЧ:ММ)
        if len(time_str) > 5:
            time_str = time_str[:5]
        return datetime.strptime(time_str, "%H:%M").time()

    def load_hall(self):
        date_str = self.hall_date.get().strip()
        time_str = self.hall_time.get().strip()

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты или времени")
            return

        self._draw_hall(date_str, time_str)

    def load_hall_all(self):
        self._draw_hall(None, None)

    def _draw_hall(self, date_str, time_str):
        self.hall_canvas.delete("all")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, number, seats FROM tables WHERE restaurant_id = ? ORDER BY number",
            (self.restaurant_id,),
        )
        tables = cursor.fetchall()

        booked_ids = set()
        if date_str and time_str:
            requested_start = datetime.strptime(time_str, "%H:%M").time()
            requested_end = (datetime.combine(date.today(), requested_start) + timedelta(minutes=40)).time()

            cursor.execute("""
                SELECT DISTINCT b.table_id, b.time FROM bookings b
                JOIN tables t ON t.id = b.table_id
                WHERE t.restaurant_id = ? AND b.date = ? AND b.status != 'Отменена'
            """, (self.restaurant_id, date_str))

            for row in cursor.fetchall():
                try:
                    existing_start = self._safe_parse_time(row["time"])
                except ValueError:
                    # Пропускаем битые записи
                    continue
                existing_end = (datetime.combine(date.today(), existing_start) + timedelta(minutes=40)).time()

                if requested_start < existing_end and existing_start < requested_end:
                    booked_ids.add(row["table_id"])
        else:
            cursor.execute("""
                SELECT DISTINCT t.id FROM bookings b
                JOIN tables t ON t.id = b.table_id
                WHERE t.restaurant_id = ? AND b.status != 'Отменена'
            """, (self.restaurant_id,))
            booked_ids = {row["id"] for row in cursor.fetchall()}

        conn.close()

        if date_str and time_str:
            header = f"Зал на {date_str} в {time_str}"
        else:
            header = "Общий статус столиков"
        self.hall_canvas.create_text(300, 20, text=header,
                                     font=("Arial", 12, "bold"))

        for i, row in enumerate(tables):
            x = 60 + (i % 4) * 100
            y = 60 + (i // 4) * 100
            is_booked = row["id"] in booked_ids
            color = "salmon" if is_booked else "lightgreen"

            self.hall_canvas.create_oval(x, y, x + 60, y + 60, fill=color, outline="black")
            self.hall_canvas.create_text(x + 30, y + 25, text=str(row["number"]),
                                         font=("Arial", 12, "bold"))
            self.hall_canvas.create_text(x + 30, y + 45, text=f"{row['seats']} мест",
                                         font=("Arial", 8))

    def add_table(self):
        try:
            number = int(self.hall_number.get())
            seats = int(self.hall_seats.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числа в поля «Номер» и «Мест»")
            return
        if seats < 1:
            messagebox.showerror("Ошибка", "Количество мест должно быть больше 0")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tables WHERE restaurant_id = ? AND number = ?",
                       (self.restaurant_id, number))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Ошибка", f"Столик №{number} уже существует")
            return
        cursor.execute("INSERT INTO tables (restaurant_id, number, seats) VALUES (?, ?, ?)",
                       (self.restaurant_id, number, seats))
        conn.commit()
        conn.close()
        self.hall_number.delete(0, tk.END)
        self.load_hall()
        messagebox.showinfo("Готово", f"Столик №{number} добавлен")

    def remove_table(self):
        number = self.hall_number.get().strip()
        if not number:
            messagebox.showwarning("Внимание", "Укажите номер столика в поле «Номер»")
            return
        try:
            number = int(number)
        except ValueError:
            messagebox.showerror("Ошибка", "Номер должен быть числом")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tables WHERE restaurant_id = ? AND number = ?",
                       (self.restaurant_id, number))
        row = cursor.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("Ошибка", f"Столик №{number} не найден")
            return

        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE table_id = ? AND status != 'Отменена'
        """, (row["id"],))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Ошибка",
                                 f"Нельзя удалить столик №{number}: есть активные бронирования")
            return

        cursor.execute("DELETE FROM tables WHERE id = ?", (row["id"],))
        conn.commit()
        conn.close()
        self.load_hall()
        messagebox.showinfo("Готово", f"Столик №{number} удалён")

    # =========================================================
    #  ВКЛАДКА 3: ИНФОРМАЦИЯ О РЕСТОРАНЕ
    # =========================================================
    def _build_info_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Информация о ресторане")

        frame = tk.Frame(tab)
        frame.pack(pady=20, padx=20)

        fields = [
            ("Название", "name"),
            ("Адрес", "address"),
            ("Телефон", "phone"),
            ("Часы работы", "hours"),
        ]

        self.info_entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(frame, text=label, width=15, anchor="w").grid(row=i, column=0, pady=8)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, pady=8)
            self.info_entries[key] = entry

        tk.Button(frame, text="Сохранить", width=20,
                  command=self.save_info).grid(row=len(fields), column=1, pady=20)

        self.load_info()

    def load_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (self.restaurant_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        self.info_entries["name"].delete(0, tk.END)
        self.info_entries["name"].insert(0, row["name"])

        self.info_entries["address"].delete(0, tk.END)
        self.info_entries["address"].insert(0, row["address"])

        self.info_entries["phone"].delete(0, tk.END)
        self.info_entries["phone"].insert(0, row["phone"] or "")

        self.info_entries["hours"].delete(0, tk.END)
        self.info_entries["hours"].insert(0, row["working_hours"] or "")

    def save_info(self):
        name = self.info_entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Название не может быть пустым")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE restaurants SET name = ?, address = ?, phone = ?, working_hours = ? WHERE id = ?",
            (
                name,
                self.info_entries["address"].get().strip(),
                self.info_entries["phone"].get().strip(),
                self.info_entries["hours"].get().strip(),
                self.restaurant_id,
            ),
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Готово", "Информация о ресторане обновлена")