"""
Pydantic схемы для валидации данных
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enum для статусов и уровней
# ============================================================================
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ConfigValueType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    ARRAY = "array"
    JSON = "json"
    ENUM = "enum"


# ============================================================================
# Схемы для пользователей
# ============================================================================
class UserBase(BaseModel):
    tg_id: int = Field(..., description="Telegram ID пользователя")
    username: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для сервисов
# ============================================================================
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    is_blocked: bool = False
    max_concurrent_tasks: int = Field(1, ge=1)
    timeout_seconds: int = Field(300, ge=1)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1)
    timeout_seconds: Optional[int] = Field(None, ge=1)


class Service(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для полей конфигурации
# ============================================================================
class ServiceConfigFieldBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name_ru: str = Field(..., min_length=1, max_length=255)
    name_en: str = Field(..., min_length=1, max_length=255)
    value_type: ConfigValueType
    default_value: Optional[Any] = None
    is_required: bool = False
    options: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    is_active: bool = True


class ServiceConfigFieldCreate(ServiceConfigFieldBase):
    pass


class ServiceConfigFieldUpdate(BaseModel):
    name_ru: Optional[str] = Field(None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, min_length=1, max_length=255)
    default_value: Optional[Any] = None
    is_required: Optional[bool] = None
    options: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceConfigField(ServiceConfigFieldBase):
    id: int
    service_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для конфигураций пользователей
# ============================================================================
class UserServiceBase(BaseModel):
    config_data: Optional[Dict[str, Any]] = None
    is_enabled: bool = True


class UserServiceCreate(UserServiceBase):
    user_id: int
    service_id: int


class UserServiceUpdate(BaseModel):
    config_data: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class UserService(UserServiceBase):
    id: int
    user_id: int
    service_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для задач
# ============================================================================
class TaskBase(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=255)
    status: TaskStatus = TaskStatus.PENDING


class TaskCreate(TaskBase):
    user_id: int
    service_id: int


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class Task(TaskBase):
    id: int
    user_id: int
    service_id: int
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для файлов задач
# ============================================================================
class TaskFileBase(BaseModel):
    file_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None


class TaskFileCreate(TaskFileBase):
    task_id: int


class TaskFile(TaskFileBase):
    id: int
    task_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для логов
# ============================================================================
class LogBase(BaseModel):
    message: str
    level: LogLevel
    context_data: Optional[Dict[str, Any]] = None


class LogCreate(LogBase):
    service_id: Optional[int] = None
    task_id: Optional[int] = None
    user_id: Optional[int] = None


class Log(LogBase):
    id: int
    service_id: Optional[int] = None
    task_id: Optional[int] = None
    user_id: Optional[int] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Схемы для ответов
# ============================================================================
class ServiceConfigSchema(BaseModel):
    """Схема конфигурации сервиса для фронтенда"""
    code: str
    name_ru: str
    name_en: str
    value_type: ConfigValueType
    default_value: Optional[Any] = None
    is_required: bool
    options: Optional[Dict[str, Any]] = None
    sort_order: int


class ServiceWithConfig(Service):
    config_fields: List[ServiceConfigSchema]


class UserWithServices(User):
    active_services: List[Service] = []


class TaskWithDetails(Task):
    service: Optional[Service] = None
    files: List[TaskFile] = []