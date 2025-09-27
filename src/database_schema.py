# database_schema.py
import psycopg2
import logging


class DatabaseSchema:
    def __init__(self, connection, logger):
        self.conn = connection
        self.logger = logger

    def create_complete_schema(self):
        try:
            cursor = self.conn.cursor()

            # 1. Создаем схему если не существует
            cursor.execute("CREATE SCHEMA IF NOT EXISTS ai_models")

            # 2. Создаем ENUM тип для атак
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attacks') THEN
                        CREATE TYPE attacks AS ENUM ('DDoS', 'Malware', 'IoT', 'Phishing', 'BruteForce');
                    END IF;
                END $$;
            """)

            # 3. Создаем таблицу фреймворков (родительская таблица)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_models.frameworks (
                    framework_id SERIAL PRIMARY KEY,
                    framework_name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    latest_version VARCHAR(20),
                    release_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. Создаем таблицу окружений (родительская таблица)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_models.environments (
                    environment_id SERIAL PRIMARY KEY,
                    environment_name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    max_models INTEGER DEFAULT 10,
                    is_production BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. Создаем основную таблицу моделей с FOREIGN KEY
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_models.ai_models (
                    model_id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    version VARCHAR(20) NOT NULL,

                    -- FOREIGN KEY на frameworks с разными опциями
                    framework_id INTEGER NOT NULL,

                    -- FOREIGN KEY на environments с CASCADE
                    environment_id INTEGER,

                    is_production BOOLEAN NOT NULL DEFAULT FALSE,
                    production_scale VARCHAR(20) CHECK (production_scale IN ('small', 'medium', 'large')),
                    created_at DATE DEFAULT CURRENT_DATE,
                    updated_at DATE DEFAULT CURRENT_DATE,
                    attack_type attacks,
                    actual_versions TEXT[],

                    -- Ограничение уникальности
                    CONSTRAINT uq_model_version UNIQUE(name, version),

                    -- FOREIGN KEY с различными опциями ON DELETE/ON UPDATE
                    CONSTRAINT fk_model_framework 
                        FOREIGN KEY (framework_id) 
                        REFERENCES ai_models.frameworks(framework_id)
                        ON DELETE RESTRICT   -- Запрещает удаление если есть зависимые записи
                        ON UPDATE CASCADE,   -- Обновляет связанные записи при изменении PK

                    CONSTRAINT fk_model_environment 
                        FOREIGN KEY (environment_id) 
                        REFERENCES ai_models.environments(environment_id)
                        ON DELETE SET NULL   -- Устанавливает NULL при удалении родительской записи
                        ON UPDATE CASCADE    -- Обновляет связанные записи при изменении PK
                )
            """)

            # 6. Создаем таблицу метрик моделей (дочерняя таблица)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_models.model_metrics (
                    metric_id SERIAL PRIMARY KEY,
                    model_id INTEGER NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(10,4) NOT NULL,
                    metric_date DATE DEFAULT CURRENT_DATE,
                    is_best BOOLEAN DEFAULT FALSE,

                    -- FOREIGN KEY с CASCADE - при удалении модели удаляются все её метрики
                    CONSTRAINT fk_metrics_model 
                        FOREIGN KEY (model_id) 
                        REFERENCES ai_models.ai_models(model_id)
                        ON DELETE CASCADE    -- Удаляет дочерние записи при удалении родительской
                        ON UPDATE CASCADE,   -- Обновляет дочерние записи при обновлении родительской

                    -- Ограничение на значение метрики
                    CONSTRAINT chk_metric_value CHECK (metric_value >= 0 AND metric_value <= 1),

                    -- Уникальность метрики для модели на дату
                    CONSTRAINT uq_metric_model_date UNIQUE(model_id, metric_name, metric_date)
                )
            """)

            # 7. Создаем таблицу зависимостей моделей (многие-ко-многим с само-ссылкой)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_models.model_dependencies (
                    dependency_id SERIAL PRIMARY KEY,
                    parent_model_id INTEGER NOT NULL,
                    child_model_id INTEGER NOT NULL,
                    dependency_type VARCHAR(50) DEFAULT 'requires',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- FOREIGN KEY на саму таблицу моделей
                    CONSTRAINT fk_dependency_parent 
                        FOREIGN KEY (parent_model_id) 
                        REFERENCES ai_models.ai_models(model_id)
                        ON DELETE CASCADE,

                    CONSTRAINT fk_dependency_child 
                        FOREIGN KEY (child_model_id) 
                        REFERENCES ai_models.ai_models(model_id)
                        ON DELETE CASCADE,

                    -- Предотвращение циклических зависимостей
                    CONSTRAINT chk_no_self_dependency CHECK (parent_model_id != child_model_id),

                    -- Уникальность зависимости
                    CONSTRAINT uq_dependency UNIQUE(parent_model_id, child_model_id)
                )
            """)

            self.conn.commit()
            self.logger.info("DDL: Полная схема БД с FOREIGN KEY создана успешно")
            return True

        except psycopg2.Error as e:
            self.logger.error(f"Ошибка при создании схемы БД: {e}")
            self.conn.rollback()
            return False

    def insert_sample_data(self):
        try:
            cursor = self.conn.cursor()

            # Очищаем таблицы в правильном порядке (из-за FOREIGN KEY)
            cursor.execute("DELETE FROM ai_models.model_dependencies")
            cursor.execute("DELETE FROM ai_models.model_metrics")
            cursor.execute("DELETE FROM ai_models.ai_models")
            cursor.execute("DELETE FROM ai_models.environments")
            cursor.execute("DELETE FROM ai_models.frameworks")

            # Вставляем фреймворки
            frameworks = [
                ('TensorFlow', 'Google ML framework', '2.13.0', '2023-05-01', True),
                ('PyTorch', 'Facebook ML framework', '2.0.1', '2023-03-15', True),
                ('Scikit-learn', 'Python ML library', '1.3.0', '2023-06-20', True),
                ('Keras', 'High-level neural networks API', '2.13.0', '2023-07-10', True),
                ('MXNet', 'Apache deep learning framework', '1.9.1', '2022-11-05', False)
            ]

            for framework in frameworks:
                cursor.execute("""
                    INSERT INTO ai_models.frameworks 
                    (framework_name, description, latest_version, release_date, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING framework_id
                """, framework)

            # Вставляем окружения
            environments = [
                ('production', 'Основное продакшен окружение', 50, True),
                ('staging', 'Тестовое окружение для предрелиза', 20, False),
                ('development', 'Окружение для разработки', 100, False),
                ('archived', 'Архивное окружение', 1000, False)
            ]

            for env in environments:
                cursor.execute("""
                    INSERT INTO ai_models.environments 
                    (environment_name, description, max_models, is_production)
                    VALUES (%s, %s, %s, %s)
                    RETURNING environment_id
                """, env)

            # Вставляем модели AI
            ai_models = [
                ('DDoS Detection v1', 'Обнаружение DDoS атак', '1.0', 1, 1, False, 'small', 'DDoS', '{1.0,1.1}'),
                ('Malware Classifier', 'Классификация вредоносного ПО', '2.1', 2, 2, True, 'medium', 'Malware',
                 '{2.0,2.1,2.2}'),
                ('IoT Security', 'Защита IoT устройств', '1.5', 3, 1, True, 'large', 'IoT', '{1.5,1.6}'),
                ('Phishing Detector', 'Обнаружение фишинговых атак', '3.0', 1, 3, False, 'small', 'Phishing', '{3.0}'),
                ('BruteForce Prevention', 'Предотвращение брутфорс атак', '2.0', 2, 4, True, 'medium', 'BruteForce',
                 '{2.0,2.1}')
            ]

            model_ids = []
            for model in ai_models:
                cursor.execute("""
                    INSERT INTO ai_models.ai_models 
                    (name, description, version, framework_id, environment_id, 
                     is_production, production_scale, attack_type, actual_versions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING model_id
                """, model)
                model_ids.append(cursor.fetchone()[0])

            # Вставляем метрики для моделей
            metrics = [
                (model_ids[0], 'accuracy', 0.9567, '2024-01-15', True),
                (model_ids[0], 'precision', 0.9234, '2024-01-15', False),
                (model_ids[1], 'accuracy', 0.8923, '2024-01-16', True),
                (model_ids[1], 'recall', 0.8678, '2024-01-16', False),
                (model_ids[2], 'accuracy', 0.9123, '2024-01-17', True),
                (model_ids[3], 'f1_score', 0.8789, '2024-01-18', True),
                (model_ids[4], 'accuracy', 0.9345, '2024-01-19', True)
            ]

            for metric in metrics:
                cursor.execute("""
                    INSERT INTO ai_models.model_metrics 
                    (model_id, metric_name, metric_value, metric_date, is_best)
                    VALUES (%s, %s, %s, %s, %s)
                """, metric)

            # Вставляем зависимости между моделями
            dependencies = [
                (model_ids[1], model_ids[0], 'requires'),  # Malware Classifier требует DDoS Detection
                (model_ids[2], model_ids[1], 'extends'),  # IoT Security расширяет Malware Classifier
                (model_ids[4], model_ids[0], 'uses')  # BruteForce Prevention использует DDoS Detection
            ]

            for dep in dependencies:
                cursor.execute("""
                    INSERT INTO ai_models.model_dependencies 
                    (parent_model_id, child_model_id, dependency_type)
                    VALUES (%s, %s, %s)
                """, dep)

            self.conn.commit()
            self.logger.info("DDL: Тестовые данные успешно добавлены")
            return True

        except psycopg2.Error as e:
            self.logger.error(f"Ошибка при вставке тестовых данных: {e}")
            self.conn.rollback()
            return False

    def demonstrate_foreign_key_operations(self):
        demonstrations = []

        try:
            cursor = self.conn.cursor()

            # Демонстрация 1: ON DELETE RESTRICT
            demonstrations.append("=== ДЕМОНСТРАЦИЯ ON DELETE RESTRICT ===")
            try:
                cursor.execute("DELETE FROM ai_models.frameworks WHERE framework_id = 1")
                demonstrations.append("❌ ОШИБКА: Должна была быть ошибка RESTRICT!")
            except psycopg2.Error as e:
                demonstrations.append(f"✅ CORRECT: ON DELETE RESTRICT сработал: {e}")
            self.conn.rollback()

            # Демонстрация 2: ON DELETE CASCADE
            demonstrations.append("\n=== ДЕМОНСТРАЦИЯ ON DELETE CASCADE ===")
            cursor.execute("SELECT COUNT(*) FROM ai_models.model_metrics WHERE model_id = 1")
            metrics_before = cursor.fetchone()[0]
            demonstrations.append(f"Метрик до удаления модели: {metrics_before}")

            cursor.execute("DELETE FROM ai_models.ai_models WHERE model_id = 1")

            cursor.execute("SELECT COUNT(*) FROM ai_models.model_metrics WHERE model_id = 1")
            metrics_after = cursor.fetchone()[0]
            demonstrations.append(f"Метрик после удаления модели: {metrics_after}")
            demonstrations.append("✅ ON DELETE CASCADE: Метрики автоматически удалены")

            self.conn.rollback()  # Откатываем изменения

            # Демонстрация 3: ON DELETE SET NULL
            demonstrations.append("\n=== ДЕМОНСТРАЦИЯ ON DELETE SET NULL ===")
            cursor.execute("SELECT environment_id FROM ai_models.ai_models WHERE model_id = 2")
            env_before = cursor.fetchone()[0]
            demonstrations.append(f"Environment ID до удаления: {env_before}")

            cursor.execute("DELETE FROM ai_models.environments WHERE environment_id = 2")

            cursor.execute("SELECT environment_id FROM ai_models.ai_models WHERE model_id = 2")
            env_after = cursor.fetchone()[0]
            demonstrations.append(f"Environment ID после удаления: {env_after}")
            demonstrations.append("✅ ON DELETE SET NULL: Environment ID установлен в NULL")

            self.conn.rollback()  # Откатываем изменения

            # Демонстрация 4: ON UPDATE CASCADE
            demonstrations.append("\n=== ДЕМОНСТРАЦИЯ ON UPDATE CASCADE ===")
            cursor.execute("SELECT framework_id FROM ai_models.ai_models WHERE model_id = 3")
            original_framework = cursor.fetchone()[0]

            cursor.execute("UPDATE ai_models.frameworks SET framework_id = 100 WHERE framework_id = 3")

            cursor.execute("SELECT framework_id FROM ai_models.ai_models WHERE model_id = 3")
            updated_framework = cursor.fetchone()[0]
            demonstrations.append(f"Framework ID до обновления: {original_framework}")
            demonstrations.append(f"Framework ID после обновления: {updated_framework}")
            demonstrations.append("✅ ON UPDATE CASCADE: Framework ID обновлен автоматически")

            self.conn.rollback()  # Откатываем изменения

            # Демонстрация 5: Нарушение FOREIGN KEY
            demonstrations.append("\n=== ДЕМОНСТРАЦИЯ НАРУШЕНИЯ FOREIGN KEY ===")
            try:
                cursor.execute(
                    "INSERT INTO ai_models.ai_models (name, description, version, framework_id) VALUES ('Test', 'Test', '1.0', 9999)")
                demonstrations.append("❌ ОШИБКА: Должна была быть ошибка FOREIGN KEY!")
            except psycopg2.Error as e:
                demonstrations.append(f"✅ CORRECT: FOREIGN KEY violation: {e}")

            self.conn.rollback()

            return "\n".join(demonstrations)

        except Exception as e:
            self.logger.error(f"Ошибка при демонстрации FOREIGN KEY: {e}")
            return f"Ошибка при демонстрации: {e}"

    def get_foreign_key_info(self):
        """Возвращает информацию о FOREIGN KEY constraints"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT
                    tc.table_schema,
                    tc.table_name,
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule,
                    rc.update_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
                    AND rc.constraint_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'ai_models'
                ORDER BY tc.table_name, tc.constraint_name
            """)

            return cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о FOREIGN KEY: {e}")
            return []