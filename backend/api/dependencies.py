"""
Зависимости для FastAPI
"""
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.connection import get_db

async def get_db_session() -> AsyncSession:
    """
    Dependency для получения сессии БД
    """
    async for session in get_db():
        yield session
