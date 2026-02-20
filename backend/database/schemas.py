from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ========== Enums ==========
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


# ========== Базовые схемы ==========
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
    )


# ========== Service ==========
class ServiceBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    user_default_config_data: Dict[str, Any] = Field(default_factory=dict)
    system_default_config_data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_blocked: bool = False
    max_concurrent_tasks: int = Field(1, ge=1, le=100)
    timeout_seconds: int = Field(300, ge=1, le=86400)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    user_default_config_data: Optional[Dict[str, Any]] = None
    system_default_config_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=100)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=86400)


class ServiceResponse(ServiceBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ========== User ==========
class UserBase(BaseModel):
    tg_id: int = Field(..., ge=1)
    username: str = Field(..., max_length=255, min_length=1)
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tg_id: Optional[int] = Field(None, ge=1)
    username: Optional[str] = Field(None, max_length=255, min_length=1)
    is_active: Optional[bool] = None


class UserResponse(UserBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ========== UserService ==========
class UserServiceBase(BaseModel):
    user_id: int
    service_id: int
    config_data: Optional[Dict[str, Any]] = None
    is_enabled: bool = True


class UserServiceCreate(UserServiceBase):
    pass


class UserServiceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_data: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class UserServiceResponse(UserServiceBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ========== Task ==========
class TaskBase(BaseModel):
    user_id: int
    service_id: int
    task_name: str = Field(..., max_length=255, min_length=1)
    status: TaskStatus
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, TaskStatus):
            return v
        if isinstance(v, str):
            return TaskStatus(v)
        return v


class TaskCreate(BaseModel):
    user_id: int
    service_id: int
    task_name: str = Field(..., max_length=255, min_length=1)
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_name: Optional[str] = Field(None, max_length=255, min_length=1)
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ========== TaskFile ==========
class TaskFileBase(BaseModel):
    task_id: int
    file_path: str = Field(..., min_length=1, max_length=1024)
    file_size: Optional[int] = Field(None, ge=0)
    file_hash: Optional[str] = Field(None, max_length=255)


class TaskFileCreate(TaskFileBase):
    pass


class TaskFileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: Optional[str] = Field(None, max_length=1024)
    file_size: Optional[int] = Field(None, ge=0)
    file_hash: Optional[str] = Field(None, max_length=255)


class TaskFileResponse(TaskFileBase, BaseSchema):
    id: int
    created_at: datetime


# ========== Log ==========
class LogBase(BaseModel):
    user_id: int
    source: str = Field(..., max_length=255)
    message: str
    level: LogLevel
    context_data: Optional[Dict[str, Any]] = None


class LogCreate(LogBase):
    timestamp: Optional[datetime] = None


class LogUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    level: Optional[LogLevel] = None
    context_data: Optional[Dict[str, Any]] = None


class LogResponse(LogBase, BaseSchema):
    id: int
    timestamp: datetime
