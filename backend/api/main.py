"""
FastAPI приложение
"""
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import services, users, tasks, logs

# Создание приложения
app = FastAPI(
    title="Task Management API",
    description="Async API для управления сервисами, пользователями и задачами",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(services.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(logs.router)

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }