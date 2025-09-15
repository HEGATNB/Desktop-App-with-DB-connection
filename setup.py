import subprocess
import sys
import psycopg2
from configparser import ConfigParser


def install_dependencies():
    """Установка зависимостей"""
    print("Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены успешно!")
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки зависимостей")


def create_database():
    """Создание базы данных и таблиц"""
    print("Создание базы данных...")
    try:
        # Подключаемся к стандартной базе postgres
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="12345678",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Проверяем существование базы
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_ddos_detection'")
        exists = cur.fetchone()

        if not exists:
            # Создаем базу данных
            cur.execute("CREATE DATABASE ai_ddos_detection")
            print("✅ База данных 'ai_ddos_detection' создана")
        else:
            print("✅ База данных 'ai_ddos_detection' уже существует")

        # Подключаемся к новой базе
        cur.close()
        conn.close()

        conn = psycopg2.connect(
            host="localhost",
            database="ai_ddos_detection",
            user="postgres",
            password="12345678",
            port="5432"
        )
        cur = conn.cursor()

        # Создаем таблицу
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_models (
                model_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                version VARCHAR(50),
                is_production BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Добавляем тестовые данные
        cur.execute("""
            INSERT INTO ai_models (name, version, is_production) 
            VALUES 
                ('DDoS Detection Model v1', '1.0', TRUE),
                ('Traffic Analysis AI', '2.1', FALSE),
                ('Security Monitor', '1.5', TRUE)
            ON CONFLICT DO NOTHING
        """)

        conn.commit()
        print("✅ Таблица 'ai_models' создана с тестовыми данными")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("\nУбедитесь, что:")
        print("1. PostgreSQL запущен")
        print("2. Пароль правильный (12345678)")
        print("3. Порт 5432 доступен")
    except Exception as e:
        print(f"❌ Ошибка при создании базы данных: {e}")


if __name__ == "__main__":
    install_dependencies()
    create_database()
    print("\nУстановка завершена! Запустите main.py")
    input("Нажмите Enter для выхода...")