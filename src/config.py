import os
import logging.config
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

TZ = ZoneInfo('Europe/Moscow')

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(ROOT_DIR / '.env')

DB_PATH = BASE_DIR / os.getenv('DB_PATH')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

# ------------------------------------ Logging ------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        # 1. Хэндлер для INFO и выше (основной лог)
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'standard',
            'filename': ROOT_DIR / 'info.log',
            'encoding': 'utf-8',
        },
        # 2. Хэндлер СТРОГО для ошибок
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'standard',
            'filename': ROOT_DIR / 'errors.log',
            'encoding': 'utf-8',
        },
        # 3. Консоль для удобства разработки
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['error_file', 'console'],
    },
    'loggers': {
        'src': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

logging.config.dictConfig(LOGGING)
