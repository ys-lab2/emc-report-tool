from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from utils.app_paths import app_base_dir

LOG_DIR = app_base_dir() / "logs"
LOG_FILE = LOG_DIR / "app.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)
