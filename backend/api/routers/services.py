"""
Роутеры для работы с сервисами
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.database.crud import (
    get_services, get_service, create_service, update_service,
    delete_service, block_service, unblock_service,
    get_service_config_schema, get_service_by_name
)
from backend.database.schemas import (
    Service, ServiceCreate, ServiceUpdate,
    ServiceConfigSchema
)
from backend.api.dependencies import get_db

router = APIRouter(
    prefix="/services",
    tags=["services"]
)


@router.get("/", response_model=List[Service])
async def read_services(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        only_active: bool = False,
        only_available: bool = False,
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех сервисов"""
    services = await get_services(
        db,
        skip=skip,
        limit=limit,
        only_active=only_active,
        only_available=only_available
    )
    return services


@router.get("/{service_id}", response_model=Service)
async def read_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Получить сервис по ID"""
    service = await get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/", response_model=Service, status_code=201)
async def create_new_service(service: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый сервис"""
    # Проверка на уникальность имени
    existing = await get_service_by_name(db, service.name)
    if existing:
        raise HTTPException(status_code=400, detail="Service with this name already exists")

    return await create_service(db, **service.model_dump())


@router.put("/{service_id}", response_model=Service)
async def update_existing_service(
        service_id: int,
        service: ServiceUpdate,
        db: AsyncSession = Depends(get_db)
):
    """Обновить сервис"""
    updated = await update_service(db, service_id, **service.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated


@router.delete("/{service_id}", status_code=204)
async def delete_existing_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить сервис"""
    if not await delete_service(db, service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return None


@router.post("/{service_id}/block", response_model=Service)
async def block_service_endpoint(service_id: int, db: AsyncSession = Depends(get_db)):
    """Заблокировать сервис"""
    service = await block_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/{service_id}/unblock", response_model=Service)
async def unblock_service_endpoint(service_id: int, db: AsyncSession = Depends(get_db)):
    """Разблокировать сервис"""
    service = await unblock_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.get("/{service_name}/config", response_model=List[ServiceConfigSchema])
async def get_service_config(service_name: str, db: AsyncSession = Depends(get_db)):
    """Получить схему конфигурации для сервиса"""
    config = await get_service_config_schema(db, service_name)
    if not config:
        raise HTTPException(status_code=404, detail="Service not found or has no config fields")
    return config