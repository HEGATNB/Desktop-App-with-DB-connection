-- Простая схема без сложных типов (для совместимости)
CREATE TABLE IF NOT EXISTS ai_models (
    model_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    is_production BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(model_id),
    status VARCHAR(20) CHECK (status IN ('planned', 'running', 'completed', 'failed')),
    accuracy REAL CHECK (accuracy >= 0 AND accuracy <= 1),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Тестовые данные
INSERT INTO ai_models (name, version, is_production) VALUES 
('CNN-Model', '1.0', true),
('LSTM-Model', '2.1', false);

INSERT INTO experiments (model_id, status, accuracy) VALUES
(1, 'completed', 0.95),
(2, 'running', NULL);