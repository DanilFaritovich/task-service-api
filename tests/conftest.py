"""
Конфигурация тестов — полностью асинхронный подход
"""
import sys
import os
from pathlib import Path
import asyncio
import pytest
from typing import AsyncGenerator
from dotenv import load_dotenv

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Загружаем переменные окружения
load_dotenv(dotenv_path=PROJECT_ROOT / ".env.test")

from backend.database.models import Base, Service, User, Task
from backend.api.main import app
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
import asyncpg
import httpx

# Настройки БД
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "app_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "app_db")

TEST_DB_NAME = f"test_{DB_NAME}"
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

print(f"🔧 Тестовая БД: {TEST_DB_NAME}")

# Глобальный флаг для создания БД один раз
_test_db_created = False

@pytest.fixture(scope="session")
def event_loop():
    """Единый цикл событий для всей сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database(event_loop):
    """
    Создаём тестовую БД один раз для всей сессии тестов
    Используем синхронный подход через asyncio.run() для избежания проблем с циклами
    """
    global _test_db_created
    if _test_db_created:
        return

    print(f"\n🚀 Создание тестовой БД: {TEST_DB_NAME}")

    # Создаём БД через отдельный асинхронный вызов
    async def _create_db():
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )

        # Завершаем подключения к тестовой БД
        try:
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = $1
            """, TEST_DB_NAME)
        except:
            pass

        # Удаляем и создаём БД
        await conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        await conn.execute(f"CREATE DATABASE {TEST_DB_NAME}")
        await conn.close()

        # Создаём таблицы
        engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    await _create_db()
    _test_db_created = True
    yield

    # Очистка после всех тестов
    async def _drop_db():
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        try:
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = $1
            """, TEST_DB_NAME)
        except:
            pass
        await conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        await conn.close()

    await _drop_db()
    print(f"\n✅ Тестовая БД удалена: {TEST_DB_NAME}")

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная сессия с откатом транзакции после каждого теста
    """
    # Создаём новый движок для каждой сессии (избегаем проблем с циклами)
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.connect() as conn:
        async with conn.begin() as transaction:
            session = async_session(bind=conn)
            yield session
            await transaction.rollback()
            await session.close()

    # Закрываем движок после теста
    await engine.dispose()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Асинхронный тестовый клиент"""
    # Переопределяем зависимость
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Используем ASGITransport для новых версий httpx
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

# Импортируем зависимости ПОСЛЕ настройки путей
from backend.database.connection import get_db

@pytest.fixture(scope="function")
async def sample_service(db_session: AsyncSession) -> Service:
    """Тестовый сервис"""
    service = Service(
        name="test_service",
        display_name="Test Service",
        description="Test description",
        is_active=True,
        is_blocked=False,
        max_concurrent_tasks=5,
        timeout_seconds=300
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service

@pytest.fixture(scope="function")
async def sample_user(db_session: AsyncSession) -> User:
    """Тестовый пользователь"""
    user = User(
        tg_id=123456789,
        username="test_user",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
async def sample_task(
    db_session: AsyncSession,
    sample_user: User,
    sample_service: Service
) -> Task:
    """Тестовая задача"""
    task = Task(
        user_id=sample_user.id,
        service_id=sample_service.id,
        task_name="Test Task",
        status="pending"
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task