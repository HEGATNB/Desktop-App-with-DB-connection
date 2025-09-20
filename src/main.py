import psycopg2
import tkinter as tk
import pydoc
from tkinter import ttk, messagebox,  Toplevel, Label, Button
from psycopg2 import Error

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Monitor")
        self.root.geometry("600x400")
        self.create_widgets()
        self.conn= None
        #Подключение к стандартной бд

    def connect_db(self):
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="12345678",
                port="5432"
            )
            #Проверим существование нужной базы
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_ddos_detection'")
                if not cur.fetchone():
                    messagebox.showwarning("Внимание",
                                           "База данных 'ai_ddos_detection' не существует.\n"
                                           "Создайте её командой: CREATE DATABASE ai_ddos_detection;")
                    return None

            #Переподключаемся к нужной базе
            conn.close()
            messagebox.showinfo("","База данных успешно подключена")
            return psycopg2.connect(
                host="localhost",
                database="ai_ddos_detection",
                user="postgres",
                password="12345678",
                port="5432"
            )

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if "password authentication failed" in error_msg:
                messagebox.showerror("Ошибка",
                                     "Неверный пароль PostgreSQL.\n"
                                     "Проверьте пароль или сбросьте его через pgAdmin.")
            elif "connection refused" in error_msg.lower():
                messagebox.showerror("Ошибка",
                                     "PostgreSQL не запущен!\n"
                                     "Запустите службу PostgreSQL через services.msc")
            else:
                messagebox.showerror("Ошибка", f"Ошибка подключения: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")
            return None

        #Основное окно
    def create_widgets(self):
        tk.Button(self.root, text= " Создать схему и таблицы", command=self.create_table).pack(pady=20)
        tk.Button(self.root, text = " Внести данные",command=self.open_modal_window).pack(pady=20)
        tk.Button(self.root, text = "Показать данные",command=self.open_table).pack(pady=20)

        #Окно для изменения таблицы
    def open_modal_window(self):
        AddData = Toplevel(self.root)
        AddData.transient(self.root)
        AddData.grab_set()
        AddData.title("Внесение данных")
        AddData.geometry("600x400")
        ttk.Button(AddData, text="Сохранить", command= self.open_table).pack(pady=20)
        ttk.Button(AddData, text="Отмена", command= AddData.destroy).pack(pady=20)
        AddData.wait_window(AddData)

        #Создание схемы
    def create_schema(self,connection):
        cursor = connection.cursor()
        cursor.execute("CREATE SCHEMA IF NOT EXISTS ai_ddos_detection")
        messagebox.showinfo(" ","Схема успешно создана")
        if not cursor.fetchone():
            messagebox.showwarning("Внимание","Cхема не создана")
            return None

        #Окно открытой таблицы
    def open_table(self):
        table = tk.Tk()
        table.title("Таблица")
        table.geometry("600x400")
        self.tree = ttk.Treeview(table, columns=('ID', 'Name', 'Version', 'Production'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Version', text='Version')
        self.tree.heading('Production', text='Production')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        #Окно создания таблицы
    def create_table(self):
        table_create = tk.Tk()
        table_create.title("Создание таблицы")
        table_create.geometry("600x400")
        tk.Button(table_create,text="Создать схему в БД", command=self.create_schema(self.conn)).pack(pady=(90,15)) #ПОМЕНЯТЬ КОМАНДЫ НА РАБОЧИЕ
        tk.Button(table_create,text="Создать БД", command=self.connect_db).pack(pady=15)
        tk.Button(table_create,text="Создать пользовательские типы ENUM", command=self.open_table).pack(pady=15)   #ПОМЕНЯТЬ КОМАНДЫ НА РАБОЧИЕ
        tk.Button(table_create,text="Создать таблицы", command=self.open_table).pack(pady=15)    #ПОМЕНЯТЬ КОМАНДЫ НА РАБОЧИЕ
        tk.Button(table_create,text="Добавить текстовые данные",command=self.open_table).pack(pady=15)   #ПОМЕНЯТЬ КОМАНДЫ НА РАБОЧИЕ
        tk.Button(table_create, text="Выполнить", command=self.open_table).pack(side="left",padx=(95,0))  # ПОМЕНЯТЬ КОМАНДЫ НА РАБОЧИЕ
        tk.Button(table_create, text="Отмена", command=table_create.destroy).pack(side="right",padx=(0,95))

    # Загрузка данных из таблицы
    def load_data(self):
        def load_data(self):
            try:
                # Пытаемся загрузить данные
                with self.conn.cursor() as cur:
                    cur.execute("SELECT * FROM ai_models")
            except psycopg2.Error as e:
                # Если таблицы нет- показываем ошибку
                messagebox.showerror("Ошибка",
                                     "Таблица 'ai_models' не существует!\n\n"
                                     "Нажмите 'Создать схему БД' для создания таблиц.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()