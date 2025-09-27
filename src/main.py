import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from tkinter import *
import datetime
import os
from PIL import Image, ImageTk


class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Monitor")
        self.root.geometry("600x400")

        # Настройка стиля для ВСЕХ ttk виджетов
        self.setup_global_style()

        self.create_main_window()
        self.conn = None

    def setup_global_style(self):
        style = ttk.Style()
        style.configure("TButton",
                        font=("helvetica", 13),
                        foreground="#004D40",
                        padding=8,
                        background="#B2DFDB")

        style.configure("Treeview",
                        font=("helvetica", 11),
                        rowheight=25)
        style.configure("Treeview.Heading",
                        font=("helvetica", 12, "bold"),
                        background="#E0F2F1")

        style.configure("TFrame", background="#E0F2F1")

        style.configure("TEntry",
                        font=("helvetica", 11),
                        foreground="#004D40")

    def connect_db(self):
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="12345678",
                port="5432"
            )

            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_ddos_detection'")
                if not cur.fetchone():
                    messagebox.showwarning("Внимание",
                                           "База данных 'ai_ddos_detection' не существует.\n"
                                           "Создайте её командой: CREATE DATABASE ai_ddos_detection;")
                    return None

            conn.close()
            self.conn = psycopg2.connect(
                host="localhost",
                database="ai_ddos_detection",
                user="postgres",
                password="12345678",
                port="5432"
            )
            messagebox.showinfo("", "База данных успешно подключена")
            return self.conn

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if "password authentication failed" in error_msg:
                messagebox.showerror("Ошибка",
                                     "Неверный пароль PostgreSQL.\n""Проверьте пароль или сбросьте его через pgAdmin.")
            elif "connection refused" in error_msg.lower():
                messagebox.showerror("Ошибка",
                                     "PostgreSQL не запущен!\n""Запустите службу PostgreSQL через services.msc")
            else:
                messagebox.showerror("Ошибка", f"Ошибка подключения: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")
            return None

    def check_cell_value(self, row_index, column_name):
        items = self.tree.get_children()
        if row_index < len(items):
            item = items[row_index]
            values = self.tree.item(item, 'values')
            # Определяем индекс колонки
            columns = ['ID', 'Name', 'Description', 'Version', 'Framework',
                       'IsProduction', 'Production', 'CreatedAt', 'UpdatedAt', 'AttackType', 'ActualVersions']
            col_index = columns.index(column_name)
            cell_value = values[col_index]
            return cell_value

    def create_combobox_for_filters(self, parent_frame):
        types = ["Без сортировки", "ID", "Attack Type", "CreatedAt", "UpdatedAt"]
        combobox = ttk.Combobox(parent_frame, values=types, state="readonly")
        combobox.set("Без сортировки")  # Устанавливаем значение по умолчанию
        combobox.pack(anchor="nw", padx=6, pady=6)

        def on_filter_change(event):
            selected = combobox.get()
            if selected == "CreatedAt":
                self.sort_by_creation()
            elif selected == "UpdatedAt":
                self.sort_by_updated()
            elif selected == "ID":
                self.sort_by_id()
            elif selected == "Attack Type":
                self.sort_by_attack_type()
            elif selected == "Без сортировки":
                self.load_data_for_editing()  # Возвращаем исходный порядок

        combobox.bind('<<ComboboxSelected>>', on_filter_change)
        return combobox

    def sort_by_id(self):
        if hasattr(self, 'edit_tree') and self.edit_tree:
            items = [(self.edit_tree.set(item, 'ID'), item) for item in self.edit_tree.get_children('')]
            # Сортируем по числовому значению ID
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
            for index, (val, item) in enumerate(items):
                self.edit_tree.move(item, '', index)

    def sort_by_creation(self):
        if hasattr(self, 'edit_tree') and self.edit_tree:
            items = []
            for item in self.edit_tree.get_children(''):
                date_str = self.edit_tree.set(item, 'CreatedAt')
                try:
                    # Пытаемся преобразовать дату
                    if date_str:
                        date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_val = datetime.datetime.min
                except ValueError:
                    date_val = datetime.datetime.min

                items.append((date_val, item))

            # Сортировка по убыванию (сначала новые)
            items.sort(key=lambda x: x[0], reverse=True)

            for index, (date_val, item) in enumerate(items):
                self.edit_tree.move(item, '', index)

    def sort_by_updated(self):
        if hasattr(self, 'edit_tree') and self.edit_tree:
            items = []
            for item in self.edit_tree.get_children(''):
                date_str = self.edit_tree.set(item, 'UpdatedAt')
                try:
                    if date_str:
                        date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_val = datetime.datetime.min
                except ValueError:
                    date_val = datetime.datetime.min

                items.append((date_val, item))

            # Сортировка по убыванию (сначала новые)
            items.sort(key=lambda x: x[0], reverse=True)

            for index, (date_val, item) in enumerate(items):
                self.edit_tree.move(item, '', index)

    def sort_by_attack_type(self):
        if hasattr(self, 'edit_tree') and self.edit_tree:
            items = [(self.edit_tree.set(item, 'AttackType'), item) for item in self.edit_tree.get_children('')]
            items.sort(key=lambda x: x[0] if x[0] else '')
            for index, (attack_type, item) in enumerate(items):
                self.edit_tree.move(item, '', index)

    def try_fetch_from_schemas(self, cur, schemas, table_name='ai_models'):
        for schema in schemas:
            try:
                cur.execute(f"""
                    SELECT model_id, name, description, version, framework, 
                           is_production, production, created_at, updated_at, attack_type, actual_versions 
                    FROM {schema}.{table_name}
                    ORDER BY model_id
                """)
                return cur.fetchall()
            except psycopg2.Error:
                continue
        return None

    def get_current_schema(self):
        if not self.conn:
            return None

        try:
            with self.conn.cursor() as cur:
                # Проверяем существование таблицы в разных схемах
                for schema in ['ai_models', 'public']:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = 'ai_models'
                        )
                    """, (schema,))
                    if cur.fetchone()[0]:
                        return schema
                return None
        except Exception:
            return None

    def create_main_window(self):
        image_path = os.path.join(os.path.dirname(__file__), "..", "images", "main_window_background.png")

        try:
            self.pil_image = Image.open(image_path)
            self.original_image = self.pil_image.copy()

            canvas = Canvas(self.root, bg="white", width=600, height=400)
            canvas.pack(fill="both", expand=True)
            self.canvas_image = None

            def resize_image(event=None):
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()

                if canvas_width <= 1 or canvas_height <= 1:
                    return
                resized_image = self.original_image.resize(
                    (canvas_width, canvas_height),
                    Image.Resampling.LANCZOS
                )
                self.canvas_image = ImageTk.PhotoImage(resized_image)
                if hasattr(canvas, 'bg_item'):
                    canvas.itemconfig(canvas.bg_item, image=self.canvas_image)
                else:
                    canvas.bg_item = canvas.create_image(
                        0, 0,
                        anchor="nw",
                        image=self.canvas_image
                    )

            canvas.bind("<Configure>", resize_image)
            canvas.after(100, lambda: resize_image())

        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            # Создаем простой canvas без изображения
            canvas = Canvas(self.root, bg="#E0F2F1", width=600, height=400)
            canvas.pack(fill="both", expand=True)

        ttk.Button(canvas, text="Создать схему и таблицы", command=self.create_table_and_schema).place(relx=0.5,
                                                                                                       rely=0.3,
                                                                                                       anchor="center")
        ttk.Button(canvas, text="Внести данные", command=self.edit_data).place(relx=0.5, rely=0.5, anchor="center")
        ttk.Button(canvas, text="Показать данные", command=self.open_table).place(relx=0.5, rely=0.7, anchor="center")

    def create_schema(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("CREATE SCHEMA IF NOT EXISTS ai_models")
            self.conn.commit()
            messagebox.showinfo("Успех", "Схема успешно создана")
            return True
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании схемы: {e}")
            return False

    def edit_data(self, parent_window=None):
        if parent_window is None:
            parent_window = self.root

        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return

        edit_window = Toplevel(parent_window)
        edit_window.title("Редактирование данных")
        edit_window.geometry("1400x600")  # Увеличили ширину для нового столбца

        if parent_window != self.root:
            edit_window.transient(parent_window)
            edit_window.grab_set()

        # Используем ttk.Frame для применения стиля
        frame = ttk.Frame(edit_window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_scroll_y = ttk.Scrollbar(frame, orient='vertical')
        tree_scroll_y.pack(side='right', fill='y')

        tree_scroll_x = ttk.Scrollbar(frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')

        filter_frame = ttk.Frame(edit_window)
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text="Сортировка:").pack(side='left', padx=5)
        self.filter_combobox = self.create_combobox_for_filters(filter_frame)

        # Обновленные колонки с добавлением ActualVersions
        self.edit_tree = ttk.Treeview(frame,
                                      columns=('ID', 'Name', 'Description', 'Version', 'Framework', 'IsProduction',
                                               'Production', 'CreatedAt', 'UpdatedAt', 'AttackType', 'ActualVersions'),
                                      show='headings',
                                      yscrollcommand=tree_scroll_y.set,
                                      xscrollcommand=tree_scroll_x.set)

        tree_scroll_y.config(command=self.edit_tree.yview)
        tree_scroll_x.config(command=self.edit_tree.xview)

        # Обновленные колонки с ширинами
        columns = [
            ('ID', 80), ('Name', 120), ('Description', 200), ('Version', 100), ('Framework', 120),
            ('IsProduction', 100), ('Production', 120), ('CreatedAt', 120), ('UpdatedAt', 120),
            ('AttackType', 120), ('ActualVersions', 200)  # Новый столбец
        ]

        for col, width in columns:
            self.edit_tree.heading(col, text=col, anchor='w')
            self.edit_tree.column(col, width=width, anchor='w')

        self.edit_tree.pack(fill='both', expand=True)
        self.edit_tree.tag_configure('evenrow', background='#f0f0f0')

        self.load_data_for_editing()
        self.edit_tree.bind('<Double-1>', self.on_double_click)
        self.edit_tree.bind('<Motion>', self.on_hover)

        button_frame = ttk.Frame(edit_window)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="Добавить строку", command=self.add_new_row).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Удалить строку", command=self.delete_row).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Сохранить изменения", command=self.save_changes).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Обновить данные", command=self.load_data_for_editing).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Закрыть", command=edit_window.destroy).pack(side='right', padx=5)

    def on_hover(self, event):
        item = self.edit_tree.identify('item', event.x, event.y)
        if item:
            self.edit_tree.config(cursor="hand2")
        else:
            self.edit_tree.config(cursor="")

    def load_data_for_editing(self):
        self._load_data_into_treeview(self.edit_tree)

    def load_table_data(self):
        self._load_data_into_treeview(self.tree)

    def _load_data_into_treeview(self, treeview):
        try:
            if not self.conn:
                messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
                return

            # Очищаем существующие данные
            for item in treeview.get_children():
                treeview.delete(item)

            # Загружаем данные из базы
            with self.conn.cursor() as cur:
                rows = self.try_fetch_from_schemas(cur, ['ai_models', 'public'])

                if rows is not None:
                    for i, row in enumerate(rows):
                        formatted_row = []
                        for cell in row:
                            if isinstance(cell, list):  # Если это массив
                                formatted_row.append("{" + ",".join(map(str, cell)) + "}")
                            else:
                                formatted_row.append(str(cell) if cell is not None else '')

                        tag = 'evenrow' if i % 2 == 0 else ('oddrow' if treeview == self.edit_tree else '')
                        treeview.insert('', 'end', values=formatted_row, tags=(tag,))
                else:
                    messagebox.showinfo("Информация", "Таблица пуста или не существует. Добавьте новые строки.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")

    def get_enum_values(self):
        if not self.conn:
            return ['DDoS', 'Malware', 'IoT']

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT enumlabel 
                    FROM pg_enum 
                    JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                    WHERE pg_type.typname = 'attacks'
                    ORDER BY enumsortorder
                """)
                result = cur.fetchall()
                return [row[0] for row in result] if result else ['DDoS', 'Malware', 'IoT']
        except Exception as e:
            print(f"Ошибка при получении enum значений: {e}")
            return ['DDoS', 'Malware', 'IoT']

    def on_double_click(self, event):
        item = self.edit_tree.identify('item', event.x, event.y)
        if not item:
            return

        column = self.edit_tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1
        column_name = self.edit_tree.heading(column_index)['text']

        current_values = list(self.edit_tree.item(item, 'values'))
        current_value = current_values[column_index]

        bbox = self.edit_tree.bbox(item, column)
        if not bbox:
            return

        if column_name == 'AttackType':
            self.create_combobox_for_enum(item, column_index, bbox, current_value)
        elif column_name == 'ActualVersions':  # Особая обработка для массива
            self.create_array_entry(item, column_index, bbox, current_value)
        else:
            self.create_entry_for_cell(item, column_index, bbox, current_value)

    def create_combobox_for_enum(self, item, column_index, bbox, current_value):
        enum_values = self.get_enum_values()

        combo = ttk.Combobox(self.edit_tree, values=enum_values, state="readonly")
        combo.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        if current_value and current_value in enum_values:
            combo.set(current_value)
        elif enum_values:
            combo.set(enum_values[0])

        combo.focus_set()

        def save_edit(event=None):
            new_value = combo.get()
            current_values = list(self.edit_tree.item(item, 'values'))
            current_values[column_index] = new_value
            self.edit_tree.item(item, values=current_values)
            combo.destroy()

        def cancel_edit(event=None):
            combo.destroy()

        combo.bind('<<ComboboxSelected>>', save_edit)
        combo.bind('<Return>', save_edit)
        combo.bind('<Escape>', cancel_edit)
        combo.bind('<FocusOut>', save_edit)

    def create_array_entry(self, item, column_index, bbox, current_value):
        # Создаем окно для редактирования массива
        array_window = Toplevel(self.edit_tree)
        array_window.title("Редактирование Actual Versions")
        array_window.geometry("400x300")
        array_window.transient(self.edit_tree)
        array_window.grab_set()

        ttk.Label(array_window, text="Введите версии (через запятую):").pack(pady=10)

        text_widget = tk.Text(array_window, height=10, width=50)
        text_widget.pack(padx=10, pady=5, fill='both', expand=True)

        # Преобразуем массив в строку для редактирования
        if current_value and current_value != 'None' and current_value != '{}':
            try:
                # Убираем фигурные скобки если это строковое представление массива
                clean_value = current_value.strip('{}')
                text_widget.insert('1.0', clean_value)
            except:
                text_widget.insert('1.0', str(current_value))
        else:
            # Значения по умолчанию
            default_versions = "1.0, 1.1, 1.2, 2.0"
            text_widget.insert('1.0', default_versions)

        def save_array():
            array_text = text_widget.get('1.0', 'end-1c').strip()
            # Преобразуем текст в массив версий
            if array_text:
                try:
                    # Разделяем по запятой и очищаем элементы
                    elements = [elem.strip() for elem in array_text.split(',')]
                    # Убираем пустые элементы
                    versions = [elem for elem in elements if elem]

                    # Сохраняем как строку в формате массива PostgreSQL
                    array_str = "{" + ",".join(versions) + "}"
                    current_values = list(self.edit_tree.item(item, 'values'))
                    current_values[column_index] = array_str
                    self.edit_tree.item(item, values=current_values)

                except ValueError as e:
                    messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
                    return
            else:
                current_values = list(self.edit_tree.item(item, 'values'))
                current_values[column_index] = "{}"  # Пустой массив
                self.edit_tree.item(item, values=current_values)

            array_window.destroy()

        def cancel_edit():
            array_window.destroy()

        button_frame = ttk.Frame(array_window)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="Сохранить", command=save_array).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Отмена", command=cancel_edit).pack(side='right', padx=5)

        # Фокус на текстовом поле
        text_widget.focus_set()

    def create_entry_for_cell(self, item, column_index, bbox, current_value):
        entry = ttk.Entry(self.edit_tree, width=20)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, current_value)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def save_edit(event=None):
            new_value = entry.get()
            current_values = list(self.edit_tree.item(item, 'values'))
            current_values[column_index] = new_value
            self.edit_tree.item(item, values=current_values)
            entry.destroy()

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)

    def add_new_row(self):
        new_values = ['NEW'] + [''] * 10  # Теперь 11 столбцов
        new_values[1] = 'Новая модель'
        new_values[2] = 'Описание модели'
        new_values[3] = '1.0'
        new_values[4] = 'TensorFlow'
        new_values[5] = 'False'
        new_values[6] = 'production'
        new_values[7] = datetime.datetime.now().strftime('%Y-%m-%d')
        new_values[8] = datetime.datetime.now().strftime('%Y-%m-%d')
        new_values[10] = '{1.0,1.1,1.2,2.0}'  # Версии по умолчанию

        enum_values = self.get_enum_values()
        if enum_values:
            new_values[9] = enum_values[0]

        item_count = len(self.edit_tree.get_children())
        tag = 'evenrow' if item_count % 2 == 0 else 'oddrow'
        self.edit_tree.insert('', 'end', values=new_values, tags=(tag,))
        self.edit_tree.see(self.edit_tree.get_children()[-1])

    def delete_row(self):
        selected = self.edit_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите строку для удаления")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранную строку?"):
            for item in selected:
                self.edit_tree.delete(item)

    def save_changes(self):
        try:
            if not self.conn:
                messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
                return

            current_schema = self.get_current_schema()
            if not current_schema:
                messagebox.showerror("Ошибка", "Не найдена таблица ai_models ни в одной схеме")
                return

            cursor = self.conn.cursor()
            all_items = self.edit_tree.get_children()
            if not all_items:
                messagebox.showinfo("Информация", "Нет данных для сохранения")
                return

            success_count = 0
            error_count = 0
            errors = []

            for item in all_items:
                values = self.edit_tree.item(item, 'values')
                if len(values) < 11:  # Теперь 11 столбцов
                    continue

                model_id, name, description, version, framework, is_production, production, created_at, updated_at, attack_type, actual_versions = values
                try:
                    # ВАЛИДАЦИЯ ДАННЫХ
                    if not name or not description or not version or not framework:
                        raise ValueError("Поля Name, Description, Version, Framework обязательны для заполнения")

                    # Преобразование boolean
                    if is_production.lower() in ('true', '1', 'yes', 't', 'да'):
                        is_production_bool = True
                    elif is_production.lower() in ('false', '0', 'no', 'f', 'нет', ''):
                        is_production_bool = False
                    else:
                        raise ValueError("IsProduction должен быть True/False")

                    # Преобразование массива actual_versions
                    versions_array = None
                    if actual_versions and actual_versions != '{}' and actual_versions != 'None':
                        try:
                            # Преобразуем строку в массив Python
                            if actual_versions.startswith('{') and actual_versions.endswith('}'):
                                # Убираем фигурные скобки и разделяем элементы
                                elements = actual_versions[1:-1].split(',')
                                versions_array = [elem.strip() for elem in elements if elem.strip()]
                            else:
                                # Если не в формате массива, пытаемся разделить по запятой
                                elements = actual_versions.split(',')
                                versions_array = [elem.strip() for elem in elements if elem.strip()]
                        except ValueError as e:
                            raise ValueError(f"Некорректный формат массива версий: {e}")

                    # Валидация дат
                    if created_at:
                        try:
                            if created_at != 'NULL':
                                datetime.datetime.strptime(created_at, '%Y-%m-%d')
                        except ValueError:
                            raise ValueError(f"Неверный формат даты CreatedAt: {created_at}. Используйте YYYY-MM-DD")

                    if updated_at:
                        try:
                            if updated_at != 'NULL':
                                datetime.datetime.strptime(updated_at, '%Y-%m-%d')
                        except ValueError:
                            raise ValueError(f"Неверный формат даты UpdatedAt: {updated_at}. Используйте YYYY-MM-DD")

                    if model_id == 'NEW' or not model_id:
                        cursor.execute(f"""
                            INSERT INTO {current_schema}.ai_models 
                            (name, description, version, framework, is_production, production, 
                             created_at, updated_at, attack_type, actual_versions)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING model_id
                        """, (
                            name.strip(),
                            description.strip(),
                            version.strip(),
                            framework.strip(),
                            is_production_bool,
                            production.strip() if production else None,
                            created_at if created_at else None,
                            updated_at if updated_at else None,
                            attack_type if attack_type else None,
                            versions_array  # Массив версий
                        ))

                        # Получаем новый ID и обновляем отображение
                        new_id = cursor.fetchone()[0]
                        new_values = list(values)
                        new_values[0] = str(new_id)
                        self.edit_tree.item(item, values=new_values)
                        success_count += 1

                    else:
                        # Обновление существующей записи
                        cursor.execute(f"""
                            UPDATE {current_schema}.ai_models 
                            SET name = %s, description = %s, version = %s, framework = %s, 
                                is_production = %s, production = %s, created_at = %s, 
                                updated_at = %s, attack_type = %s, actual_versions = %s
                            WHERE model_id = %s
                        """, (
                            name.strip(),
                            description.strip(),
                            version.strip(),
                            framework.strip(),
                            is_production_bool,
                            production.strip() if production else None,
                            created_at if created_at else None,
                            updated_at if updated_at else None,
                            attack_type if attack_type else None,
                            versions_array,  # Массив версий
                            int(model_id)
                        ))
                        success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"Строка {model_id if model_id != 'NEW' else 'NEW'}: {str(e)}")
                    continue

            if error_count > 0:
                self.conn.rollback()
                error_msg = f"Ошибки при сохранении ({error_count} из {len(all_items)} строк):\n" + "\n".join(
                    errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... и еще {len(errors) - 5} ошибок"
                messagebox.showerror("Ошибки сохранения", error_msg)
            else:
                self.conn.commit()
                messagebox.showinfo("Успех", f"Все {success_count} строк успешно сохранены")
            self.load_data_for_editing()

        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", f"Критическая ошибка при сохранении данных: {e}")

    def create_enum_types(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'attacks')")
            if cursor.fetchone()[0]:
                messagebox.showinfo(" ", "enum тип создан или уже существет")
                return True

            cursor.execute("CREATE TYPE attacks AS ENUM ('DDoS', 'Malware', 'IoT')")
            self.conn.commit()
            messagebox.showinfo("Успех", "Созданы пользовательские типы ENUM")
            return True
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                messagebox.showinfo("Тип ENUM уже существует")
                return True
            messagebox.showerror("Ошибка", f"Ошибка при создании пользовательских типов: {e}")
            self.conn.rollback()
            return False

    def open_table(self):
        table = tk.Toplevel(self.root)
        table.title("Просмотр данных")
        table.geometry("1600x600")  # Увеличили ширину для нового столбца

        frame = ttk.Frame(table)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_scroll_y = ttk.Scrollbar(frame, orient='vertical')
        tree_scroll_y.pack(side='right', fill='y')

        tree_scroll_x = ttk.Scrollbar(frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')

        # Обновленные колонки с добавлением ActualVersions
        self.tree = ttk.Treeview(frame,
                                 columns=('ID', 'Name', 'Description', 'Version', 'Framework',
                                          'IsProduction', 'Production', 'CreatedAt', 'UpdatedAt', 'AttackType',
                                          'ActualVersions'),
                                 show='headings',
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set)

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Обновленные колонки с ширинами
        columns = [
            ('ID', 80), ('Name', 120), ('Description', 200), ('Version', 100), ('Framework', 120),
            ('IsProduction', 100), ('Production', 120), ('CreatedAt', 120), ('UpdatedAt', 120),
            ('AttackType', 120), ('ActualVersions', 200)  # Новый столбец
        ]

        for col, width in columns:
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=width, anchor='w')

        self.tree.pack(fill='both', expand=True)
        self.tree.tag_configure('evenrow', background='#f0f0f0')

        button_frame = ttk.Frame(table)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="Обновить данные", command=self.load_table_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", command=table.destroy).pack(side='right', padx=5)

        self.load_table_data()

    def create_table(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return False

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'ai_models' 
                    AND table_name = 'ai_models'
                )
            """)
            if cursor.fetchone()[0]:
                # Проверяем, существует ли уже столбец actual_versions
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'ai_models' 
                    AND table_name = 'ai_models' 
                    AND column_name = 'actual_versions'
                """)
                if not cursor.fetchone():
                    # Добавляем столбец actual_versions если его нет
                    cursor.execute("""
                        ALTER TABLE ai_models.ai_models 
                        ADD COLUMN actual_versions TEXT[]
                    """)
                    self.conn.commit()
                    messagebox.showinfo("Успех", "Столбец actual_versions добавлен в существующую таблицу")
                return True

            cursor.execute("""
                CREATE TABLE ai_models.ai_models (
                    model_id SERIAL NOT NULL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    version TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    is_production BOOLEAN NOT NULL,
                    production TEXT,
                    created_at DATE,
                    updated_at DATE,
                    attack_type attacks,
                    actual_versions TEXT[]  -- НОВЫЙ СТОЛБЕЦ С МАССИВОМ ВЕРСИЙ
                )
            """)
            self.conn.commit()
            messagebox.showinfo("Успех", "Таблица успешно создана")
            return True
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании таблицы: {e}")
            self.conn.rollback()
            return False

    def create_table_and_schema(self):
        table_create = Toplevel(self.root)
        table_create.title("Создание таблицы")
        table_create.geometry("600x400")

        table_create.transient(self.root)
        table_create.grab_set()

        ttk.Button(table_create, text="Подключиться к БД", command=self.connect_db).pack(pady=10)
        ttk.Button(table_create, text="Создать схему в БД", command=self.create_schema).pack(pady=10)
        ttk.Button(table_create, text="Создать пользовательские типы ENUM", command=self.create_enum_types).pack(
            pady=10)
        ttk.Button(table_create, text="Создать таблицы", command=self.create_table).pack(pady=10)
        ttk.Button(table_create, text="Редактировать данные", command=lambda: self.edit_data(table_create)).pack(
            pady=10)
        ttk.Button(table_create, text="Закрыть", command=table_create.destroy).pack(side='left', padx=20)
        ttk.Button(table_create, text="Обновить", command=self.connect_db).pack(side='right', padx=20)

    def load_data(self):
        if hasattr(self, 'tree'):
            self.load_table_data()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()