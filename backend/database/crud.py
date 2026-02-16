"""
Асинхронные CRUD операции для работы с БД
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .models import (
    User, Service, ServiceConfigField, UserService,
    Task, TaskFile, Log
)
from .schemas import TaskStatus, LogLevel

# ============================================================================
# CRUD для пользователей
# ============================================================================

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_by_tg_id(db: AsyncSession, tg_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    result = await db.execute(
        select(User).where(User.tg_id == tg_id)
    )
    return result.scalar_one_or_none()

async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Получить всех пользователей"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def create_user(
    db: AsyncSession,
    tg_id: int,
    username: str
) -> User:
    """Создать пользователя"""
    db_user = User(tg_id=tg_id, username=username)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(
    db: AsyncSession,
    user_id: int,
    username: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[User]:
    """Обновить пользователя"""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    if username is not None:
        db_user.username = username
    if is_active is not None:
        db_user.is_active = is_active

    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Удалить пользователя"""
    db_user = await get_user(db, user_id)
    if not db_user:
        return False

    await db.delete(db_user)
    await db.commit()
    return True

# ============================================================================
# CRUD для сервисов
# ============================================================================

async def get_service(db: AsyncSession, service_id: int) -> Optional[Service]:
    """Получить сервис по ID"""
    result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    return result.scalar_one_or_none()

async def get_service_by_name(db: AsyncSession, name: str) -> Optional[Service]:
    """Получить сервис по имени"""
    result = await db.execute(
        select(Service).where(Service.name == name)
    )
    return result.scalar_one_or_none()

