from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_DEFAULT_LOG_DIR = "/app/logs" if Path("/app/logs").exists() else "logs"
LOG_DIR  = Path(os.getenv("LOG_DIR", _DEFAULT_LOG_DIR))
LOG_FILE = LOG_DIR / "analyzer.log"

_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES   = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

_configured = False

def _configure() -> None:

    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger("analyzer")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FMT, datefmt=_DATE)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError as e:
        root.warning("Не удалось открыть лог-файл %s: %s", LOG_FILE, e)

    root.info("Логгер инициализирован. Файл: %s", LOG_FILE.resolve())


def get_logger(name: str) -> logging.Logger:
    _configure()
    if not name.startswith("analyzer"):
        name = f"analyzer.{name}"
    return logging.getLogger(name)
