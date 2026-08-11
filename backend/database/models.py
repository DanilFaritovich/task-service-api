from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    desc,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.database.base import Base


class Service(Base):
    """Модель доступных сервисов"""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_default_config_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, server_default="{}"
    )
    system_default_config_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, server_default="{}"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    is_blocked: Mapped[bool] = mapped_column(Boolean, server_default="false")
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, server_default="1")
    timeout_seconds: Mapped[int] = mapped_column(Integer, server_default="300")
    created_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user_services: Mapped[list["UserService"]] = relationship(
        "UserService", back_populates="service", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="service", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_services_active_blocked", "is_active", "is_blocked"),)


class User(Base):
    """Модель пользователей"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user_services: Mapped[list["UserService"]] = relationship(
        "UserService", back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )
    logs: Mapped[list["Log"]] = relationship(
        "Log", back_populates="user", cascade="all, delete-orphan"
    )


class UserService(Base):
    """Конфигурации пользователей для сервисов"""

    __tablename__ = "user_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    config_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user: Mapped["User"] = relationship("User", back_populates="user_services")
    service: Mapped["Service"] = relationship("Service", back_populates="user_services")

    __table_args__ = (
        UniqueConstraint("user_id", "service_id", name="uq_user_service"),
        Index("idx_user_services_user_id", "user_id"),
        Index("idx_user_services_service_id", "service_id"),
        Index("idx_user_services_enabled", "is_enabled"),
    )


class Task(Base):
    """Задачи пользователей"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    service: Mapped["Service"] = relationship("Service", back_populates="tasks")
    task_files: Mapped[list["TaskFile"]] = relationship(
        "TaskFile", back_populates="task", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="check_task_status",
        ),
        Index("idx_tasks_user_id", "user_id"),
        Index("idx_tasks_service_id", "service_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_created_at", "created_at"),
    )


class TaskFile(Base):
    """Файлы задач"""

    __tablename__ = "task_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.current_timestamp()
    )

    task: Mapped["Task"] = relationship("Task", back_populates="task_files")

    __table_args__ = (Index("idx_task_files_task_id", "task_id"),)


class Log(Base):
    """Логи"""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="NO ACTION"), nullable=False
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[Optional[Any]] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="logs")

    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="check_log_level",
        ),
        Index("idx_logs_user_id", "user_id"),
        Index("idx_logs_source_timestamp", "source", desc("timestamp")),
    )