async def get_services(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    only_active: bool = False,
    only_available: bool = False
) -> List[Service]:
    """Получить все сервисы"""
    query = select(Service)

    if only_active:
        query = query.where(Service.is_active == True)

    if only_available:
        query = query.where(
            Service.is_active == True,
            Service.is_blocked == False
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_service(
    db: AsyncSession,
    name: str,
    display_name: str,
    description: Optional[str] = None,
    is_active: bool = True,
    is_blocked: bool = False,
    max_concurrent_tasks: int = 1,
    timeout_seconds: int = 300
) -> Service:
    """Создать новый сервис"""
    db_service = Service(
        name=name,
        display_name=display_name,
        description=description,
        is_active=is_active,
        is_blocked=is_blocked,
        max_concurrent_tasks=max_concurrent_tasks,
        timeout_seconds=timeout_seconds
    )
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service

async def update_service(
    db: AsyncSession,
    service_id: int,
    **kwargs
) -> Optional[Service]:
    """Обновить сервис"""
    db_service = await get_service(db, service_id)
    if not db_service:
        return None

    for key, value in kwargs.items():
        if hasattr(db_service, key):
            setattr(db_service, key, value)

    await db.commit()
    await db.refresh(db_service)
    return db_service

async def delete_service(db: AsyncSession, service_id: int) -> bool:
    """Удалить сервис"""
    db_service = await get_service(db, service_id)
    if not db_service:
        return False

    await db.delete(db_service)
    await db.commit()
    return True

async def block_service(db: AsyncSession, service_id: int) -> Optional[Service]:
    """Заблокировать сервис"""
    return await update_service(db, service_id, is_blocked=True)

async def unblock_service(db: AsyncSession, service_id: int) -> Optional[Service]:
    """Разблокировать сервис"""
    return await update_service(db, service_id, is_blocked=False)

# ============================================================================
# CRUD для полей конфигурации
# ============================================================================

async def get_config_fields_by_service(
    db: AsyncSession,
    service_id: int,
    only_active: bool = True
) -> List[ServiceConfigField]:
    """Получить все поля конфигурации для сервиса"""
    query = select(ServiceConfigField).where(
        ServiceConfigField.service_id == service_id
    )

    if only_active:
        query = query.where(ServiceConfigField.is_active == True)

    result = await db.execute(query.order_by(ServiceConfigField.sort_order))
    return list(result.scalars().all())

async def get_service_config_schema(
    db: AsyncSession,
    service_name: str
) -> List[Dict[str, Any]]:
    """Получить схему конфигурации сервиса"""
    service = await get_service_by_name(db, service_name)
    if not service:
        return []

    fields = await get_config_fields_by_service(db, service.id)

    return [
        {
            "code": field.code,
            "name_ru": field.name_ru,
            "name_en": field.name_en,
            "value_type": field.value_type,
            "default_value": field.default_value,
            "is_required": field.is_required,
            "options": field.options,
            "sort_order": field.sort_order
        }
        for field in fields
    ]

# ============================================================================
# CRUD для конфигураций пользователей
# ============================================================================

async def get_user_service_config(
    db: AsyncSession,
    user_id: int,
    service_id: int
) -> Optional[UserService]:
    """Получить конфигурацию пользователя для сервиса"""
    result = await db.execute(
        select(UserService).where(
            UserService.user_id == user_id,
            UserService.service_id == service_id
        )
    )
    return result.scalar_one_or_none()

async def create_or_update_user_service_config(
    db: AsyncSession,
    user_id: int,
    service_id: int,
    config_data: Optional[Dict[str, Any]] = None,
    is_enabled: bool = True
) -> UserService:
    """Создать или обновить конфигурацию пользователя для сервиса"""
    db_config = await get_user_service_config(db, user_id, service_id)

    if db_config:
        if config_data is not None:
            db_config.config_data = config_data
        db_config.is_enabled = is_enabled
    else:
        db_config = UserService(
            user_id=user_id,
            service_id=service_id,
            config_data=config_data,
            is_enabled=is_enabled
        )
        db.add(db_config)

    await db.commit()
    await db.refresh(db_config)
    return db_config

async def get_user_active_services(
    db: AsyncSession,
    user_id: int
) -> List[Service]:
    """Получить все активные сервисы для пользователя"""
    result = await db.execute(
        select(Service)
        .join(UserService, Service.id == UserService.service_id)
        .where(
            UserService.user_id == user_id,
            UserService.is_enabled == True,
            Service.is_active == True,
            Service.is_blocked == False
        )
    )
    return list(result.scalars().all())

# ============================================================================
# CRUD для задач
# ============================================================================

async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Получить задачу по ID"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()

async def get_tasks(
    db: AsyncSession,
    user_id: Optional[int] = None,
    service_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Task]:
    """Получить задачи с фильтрацией"""
    query = select(Task)

    if user_id:
        query = query.where(Task.user_id == user_id)

    if service_id:
        query = query.where(Task.service_id == service_id)

    if status:
        query = query.where(Task.status == status.value)

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_task(
    db: AsyncSession,
    user_id: int,
    service_id: int,
    task_name: str,
    status: TaskStatus = TaskStatus.PENDING
) -> Task:
    """Создать новую задачу"""
    db_task = Task(
        user_id=user_id,
        service_id=service_id,
        task_name=task_name,
        status=status.value
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def update_task(
    db: AsyncSession,
    task_id: int,
    status: Optional[TaskStatus] = None,
    error_message: Optional[str] = None,
    result_data: Optional[Dict[str, Any]] = None
) -> Optional[Task]:
    """Обновить задачу"""
    db_task = await get_task(db, task_id)
    if not db_task:
        return None

    if status:
        db_task.status = status.value

    if error_message is not None:
        db_task.error_message = error_message

    if result_data is not None:
        db_task.result_data = result_data

    await db.commit()
    await db.refresh(db_task)
    return db_task

async def get_running_tasks_count(db: AsyncSession, service_id: int) -> int:
    """Получить количество запущенных задач для сервиса"""
    result = await db.execute(
        select(func.count()).select_from(Task).where(
            Task.service_id == service_id,
            Task.status == TaskStatus.RUNNING.value
        )
    )
    return result.scalar_one() or 0

# ============================================================================
# CRUD для файлов задач
# ============================================================================

async def create_task_file(
    db: AsyncSession,
    task_id: int,
    file_path: str,
    file_size: Optional[int] = None,
    file_hash: Optional[str] = None
) -> TaskFile:
    """Добавить файл к задаче"""
    db_file = TaskFile(
        task_id=task_id,
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file

async def get_task_files(db: AsyncSession, task_id: int) -> List[TaskFile]:
    """Получить все файлы задачи"""
    result = await db.execute(
        select(TaskFile).where(TaskFile.task_id == task_id)
    )
    return list(result.scalars().all())

# ============================================================================
# CRUD для логов
# ============================================================================

async def create_log(
    db: AsyncSession,
    message: str,
    level: str,
    service_id: Optional[int] = None,
    task_id: Optional[int] = None,
    user_id: Optional[int] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> Log:
    """Создать запись в логе"""
    db_log = Log(
        service_id=service_id,
        task_id=task_id,
        user_id=user_id,
        message=message,
        level=level,
        context_data=context_data
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

async def get_logs(
    db: AsyncSession,
    service_id: Optional[int] = None,
    task_id: Optional[int] = None,
    user_id: Optional[int] = None,
    level: Optional[str] = None,
    hours: int = 24,
    skip: int = 0,
    limit: int = 100
) -> List[Log]:
    """Получить логи с фильтрацией"""
    query = select(Log).where(
        Log.timestamp >= func.now() - timedelta(hours=hours)
    )

    if service_id:
        query = query.where(Log.service_id == service_id)

    if task_id:
        query = query.where(Log.task_id == task_id)

    if user_id:
        query = query.where(Log.user_id == user_id)

    if level:
        query = query.where(Log.level == level)

    result = await db.execute(
        query.order_by(Log.timestamp.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())