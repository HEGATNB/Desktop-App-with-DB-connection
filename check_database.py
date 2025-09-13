import psycopg2
import tkinter as tk
from tkinter import messagebox


def test_connection():
    """Тестирование всех возможных вариантов подключения"""

    connections = [
        {
            'name': 'ai_ddos_detection',
            'host': 'localhost',
            'database': 'ai_ddos_detection',
            'user': 'postgres',
            'password': '12345678'
        },
        {
            'name': 'postgres (стандартная БД)',
            'host': 'localhost',
            'database': 'postgres',
            'user': 'postgres',
            'password': '12345678'
        },
        {
            'name': 'без указания БД',
            'host': 'localhost',
            'user': 'postgres',
            'password': '12345678'
        }
    ]

    results = []

    for config in connections:
        try:
            conn = psycopg2.connect(
                host=config['host'],
                database=config.get('database'),
                user=config['user'],
                password=config['password'],
                client_encoding='utf-8'
            )

            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version()")
                db_info = cur.fetchone()

            results.append(f"✅ {config['name']}: УСПЕХ - {db_info}")
            conn.close()

        except Exception as e:
            results.append(f"❌ {config['name']}: ОШИБКА - {str(e)}")

    # Показываем результаты
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно

    result_text = "\n".join(results)
    messagebox.showinfo("Результаты тестирования подключения", result_text)

    root.destroy()


if __name__ == "__main__":
    test_connection()