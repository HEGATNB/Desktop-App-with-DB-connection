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
        """Простое подключение к БД"""
        try:
            return psycopg2.connect(
                host="localhost",
                database="ai_ddos_detection",
                user="postgres",
                password="12345678",  # Пароль который задавали при установке
                port="5432"
            )
        except Exception as e:
            messagebox.showerror("Ошибка",
                                 f"Не удалось подключиться к БД:\n"
                                 f"1. Убедитесь что PostgreSQL запущен\n"
                                 f"2. Пароль: 12345678\n"
                                 f"3. База ai_ddos_detection создана\n\n"
                                 f"Ошибка: {e}")
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