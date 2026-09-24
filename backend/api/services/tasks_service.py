from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Task
from backend.exceptions import BusinessValidationError

class TasksService:
    """Бизнес-логика работы с задачами"""

    VALID_STATUSES = (
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
    )

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_crud = FastCRUD(Task)

    async def get_tasks_by_status(
        self, 
        task_status: str, 
        skip: int, 
        limit: int
    ) -> list[dict]:
        """Получение задач по статусу"""
        
        if task_status not in self.VALID_STATUSES:
            raise BusinessValidationError(
                f"Invalid task status: '{task_status}'. "
                f"Allowed values: {', '.join(self.VALID_STATUSES)}"
            )
        
        result = await self.task_crud.get_multi(
            db=self.db,
            status=task_status,
            offset=skip,
            limit=limit,
            sort_columns=["created_at"],
            sort_orders=["desc"],
        )
        return result["data"]
    