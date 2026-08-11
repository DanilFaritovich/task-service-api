from fastapi import APIRouter
from fastcrud import UpdateConfig, crud_router

from backend.api.deps import DbDep, get_db
from backend.database.models import User
from backend.database.schemas import UserCreate, UserResponse, UserUpdate
from backend.api.services.users_service import UsersService

router = crud_router(
    session=get_db,
    model=User,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    select_schema=UserResponse,
    path="/users",
    tags=["Users"],
    include_relationships=False,
    update_config=UpdateConfig(
        auto_fields={},
        exclude_from_schema=["created_at", "updated_at"],
    ),
)

custom_router = APIRouter(prefix="/users", tags=["Users"])

@custom_router.get("/tg/{tg_id}", tags=["Users"], response_model=UserResponse)
async def get_user_by_tg_id(
    tg_id: int,
    db: DbDep,
):
    """
    Получение одного пользователя по Telegram ID
    """
    return await UsersService(db).get_user_by_tg_id(tg_id)
