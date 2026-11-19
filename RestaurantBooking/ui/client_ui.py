import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from tkcalendar import DateEntry
from models.booking import SearchCriteria
from models.restaurant import Table
from repositories.database import get_connection


class ClientUI:
    def __init__(self, root, client, booking_service, on_logout=None):
        self.root = root
        self.client = client
        self.booking_service = booking_service
        self.on_logout = on_logout
        self.root.title("Бронирование столика")
        self.root.geometry("500x650")
        self.root.resizable(False, False)

        self.current_criteria = None
        self.selected_table = None
        self.current_restaurant_name = ""
        self._restaurants = []

        self.show_search_form()

    # ---------- Утилиты ----------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.update_idletasks()

    def _build_header(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(5, 0))
        tk.Label(top, text=f"👤 {self.client.name}", fg="gray").pack(side=tk.LEFT)
        if self.on_logout:
            tk.Button(top, text="Выйти", command=self.on_logout).pack(side=tk.RIGHT)

    @staticmethod
    def _generate_default_time_slots():
        """Базовые слоты (на случай, если у ресторана нет настроек)."""
        slots = []
        current = datetime.strptime("10:00", "%H:%M")
        end = datetime.strptime("23:00", "%H:%M")
        while current <= end:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=20)
        return slots

    def _get_time_slots_for_restaurant(self, restaurant_id):
        """Генерирует слоты с шагом 20 минут в зависимости от часов работы ресторана."""
        if not restaurant_id:
            return self._generate_default_time_slots()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT working_hours FROM restaurants WHERE id = ?", (restaurant_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row["working_hours"]:
            return self._generate_default_time_slots()

        wh = row["working_hours"]
        try:
            # Ожидаем формат "10:00 - 23:00"
            parts = wh.split("-")
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            start_dt = datetime.strptime(start_str, "%H:%M")
            end_dt = datetime.strptime(end_str, "%H:%M")
        except (ValueError, IndexError):
            return self._generate_default_time_slots()

        slots = []
        current = start_dt
        # Генерируем, пока не дойдем до времени закрытия
        while current <= end_dt:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=20)
        return slots

    def _get_all_restaurants(self):
        """Возвращает список (id, name) всех ресторанов."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM restaurants ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [(row["id"], row["name"]) for row in rows]

    def _get_selected_restaurant(self):
        """Возвращает (id, name) выбранного ресторана."""
        idx = self.rest_combo.current()
        if idx < 0 or idx >= len(self._restaurants):
            return None, None
        return self._restaurants[idx]

    # ---------- Экран поиска ----------
    def show_search_form(self):
        self.clear_window()
        self._build_header()

        tk.Label(self.root, text="Забронируйте столик в ресторане или кафе",
                 font=("Arial", 12, "bold")).pack(pady=20)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self._restaurants = self._get_all_restaurants()
        if not self._restaurants:
            messagebox.showerror("Ошибка", "В системе нет ни одного ресторана")
            return

        restaurant_names = [name for _, name in self._restaurants]

        # Ресторан
        tk.Label(frame, text="Ресторан").grid(row=0, column=0, sticky="w", pady=5)
        self.rest_combo = ttk.Combobox(frame, values=restaurant_names,
                                       state="readonly", width=25)
        self.rest_combo.current(0)
        self.rest_combo.grid(row=0, column=1, pady=5)

        # Привязываем событие смены ресторана, чтобы обновить список времени
        self.rest_combo.bind("<<ComboboxSelected>>", self._on_restaurant_change)

        # Дата
        tk.Label(frame, text="Дата").grid(row=1, column=0, sticky="w", pady=5)
        today = date.today()
        min_date = today
        max_date = today + timedelta(days=182)
        self.date_entry = DateEntry(
            frame, width=23, date_pattern="yyyy-mm-dd",
            mindate=min_date, maxdate=max_date,
            background="darkblue", foreground="white", borderwidth=2,
        )
        self.date_entry.set_date(today)
        self.date_entry.grid(row=1, column=1, pady=5)

        # Время
        tk.Label(frame, text="Время").grid(row=2, column=0, sticky="w", pady=5)
        # Инициализируем слоты для первого ресторана в списке
        initial_rest_id, _ = self._get_selected_restaurant()
        time_slots = self._get_time_slots_for_restaurant(initial_rest_id)

        self.time_combo = ttk.Combobox(frame, values=time_slots,
                                       state="readonly", width=25)
        # Устанавливаем 19:00, если оно есть в списке, иначе первый слот
        default_time = "19:00" if "19:00" in time_slots else (time_slots[0] if time_slots else "")
        self.time_combo.set(default_time)
        self.time_combo.grid(row=2, column=1, pady=5)

        # Гости
        tk.Label(frame, text="Гостей").grid(row=3, column=0, sticky="w", pady=5)
        self.guests_entry = ttk.Entry(frame, width=28)
        self.guests_entry.insert(0, "2")
        self.guests_entry.grid(row=3, column=1, pady=5)

        tk.Button(self.root, text="Найти столик",
                  command=self.search_tables, width=20).pack(pady=20)

    def _on_restaurant_change(self, event=None):
        """Обновляет список доступного времени при смене ресторана."""
        rest_id, _ = self._get_selected_restaurant()
        new_slots = self._get_time_slots_for_restaurant(rest_id)

        self.time_combo['values'] = new_slots
        # Пытаемся сохранить текущий выбор, если он есть в новом списке
        current_val = self.time_combo.get()
        if current_val in new_slots:
            self.time_combo.set(current_val)
        elif "19:00" in new_slots:
            self.time_combo.set("19:00")
        elif new_slots:
            self.time_combo.set(new_slots[0])
        else:
            self.time_combo.set("")

    # ---------- Поиск ----------
    def search_tables(self):
        try:
            date_obj = self.date_entry.get_date()
            time_str = self.time_combo.get()
            if not time_str:
                raise ValueError("Время не выбрано")
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            guests = int(self.guests_entry.get())
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Проверьте введенные данные: {e}")
            return

        restaurant_id, restaurant_name = self._get_selected_restaurant()
        if not restaurant_id:
            messagebox.showerror("Ошибка", "Выберите ресторан")
            return

        today = date.today()
        if not (today <= date_obj <= today + timedelta(days=182)):
            messagebox.showerror("Ошибка", "Дата вне допустимого диапазона")
            return
        if guests < 1:
            messagebox.showerror("Ошибка", "Количество гостей должно быть больше 0")
            return

        self.current_restaurant_name = restaurant_name
        self.current_criteria = SearchCriteria(
            restaurant_id=restaurant_id,
            date=date_obj,
            time=time_obj,
            guests=guests,
        )
        tables = self.booking_service.find_tables(self.current_criteria)

        if not tables:
            self.show_no_tables()
        else:
            self.show_hall_scheme(tables)

    # ---------- Нет столиков ----------
    def show_no_tables(self):
        self.clear_window()
        self._build_header()

        tk.Label(self.root, text="Нет свободных столиков",
                 font=("Arial", 16, "bold"), fg="red").pack(pady=50)
        tk.Label(self.root,
                 text="На выбранную дату и время свободных столиков нет.\n"
                      "Измените дату, время или число гостей.").pack(pady=10)
        tk.Button(self.root, text="Изменить параметры",
                  command=self.show_search_form).pack(pady=20)

    # ---------- Схема зала ----------
    def show_hall_scheme(self, tables: list[Table]):
        self.clear_window()
        self._build_header()

        tk.Label(self.root, text="Схема зала",
                 font=("Arial", 14, "bold")).pack(pady=10)

        info_text = (f"{self.current_restaurant_name} · {self.current_criteria.date} · "
                     f"{self.current_criteria.time.strftime('%H:%M')} · "
                     f"{self.current_criteria.guests} гостя")
        tk.Label(self.root, text=info_text, font=("Arial", 10)).pack(pady=5)

        canvas_frame = tk.Frame(self.root, bg="white", relief="sunken", borderwidth=2)
        canvas_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.table_buttons = []
        for i, table in enumerate(tables):
            btn = tk.Button(canvas_frame, text=str(table.number), width=4, height=2,
                            bg="white", relief="raised",
                            command=lambda t=table: self.select_table(t))
            btn.grid(row=i // 4, column=i % 4, padx=10, pady=10)
            self.table_buttons.append((btn, table))

        legend_frame = tk.Frame(self.root)
        legend_frame.pack(pady=5)
        tk.Label(legend_frame, text="⚪ Свободен", bg="white",
                 relief="solid", padx=5).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="⚫ Выбран", bg="gray", fg="white",
                 relief="solid", padx=5).pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Назад",
                  command=self.show_search_form).pack(side=tk.LEFT, padx=10)
        self.book_btn = tk.Button(btn_frame, text="Забронировать",
                                  state=tk.DISABLED, command=self.book_selected)
        self.book_btn.pack(side=tk.LEFT, padx=10)

    def select_table(self, table: Table):
        self.selected_table = table
        for btn, t in self.table_buttons:
            if t.id == table.id:
                btn.config(bg="gray", fg="white")
            else:
                btn.config(bg="white", fg="black")
        self.book_btn.config(state=tk.NORMAL)

    def book_selected(self):
        if not self.selected_table:
            return
        booking = self.booking_service.book_table(
            client_id=self.client.id,
            table_id=self.selected_table.id,
            criteria=self.current_criteria,
            email=self.client.email,
            phone=self.client.phone,
        )
        self.show_success(booking)

    # ---------- Успех ----------
    def show_success(self, booking):
        self.clear_window()
        self._build_header()

        tk.Label(self.root, text="✓", font=("Arial", 40),
                 fg="green").pack(pady=20)
        tk.Label(self.root, text="Бронирование подтверждено",
                 font=("Arial", 14, "bold")).pack(pady=10)

        info_text = (f"Столик №{self.selected_table.number} забронирован\n"
                     f"{self.current_restaurant_name}\n"
                     f"{self.current_criteria.date} · "
                     f"{self.current_criteria.time.strftime('%H:%M')} · "
                     f"{self.current_criteria.guests} гостя")
        tk.Label(self.root, text=info_text, justify="center").pack(pady=10)

        tk.Label(self.root, text="Подтверждение отправлено по SMS и Email",
                 font=("Arial", 9), fg="gray").pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Новый поиск",
                  command=self.show_search_form).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Закрыть",
                  command=self.root.destroy).pack(side=tk.LEFT, padx=10)