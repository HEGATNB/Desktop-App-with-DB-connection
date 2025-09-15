import psycopg2
import subprocess
import os
from datetime import datetime

def export_database():
    """Экспорт данных в SQL файл"""
    try:
        # Создаем дамп базы данных
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_dump_{timestamp}.sql"
        
        # Команда для pg_dump
        cmd = [
            'pg_dump',
            '-h', 'localhost',
            '-U', 'postgres',
            '-d', 'ai_ddos_detection',
            '-f', filename,
            '--inserts'  # Чтобы данные были в виде INSERT语句
        ]
        
        # Устанавливаем переменную окружения с паролем
        env = os.environ.copy()
        env['PGPASSWORD'] = '12345678'
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Данные экспортированы в {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return None

def import_database(filename):
    """Импорт данных из SQL файла"""
    try:
        # Команда для psql
        cmd = [
            'psql',
            '-h', 'localhost',
            '-U', 'postgres',
            '-d', 'ai_ddos_detection',
            '-f', filename
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = '12345678'
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Данные импортированы из {filename}")
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")

if __name__ == "__main__":
    print("1. Экспорт данных")
    print("2. Импорт данных")
    choice = input("Выберите действие (1/2): ")
    
    if choice == "1":
        export_database()
    elif choice == "2":
        files = [f for f in os.listdir('.') if f.startswith('database_dump_') and f.endswith('.sql')]
        if files:
            print("Доступные дампы:")
            for i, f in enumerate(files, 1):
                print(f"{i}. {f}")
            file_choice = int(input("Выберите файл: ")) - 1
            import_database(files[file_choice])
        else:
            print("Нет файлов дампа")