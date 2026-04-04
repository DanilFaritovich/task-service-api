from fastapi import APIRouter, HTTPException, Query
from fastcrud import FastCRUD, UpdateConfig, crud_router

from backend.api.deps import DbDep, get_db
from backend.database.models import Task
from backend.database.schemas import TaskCreate, TaskResponse, TaskUpdate

task_crud = FastCRUD(Task)

router = crud_router(
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

custom_router = APIRouter(prefix="/tasks", tags=["Tasks"])


@custom_router.get("/status/{status}", tags=["Tasks"])
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
