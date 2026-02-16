"""
Точка входа для запуска сервера
"""
import os
import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.append(str(Path(__file__).parent))

# Теперь можем импортировать из пакета backend
from backend.api.main import app

if __name__ == "__main__":
    import uvicorn

    # Настройки из .env
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True") == "True"

    print(f"🚀 Запуск сервера на http://{host}:{port}")
    print(f"📚 Документация: http://{host}:{port}/docs")

    # Запуск сервера
    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )