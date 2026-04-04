from fastapi import APIRouter, HTTPException
from fastcrud import FastCRUD, UpdateConfig, crud_router

from backend.api.deps import DbDep, get_db
from backend.database.models import User
from backend.database.schemas import UserCreate, UserResponse, UserUpdate

user_crud = FastCRUD(User)

router = crud_router(
    session=get_db,
    model=User,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    select_schema=UserResponse,
    path="/users",
    tags=["Users"],
    include_relationships=False,  # СВЯЗИ ОТКЛЮЧЕНЫ
    update_config=UpdateConfig(
        auto_fields={},  # Provide appropriate auto field mappings if needed
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
    print(f"🔍 DB TYPE: {type(db)}")
    user = await user_crud.get(db=db, tg_id=tg_id)
    print(f"🔍 FASTCRUD RESULT: {user}")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # FastAPI автоматически сериализует модель SQLAlchemy в JSON
    # благодаря response_model=UserResponse (при from_attributes=True в схеме)
    return user
