import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox


class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Monitor")
        self.root.geometry("600x400")

        self.conn = self.connect_db()
        self.create_widgets()
        self.load_data()

    def connect_db(self):
        """Простое подключение к БД с улучшенной диагностикой"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",  # Сначала подключимся к стандартной базе
                user="postgres",
                password="12345678",
                port="5432"
            )

            # Проверим существование нужной базы
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_ddos_detection'")
                if not cur.fetchone():
                    messagebox.showwarning("Внимание",
                                           "База данных 'ai_ddos_detection' не существует.\n"
                                           "Создайте её командой: CREATE DATABASE ai_ddos_detection;")
                    return None

            # Переподключаемся к нужной базе
            conn.close()
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

    def create_widgets(self):
        """Простой интерфейс"""
        self.tree = ttk.Treeview(self.root, columns=('ID', 'Name', 'Version', 'Production'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Version', text='Version')
        self.tree.heading('Production', text='Production')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Button(self.root, text="Обновить", command=self.load_data).pack(pady=5)

    def load_data(self):
        """Загрузка данных"""
        if not self.conn:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT model_id, name, version, is_production FROM ai_models")
                for row in cur.fetchall():
                    production = "Да" if row[3] else "Нет"
                    self.tree.insert('', 'end', values=(row[0], row[1], row[2], production))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()