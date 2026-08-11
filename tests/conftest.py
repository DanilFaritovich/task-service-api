"""
Фикстуры для тестов
"""

import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ["TESTING_MODE"] = "true"


from backend.api.deps import get_db, session_context
from backend.api.main import app
from backend.database.base import Base, settings

# =============================================================================
# БАЗА ДАННЫХ: ENGINE
# =============================================================================
@pytest.fixture(scope="session")
async def db_engine():
    """Создает движок БД один раз на все тесты"""
    db_url = str(settings.database_url)

    test_engine = create_async_engine(
        db_url,
        echo=False,
        poolclass=NullPool,
        future=True,
        connect_args={
            "server_settings": {"application_name": "test_app"},
            "timeout": 10,
        },
    )

    try:
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("✅ Подключение к БД успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы")

    yield test_engine
    await test_engine.dispose()


# =============================================================================
# БАЗА ДАННЫХ: СЕССИЯ (Исправленная версия)
# =============================================================================
@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создает сессию БД для одного теста.

    ИСПОЛЬЗУЕМ ПРОСТОЙ ПАТТЕРН:
    1. Очищаем таблицы в НАЧАЛЕ теста (TRUNCATE)
    2. Yield сессии
    3. Rollback в конце для подстраховки
    """
    async_session = async_sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
    )

    async with async_session() as session:
        try:
            # Очищаем таблицы перед тестом (в порядке: дочерние → родительские)
            await session.execute(
                text(
                    "TRUNCATE TABLE task_files, logs, tasks, user_services, services, users "
                    "RESTART IDENTITY CASCADE"
                )
            )
            await session.commit()

            # Устанавливаем сессию в ContextVar (как в оригинальном get_db)
            token = session_context.set(session)
            yield session
            session_context.reset(token)

        except Exception:
            await session.rollback()
            raise
        finally:
            await session.rollback()
            await session.close()


# =============================================================================
# HTTP CLIENT
# =============================================================================
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Создает асинхронный клиент для тестирования API"""

    original_overrides = app.dependency_overrides.copy()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            follow_redirects=True,
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides = original_overrides


# =============================================================================
# ФИКСТУРЫ ДАННЫХ (упрощённые)
# =============================================================================
@pytest.fixture
async def sample_service(db_session: AsyncSession):
    from backend.database.models import Service

    service = Service(
        name="test_service",
        display_name="Test Service",
        description="Test service description",
        is_active=True,
        is_blocked=False,
        max_concurrent_tasks=5,
        timeout_seconds=300,
    )
    db_session.add(service)
    await db_session.flush()
    await db_session.refresh(service)
    return service


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    from backend.database.models import User

    user = User(tg_id=100001, username="test_user")
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_task(db_session, sample_user, sample_service):
    from backend.database.models import Task

    task = Task(
        user_id=sample_user.id,
        service_id=sample_service.id,
        task_name="Test Task",
        status="pending",
    )
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


@pytest.fixture
async def sample_log(db_session, sample_user):
    from backend.database.models import Log

    log = Log(
        user_id=sample_user.id,
        source="test_logger",
        message="Test log message",
        level="INFO",
    )
    db_session.add(log)
    await db_session.flush()
    await db_session.refresh(log)
    return log


@pytest.fixture
async def sample_user_service(db_session, sample_user, sample_service):
    """Создает и возвращает тестовый экземпляр UserService."""
    from backend.database.models import UserService

    existing = await db_session.execute(
        select(UserService).where(
            UserService.user_id == sample_user.id,
            UserService.service_id == sample_service.id,
        )
    )
    if existing.scalars().first():
        await db_session.execute(
            delete(UserService).where(
                UserService.user_id == sample_user.id,
                UserService.service_id == sample_service.id,
            )
        )
        await db_session.commit()

    user_service = UserService(
        user_id=sample_user.id,
        service_id=sample_service.id,
        config_data={
            "api_key": "test_api_key",
            "endpoint": "https://test.example.com/api",
        },
        is_enabled=True,
    )
    db_session.add(user_service)
    await db_session.commit()
    await db_session.refresh(user_service)

    return user_service


@pytest.fixture
async def sample_task_file(db_session, sample_task):
    """Создает и возвращает тестовый экземпляр TaskFile."""
    from backend.database.models import TaskFile

    existing = await db_session.execute(
        select(TaskFile).where(
            TaskFile.task_id == sample_task.id,
            TaskFile.file_path
            == "/test/sample_file.txt",
        )
    )
    if existing.scalars().first():
        await db_session.execute(
            delete(TaskFile).where(
                TaskFile.task_id == sample_task.id,
                TaskFile.file_path == "/test/sample_file.txt",
            )
        )
        await db_session.commit()

    task_file = TaskFile(
        task_id=sample_task.id,
        file_path="/test/sample_file.txt",
        file_size=1024,
        file_hash="abc123def456",
    )
    db_session.add(task_file)
    await db_session.commit()
    await db_session.refresh(task_file)

    return task_file
