# logging_config.py (без изменений)
import logging
import os

def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "..", "database")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "logs.txt")

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[file_handler]
    )
    return logging.getLogger(__name__)