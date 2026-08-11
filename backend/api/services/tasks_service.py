from fastapi import HTTPException
from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Task

class TasksService:
    """Бизнес-логика работы с задачами"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_crud = FastCRUD(Task)

    async def get_tasks_by_status(
        self, 
        status: str, 
        skip: int, 
        limit: int
    ) -> list[dict]:
        """Получение задач по статусу"""
        
        if status not in ["pending", "running", "completed", "failed", "cancelled"]:
                raise HTTPException(status_code=400, detail="Invalid status...")
        
        result = await self.task_crud.get_multi(
            db=self.db,
            status=status,
            offset=skip,
            limit=limit,
            sort_columns=["created_at"],
            sort_orders=["desc"],
        )
        return result["data"]
    