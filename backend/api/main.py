import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastcrud import FastCRUD, UpdateConfig, crud_router
from sqlalchemy import and_, func, select, text
from sqlalchemy.exc import IntegrityError

from backend.api.deps import DbDep, db_session_middleware, get_db
from backend.database.base import Base, engine, settings
from backend.database.models import Log, Service, Task, TaskFile, User, UserService
from backend.database.schemas import (
    LogCreate,
    LogResponse,
    LogUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    TaskCreate,
    TaskFileCreate,
    TaskFileResponse,
    TaskFileUpdate,
    TaskResponse,
    TaskUpdate,
    UserCreate,
    UserResponse,
    UserServiceCreate,
    UserServiceResponse,
    UserServiceUpdate,
    UserUpdate,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    События жизненного цикла приложения
    """
    # Startup
    logger.info("🚀 Starting up Application...")

    # Безопасно маскируем пароль в URL
    db_url = str(settings.database_url)
    if hasattr(settings, "db_password") and settings.db_password:
        db_url = db_url.replace(settings.db_password, "******")
    logger.info(f"Database URL: {db_url}")

    # Проверяем подключение к БД
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Database connection successful: {version}")

            # Автоматическое создание таблиц (только для разработки)
            if settings.db_echo:
                logger.info("Creating database tables...")
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Application...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# Создаем приложение
app = FastAPI(
    title="Task Service API",
    description="API для управления сервисами, задачами и пользователями",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для БД
if os.getenv("TESTING_MODE") != "true":
    app.middleware("http")(db_session_middleware)


# Обработчик глобальных исключений
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Обрабатывает ошибки целостности БД (FK, unique) как 400 Bad Request"""
    error_msg = str(exc.orig).lower()

    if "foreign key" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Referenced resource does not exist"},
        )
    elif "unique" in error_msg or "duplicate" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Resource already exists"},
        )

    # Для остальных IntegrityError
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity error"},
    )


# ============================================================================
# АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ CRUD ЭНДПОИНТОВ (БЕЗ СВЯЗЕЙ)
# ============================================================================

# 1. Services - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=Service,
        create_schema=ServiceCreate,
        update_schema=ServiceUpdate,
        select_schema=ServiceResponse,
        path="/services",
        tags=["Services"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
        included_methods=[
            "create",
            "read",
            "update",
            "delete",
            "read_multi",
        ],
    )
)

# 2. Users - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=User,
        create_schema=UserCreate,
        update_schema=UserUpdate,
        select_schema=UserResponse,
        path="/users",
        tags=["Users"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
        update_config=UpdateConfig(
            auto_fields={},  # Provide appropriate auto field mappings if needed
            exclude_from_schema=["created_at", "updated_at"],
        ),
    )
)

# 3. User Services - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=UserService,
        create_schema=UserServiceCreate,
        update_schema=UserServiceUpdate,
        select_schema=UserServiceResponse,
        path="/user-services",
        tags=["User Services"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
    )
)

# 4. Tasks - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=Task,
        create_schema=TaskCreate,
        update_schema=TaskUpdate,
        select_schema=TaskResponse,
        path="/tasks",
        tags=["Tasks"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
        update_config=UpdateConfig(
            auto_fields={},  # Provide appropriate auto field mappings if needed
            exclude_from_schema=["created_at", "updated_at"],
        ),
    )
)

# 5. Task Files - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=TaskFile,
        create_schema=TaskFileCreate,
        update_schema=TaskFileUpdate,
        select_schema=TaskFileResponse,
        path="/task-files",
        tags=["Task Files"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
    )
)

# 6. Logs - только базовые операции
app.include_router(
    crud_router(
        session=get_db,
        model=Log,
        create_schema=LogCreate,
        update_schema=LogUpdate,
        select_schema=LogResponse,
        path="/logs",
        tags=["Logs"],
        deleted_methods=["update", "delete"],
        include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
    )
)


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ
# ============================================================================

# Создаем CRUD объекты для кастомных операций
task_crud = FastCRUD(Task)
user_crud = FastCRUD(User)


@app.get("/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(db: DbDep):
    """
    Получение статистики для дашборда
    """
    # Количество пользователей
    result = await db.execute(select(func.count()).select_from(User))
    users_count = result.scalar()

    # Количество активных задач по статусам
    tasks_by_status = {}
    for status in ["pending", "running", "completed", "failed", "cancelled"]:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status == status)
        )
        tasks_by_status[status] = result.scalar() or 0

    # Последние логи
    result = await db.execute(select(Log).order_by(Log.timestamp.desc()).limit(10))
    recent_logs = result.scalars().all()

    # Статистика по сервисам
    result = await db.execute(select(func.count()).select_from(Service))
    services_count = result.scalar() or 0

    # Активные сервисы
    result = await db.execute(
        select(func.count())
        .select_from(Service)
        .where(and_(Service.is_active, ~Service.is_blocked))
    )
    active_services = result.scalar() or 0

    return {
        "total_users": users_count or 0,
        "total_services": services_count,
        "active_services": active_services,
        "tasks_by_status": tasks_by_status,
        "total_tasks": sum(tasks_by_status.values()),
        "recent_logs": [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message[:100] + "..."
                if len(log.message) > 100
                else log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in recent_logs
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/tasks/status/{status}", tags=["Tasks Custom"])
async def get_tasks_by_status(
    status: str,
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    if status not in ["pending", "running", "completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status...")

    result = await task_crud.get_multi(
        db=db,
        status=status,
        offset=skip,
        limit=limit,
        sort_columns=["created_at"],
        sort_orders=["desc"],
    )
    # 🔥 Возвращаем только список, чтобы соответствовать ожиданиям тестов
    return result["data"]  # или просто result, если тесты адаптировать


# ============================================================================
# Здоровье приложения
# ============================================================================
@app.get("/health", tags=["Health"])
async def health_check(db: DbDep):
    """
    Проверка здоровья приложения и подключения к БД
    """
    health_info = {
        "status": "ok",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {},
    }

    # Проверка БД
    try:
        start_time = datetime.now(timezone.utc)
        result = await db.execute(text("SELECT 1"))
        result.first()
        response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        health_info["database"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "type": "PostgreSQL",
        }
    except Exception as e:
        health_info["database"] = {"status": "unhealthy", "error": str(e)}
        health_info["status"] = "degraded"

    return health_info


@app.get("/")
async def root():
    return {
        "message": "Task Service API",
        "version": app.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
