from contextvars import ContextVar
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.base import AsyncSessionLocal

# ContextVar для хранения сессии в рамках запроса (новое в FastAPI + asyncio)
session_context: ContextVar[AsyncSession | None] = ContextVar(
    "session_context", default=None
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии базы данных с поддержкой контекста.
    Сессия автоматически закрывается после завершения запроса.
    """
    async with AsyncSessionLocal() as session:
        # Сохраняем сессию в контексте для возможного использования в других местах
        token = session_context.set(session)
        try:
            yield session
        finally:
            session_context.reset(token)
            await session.close()


# Функция для получения текущей сессии из контекста (полезно для middleware)
async def get_current_session() -> AsyncSession | None:
    return session_context.get()


# Тип для аннотации зависимостей
DbDep = Annotated[AsyncSession, Depends(get_db)]


# Middleware для добавления сессии в request.state
async def db_session_middleware(request: Request, call_next):
    """Middleware для автоматического управления сессией"""
    async with AsyncSessionLocal() as session:
        request.state.db = session
        token = session_context.set(session)
        try:
            response = await call_next(request)
            return response
        finally:
            session_context.reset(token)
