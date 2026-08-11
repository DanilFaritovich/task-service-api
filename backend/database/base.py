from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class DatabaseSettings(BaseSettings):
    """Настройки базы данных с использованием Pydantic Settings v2"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="password", alias="DB_PASSWORD")
    db_name: str = Field(default="mydatabase", alias="DB_NAME")

    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    @property
    def database_url(self) -> str:
        """Формирование URL для подключения к БД"""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                path=self.db_name,
            )
        )


settings = DatabaseSettings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_use_lifo=True,
    hide_parameters=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей с поддержкой новых фич SQLAlchemy 2.1"""

    __mapper_args__ = {
        "eager_defaults": True
    } 

    def __repr__(self) -> str:
        """Улучшенное представление для моделей"""
        cols = []
        for col in self.__table__.columns.keys():
            val = getattr(self, col)
            cols.append(f"{col}={val!r}")
        return f"{self.__class__.__name__}({', '.join(cols)})"
