"""
Модели SQLAlchemy для асинхронной работы
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, JSON, BIGINT, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from .connection import Base
from typing import List, Optional


# ============================================================================
# Модель: Сервисы
# ============================================================================
class Service(Base, AsyncAttrs):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    max_concurrent_tasks = Column(Integer, default=1, nullable=False)
    timeout_seconds = Column(Integer, default=300, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    config_fields = relationship(
        "ServiceConfigField",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    user_services = relationship(
        "UserService",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "Log",
        back_populates="service"
    )

    def is_available(self) -> bool:
        """Проверить, доступен ли сервис"""
        return self.is_active and not self.is_blocked

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}')>"


# ============================================================================
# Модель: Поля конфигурации сервисов
# ============================================================================
class ServiceConfigField(Base, AsyncAttrs):
    __tablename__ = "service_config_fields"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(100), nullable=False)
    name_ru = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    value_type = Column(String(20), nullable=False)
    default_value = Column(JSON)
    is_required = Column(Boolean, default=False, nullable=False)
    options = Column(JSON)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            value_type.in_(['string', 'integer', 'boolean', 'float', 'array', 'json', 'enum']),
            name='check_value_type'
        ),
    )

    # Relationships
    service = relationship("Service", back_populates="config_fields")

    def __repr__(self):
        return f"<ServiceConfigField(id={self.id}, code='{self.code}')>"


# ============================================================================
# Модель: Пользователи
# ============================================================================
class User(Base, AsyncAttrs):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user_services = relationship(
        "UserService",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "Log",
        back_populates="user"
    )

    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id}, username='{self.username}')>"


# ============================================================================
# Модель: Конфигурации пользователей для сервисов
# ============================================================================
class UserService(Base, AsyncAttrs):
    __tablename__ = "user_services"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    config_data = Column(JSON)
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_services")
    service = relationship("Service", back_populates="user_services")

    def __repr__(self):
        return f"<UserService(id={self.id}, user_id={self.user_id}, service_id={self.service_id})>"


# ============================================================================
# Модель: Задачи
# ============================================================================
class Task(Base, AsyncAttrs):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text)
    result_data = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'running', 'completed', 'failed', 'cancelled']),
            name='check_status'
        ),
    )

    # Relationships
    user = relationship("User", back_populates="tasks")
    service = relationship("Service", back_populates="tasks")
    files = relationship(
        "TaskFile",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "Log",
        back_populates="task"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, status='{self.status}')>"


# ============================================================================
# Модель: Файлы задач
# ============================================================================
class TaskFile(Base, AsyncAttrs):
    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_size = Column(BIGINT)
    file_hash = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="files")

    def __repr__(self):
        return f"<TaskFile(id={self.id}, file_path='{self.file_path}')>"


# ============================================================================
# Модель: Логи
# ============================================================================
class Log(Base, AsyncAttrs):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    message = Column(Text, nullable=False)
    level = Column(String(50), nullable=False, index=True)
    context_data = Column(JSON)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            level.in_(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
            name='check_log_level'
        ),
    )

    # Relationships
    service = relationship("Service", back_populates="logs")
    task = relationship("Task", back_populates="logs")
    user = relationship("User", back_populates="logs")

    def __repr__(self):
        return f"<Log(id={self.id}, level='{self.level}')>"