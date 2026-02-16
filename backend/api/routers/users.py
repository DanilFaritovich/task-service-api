"""
Роутеры для работы с пользователями
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.database.crud import (
    get_users, get_user, get_user_by_tg_id,
    create_user, update_user, delete_user,
    get_user_active_services
)
from backend.database.schemas import (
    User, UserCreate, UserUpdate,
    Service
)
from backend.api.dependencies import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/", response_model=List[User])
async def read_users(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех пользователей"""
    users = await get_users(db, skip=skip, limit=limit)
    return users


@router.get("/tg/{tg_id}", response_model=User)
async def read_user_by_tg_id(tg_id: int, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по Telegram ID"""
    user = await get_user_by_tg_id(db, tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по ID"""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/services", response_model=List[Service])
async def read_user_services(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить активные сервисы пользователя"""
    services = await get_user_active_services(db, user_id)
    return services


@router.post("/", response_model=User, status_code=201)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверка на уникальность tg_id
    existing = await get_user_by_tg_id(db, user.tg_id)
    if existing:
        raise HTTPException(status_code=400, detail="User with this tg_id already exists")

    return await create_user(db, user.tg_id, user.username)


@router.put("/{user_id}", response_model=User)
async def update_existing_user(
        user_id: int,
        user: UserUpdate,
        db: AsyncSession = Depends(get_db)
):
    """Обновить пользователя"""
    updated = await update_user(
        db,
        user_id,
        username=user.username,
        is_active=user.is_active
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/{user_id}", status_code=204)
async def delete_existing_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить пользователя"""
    if not await delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return None