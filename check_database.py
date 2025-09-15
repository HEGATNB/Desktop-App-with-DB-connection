import psycopg2
import time


def check_database_connection():
    """Проверка подключения к базе данных"""
    try:
        # Параметры подключения (те же что в main.py)
        params = {
            'host': 'localhost',
            'database': 'ai_ddos_detection',  # Изменено на нашу базу
            'user': 'postgres',
            'password': '12345678',
            'port': '5432'
        }

        print("Попытка подключения к базе данных...")
        print(f"Параметры: host={params['host']}, db={params['database']}, user={params['user']}")

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        print('✅ Подключение к PostgreSQL успешно!')

        # Проверяем версию PostgreSQL
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        print(f"Версия PostgreSQL: {db_version[0]}")

        # Проверяем нашу таблицу
        cur.execute("SELECT COUNT(*) FROM ai_models")
        count = cur.fetchone()[0]
        print(f"Количество записей в ai_models: {count}")

        # Показываем содержимое таблицы
        if count > 0:
            print("\nСодержимое таблицы ai_models:")
            cur.execute("SELECT model_id, name, version, is_production FROM ai_models")
            for row in cur.fetchall():
                production = "Да" if row[3] else "Нет"
                print(f"ID: {row[0]}, Name: {row[1]}, Version: {row[2]}, Production: {production}")

        cur.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "database \"ai_ddos_detection\" does not exist" in error_msg:
            print("❌ Ошибка: База данных 'ai_ddos_detection' не существует!")
            print("Запустите setup.py для создания базы: python setup.py")
        elif "password authentication failed" in error_msg:
            print("❌ Ошибка: Неверный пароль PostgreSQL!")
        elif "connection refused" in error_msg.lower():
            print("❌ Ошибка: PostgreSQL не запущен!")
        else:
            print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as error:
        print(f"❌ Неизвестная ошибка: {error}")
        return False


if __name__ == '__main__':
    print("=== Проверка подключения к базе данных ===\n")
    success = check_database_connection()

    if success:
        print("\n✅ Проверка завершена успешно!")
    else:
        print("\n❌ Проверка не удалась!")

    print("\nДля выхода нажмите Enter...")
    input()