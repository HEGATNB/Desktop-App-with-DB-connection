## 📋 Гайд

1. **Установите PostgreSQL** с официального сайта (https://www.postgresql.org/download)
2. **Запомните пароль** при установке (12345678) порт (5433)
3. **Скачать pgAdmin4** (https://www.pgadmin.org/download)
4. **Склонируйте проект**: `git clone https://github.com/HEGATNB/Desktop-App-with-DB-connection.git`
5. **Запустите setup**: `python setup.py`
6. **Запустите приложение**: `python src/main.py`

## 🔧 Если возникают проблемы:

1. **Проверьте что PostgreSQL запущен** (в службах Windows)
2. **Измените пароль** в src/main.py на ваш пароль от PostgreSQL
3. **Создайте БД вручную** в pgAdmin: `ai_ddos_detection`
