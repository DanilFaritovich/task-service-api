"""
Роутеры для работы с задачами
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.database.crud import (
    get_tasks, get_task, create_task, update_task,
    get_task_files, create_task_file,
    get_running_tasks_count
)
from backend.database.schemas import (
    Task, TaskCreate, TaskUpdate,
    TaskWithDetails, TaskFile, TaskFileCreate,
    TaskStatus
)
from backend.api.dependencies import get_db

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=List[Task])
async def read_tasks(
        user_id: Optional[int] = Query(None),
        service_id: Optional[int] = Query(None),
        status: Optional[TaskStatus] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: AsyncSession = Depends(get_db)
):
    """Получить список задач с фильтрацией"""
    tasks = await get_tasks(
        db,
        user_id=user_id,
        service_id=service_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return tasks


@router.get("/{task_id}", response_model=TaskWithDetails)
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Получить задачу по ID со всеми деталями"""
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Получаем файлы задачи
    files = await get_task_files(db, task_id)

    # Формируем ответ
    return TaskWithDetails(
        id=task.id,
        user_id=task.user_id,
        service_id=task.service_id,
        task_name=task.task_name,
        status=TaskStatus(task.status),
        error_message=task.error_message,
        result_data=task.result_data,
        created_at=task.created_at,
        updated_at=task.updated_at,
        service=task.service,
        files=[TaskFile.model_validate(file) for file in files]
    )


@router.post("/", response_model=Task, status_code=201)
async def create_new_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую задачу"""
    return await create_task(
        db,
        user_id=task.user_id,
        service_id=task.service_id,
        task_name=task.task_name,
        status=task.status
    )


@router.put("/{task_id}", response_model=Task)
async def update_existing_task(
        task_id: int,
        task: TaskUpdate,
        db: AsyncSession = Depends(get_db)
):
    """Обновить задачу (статус, ошибки, результат)"""
    updated = await update_task(
        db,
        task_id,
        status=task.status,
        error_message=task.error_message,
        result_data=task.result_data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.get("/{task_id}/files", response_model=List[TaskFile])
async def read_task_files(task_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все файлы задачи"""
    files = await get_task_files(db, task_id)
    return files


@router.post("/{task_id}/files", response_model=TaskFile, status_code=201)
async def create_task_file_endpoint(
        task_id: int,
        file: TaskFileCreate,
        db: AsyncSession = Depends(get_db)
):
    """Добавить файл к задаче"""
    return await create_task_file(
        db,
        task_id=task_id,
        file_path=file.file_path,
        file_size=file.file_size,
        file_hash=file.file_hash
    )


@router.get("/running/count/{service_id}")
async def get_running_count(service_id: int, db: AsyncSession = Depends(get_db)):
    """Получить количество запущенных задач для сервиса"""
    count = await get_running_tasks_count(db, service_id)
    return {"service_id": service_id, "running_tasks_count": count}