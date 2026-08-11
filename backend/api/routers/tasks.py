from fastapi import APIRouter, HTTPException, Query
from fastcrud import FastCRUD, UpdateConfig, crud_router

from backend.api.deps import DbDep, get_db
from backend.database.models import Task
from backend.database.schemas import TaskCreate, TaskResponse, TaskUpdate
from backend.api.services.tasks_service import TasksService

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
        auto_fields={},
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
    return await TasksService(db).get_tasks_by_status(status, skip, limit)
