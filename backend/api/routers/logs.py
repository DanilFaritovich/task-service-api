"""
Роутеры для работы с логами
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.database.crud import get_logs, create_log
from backend.database.schemas import Log, LogCreate, LogLevel
from backend.api.dependencies import get_db

router = APIRouter(
    prefix="/logs",
    tags=["logs"]
)

@router.get("/", response_model=List[Log])
async def read_logs(
    service_id: Optional[int] = Query(None),
    task_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    level: Optional[LogLevel] = Query(None),
    hours: int = Query(24, ge=1, le=720),  # Максимум 30 дней
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Получить логи с фильтрацией"""
    logs = await get_logs(
        db,
        service_id=service_id,
        task_id=task_id,
        user_id=user_id,
        level=level.value if level else None,
        hours=hours,
        skip=skip,
        limit=limit
    )
    return logs

@router.post("/", response_model=Log, status_code=201)
async def create_new_log(log: LogCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую запись в логе"""
    return await create_log(
        db,
        message=log.message,
        level=log.level.value,
        service_id=log.service_id,
        task_id=log.task_id,
        user_id=log.user_id,
        context_data=log.context_data
    )