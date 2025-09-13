import os
import subprocess
import sys


def install_requirements():
    """Установка зависимостей"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def check_postgres():
    """Проверка установлен ли PostgreSQL"""
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
        return True
    except:
        return False


def create_database():
    """Создание БД через командную строку"""
    try:
        # Создаем базу данных
        subprocess.run([
            "psql", "-U", "postgres",
            "-c", "CREATE DATABASE ai_ddos_detection ENCODING 'UTF8';"
        ], check=True)

        # Запускаем SQL скрипт
        subprocess.run([
            "psql", "-U", "postgres", "-d", "ai_ddos_detection",
            "-f", "database/schema.sql"
        ], check=True)

        print("✅ База данных создана успешно!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании БД: {e}")
        return False


if __name__ == "__main__":
    print("Установка зависимостей...")
    install_requirements()

    print("Проверка PostgreSQL...")
    if not check_postgres():
        print("❌ PostgreSQL не установлен. Установите его с официального сайта")
        sys.exit(1)

    print("Создание базы данных...")
    create_database()
    print("✅ Настройка завершена! Запустите: python src/main.py")