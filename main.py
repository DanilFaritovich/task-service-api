#!/usr/bin/env python
"""
Главный файл для запуска приложения
"""

import logging
import sys
from pathlib import Path

import uvicorn

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Запуск FastAPI приложения"""
    logger.info("Starting Task Service API...")

    uvicorn.run(
        "backend.api.main:app",  # Импорт из backend.api.main
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True,
        timeout_keep_alive=30,
    )


if __name__ == "__main__":
    main()
