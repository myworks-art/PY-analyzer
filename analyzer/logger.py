"""
analyzer/logger.py — централизованное логирование.

Конфигурирует один логгер для всего приложения.
Пишет одновременно в консоль и в файл logs/analyzer.log.

Использование:
    from analyzer.logger import get_logger
    log = get_logger(__name__)
    log.info("Парсинг файла %s", filename)
    log.warning("Правило %s вернуло пустой результат", rule_id)
    log.error("Ошибка парсинга: %s", exc)
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Константы ──────────────────────────────────────────────────────────────
LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "analyzer.log"

# Формат строки лога
_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"

# Максимальный размер файла и количество ротаций
_MAX_BYTES   = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

_configured = False


def _configure() -> None:
    """Один раз настраивает корневой логгер."""
    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger("analyzer")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FMT, datefmt=_DATE)

    # ── Консоль (INFO и выше) ──────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    # ── Файл с ротацией (DEBUG и выше) ────────────────────────────────────
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
    """
    Получить логгер для модуля.

    Args:
        name: обычно передают __name__

    Returns:
        logging.Logger с настроенными хендлерами
    """
    _configure()
    # Все логгеры с префиксом "analyzer." наследуют настройки корневого
    if not name.startswith("analyzer"):
        name = f"analyzer.{name}"
    return logging.getLogger(name)
