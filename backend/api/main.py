import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastcrud import crud_router
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.api.deps import DbDep, db_session_middleware, get_db
from backend.api.routers.dashboard import router as dashboard_router
from backend.api.routers.tasks import custom_router as tasks_custom_router
from backend.api.routers.tasks import router as tasks_router
from backend.api.routers.users import custom_router as users_custom_router
from backend.api.routers.users import router as users_router
from backend.database.base import Base, engine, settings
from backend.database.models import Log, Service, TaskFile, UserService
from backend.database.schemas import (
    LogCreate,
    LogResponse,
    LogUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    TaskFileCreate,
    TaskFileResponse,
    TaskFileUpdate,
    UserServiceCreate,
    UserServiceResponse,
    UserServiceUpdate,
)
from backend.exceptions import (
    AccessDeniedError,
    BusinessException,
    BusinessValidationError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BUSINESS_EXCEPTION_STATUS_CODES = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ServiceUnavailableError: status.HTTP_400_BAD_REQUEST,
    AccessDeniedError: status.HTTP_403_FORBIDDEN,
    TooManyRequestsError: status.HTTP_429_TOO_MANY_REQUESTS,
    BusinessValidationError: status.HTTP_400_BAD_REQUEST,
    ConflictError: status.HTTP_409_CONFLICT,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    События жизненного цикла приложения
    """
    logger.info("🚀 Starting up Application...")

    db_url = str(settings.database_url)
    if hasattr(settings, "db_password") and settings.db_password:
        db_url = db_url.replace(settings.db_password, "******")
    logger.info(f"Database URL: {db_url}")

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Database connection successful: {version}")

            if settings.db_echo:
                logger.info("Creating database tables...")
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    yield

    logger.info("🛑 Shutting down Application...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


app = FastAPI(
    title="Task Service API",
    description="API для управления сервисами, задачами и пользователями",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("TESTING_MODE") != "true":
    app.middleware("http")(db_session_middleware)

@app.exception_handler(BusinessException)
async def business_exception_handler(
    request: Request,
    exc: BusinessException,
) -> JSONResponse:
    status_code = BUSINESS_EXCEPTION_STATUS_CODES.get(
        type(exc),
        status.HTTP_400_BAD_REQUEST,
    )

    logger.warning(
        "Business exception: %s (status=%s, path=%s)",
        exc.__class__.__name__,
        status_code,
        request.url.path,
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    error_code = getattr(exc.orig, "sqlstate", None)

    if error_code == "23505":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Resource already exists"},
        )

    if error_code == "23503":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Referenced resource does not exist"},
        )

    if error_code == "23502":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Required field is missing"},
        )

    if error_code == "23514":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Database constraint violated"},
        )

    logger.error(
        "Unhandled database integrity error",
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity error"},
    )

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
        },
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
        include_relationships=False,
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
app.include_router(users_router)
app.include_router(users_custom_router)

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
        include_relationships=False,
    )
)

# 4. Tasks - только базовые операции
app.include_router(tasks_router)
app.include_router(tasks_custom_router)

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
        include_relationships=False,
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
        include_relationships=False,
    )
)


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ
# ============================================================================

# Создаем CRUD объекты для кастомных операций

app.include_router(dashboard_router)


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
