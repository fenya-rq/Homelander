import os
import logging.config
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

TZ = ZoneInfo('Asia/Bangkok')

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(ROOT_DIR / '.env')

DB_PATH = BASE_DIR / os.getenv('DB_PATH')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ------------------------------------ Logging ------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": ROOT_DIR / "debug.log",
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"],
    },
    "loggers": {
        "main": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING)
