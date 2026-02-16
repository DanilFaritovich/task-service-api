"""
Тесты для эндпоинтов логов
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Log, Service, Task, User


class TestLogs:
    """Тесты для операций с логами"""

    @pytest.mark.asyncio
    async def test_create_log(self, client: AsyncClient):
        """Тест создания записи в логе"""
        log_data = {
            "message": "Test log message",
            "level": "INFO",
            "context_data": {"key": "value"}
        }

        response = await client.post("/logs/", json=log_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Test log message"
        assert data["level"] == "INFO"
        assert data["context_data"]["key"] == "value"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_logs(self, client: AsyncClient):
        """Тест получения списка логов"""
        # Создаём несколько записей
        logs = [
            {"message": "Log 1", "level": "INFO"},
            {"message": "Log 2", "level": "ERROR"},
            {"message": "Log 3", "level": "WARNING"}
        ]

        for log in logs:
            await client.post("/logs/", json=log)

        response = await client.get("/logs/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_filter_logs_by_level(self, client: AsyncClient):
        """Тест фильтрации логов по уровню"""
        # Создаём логи разных уровней
        await client.post("/logs/", json={"message": "Info log", "level": "INFO"})
        await client.post("/logs/", json={"message": "Error log", "level": "ERROR"})
        await client.post("/logs/", json={"message": "Warning log", "level": "WARNING"})

        response = await client.get("/logs/?level=ERROR")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(log["level"] == "ERROR" for log in data)

    @pytest.mark.asyncio
    async def test_filter_logs_by_hours(self, client: AsyncClient):
        """Тест фильтрации логов по времени"""
        # Создаём лог
        await client.post("/logs/", json={"message": "Recent log", "level": "INFO"})

        # Получаем логи за последние 1 час
        response = await client.get("/logs/?hours=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_filter_logs_by_service(self, client: AsyncClient, sample_service: Service):
        """Тест фильтрации логов по сервису"""
        log_data = {
            "message": "Service log",
            "level": "INFO",
            "service_id": sample_service.id
        }

        await client.post("/logs/", json=log_data)

        response = await client.get(f"/logs/?service_id={sample_service.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["service_id"] == sample_service.id

    @pytest.mark.asyncio
    async def test_filter_logs_by_task(self, client: AsyncClient, sample_task: Task):
        """Тест фильтрации логов по задаче"""
        log_data = {
            "message": "Task log",
            "level": "INFO",
            "task_id": sample_task.id
        }

        await client.post("/logs/", json=log_data)

        response = await client.get(f"/logs/?task_id={sample_task.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["task_id"] == sample_task.id

    @pytest.mark.asyncio
    async def test_filter_logs_by_user(self, client: AsyncClient, sample_user: User):
        """Тест фильтрации логов по пользователю"""
        log_data = {
            "message": "User log",
            "level": "INFO",
            "user_id": sample_user.id
        }

        await client.post("/logs/", json=log_data)

        response = await client.get(f"/logs/?user_id={sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_id"] == sample_user.id

    @pytest.mark.asyncio
    async def test_combined_filters(self, client: AsyncClient, sample_service: Service):
        """Тест комбинированной фильтрации логов"""
        log_data = {
            "message": "Filtered log",
            "level": "ERROR",
            "service_id": sample_service.id
        }

        await client.post("/logs/", json=log_data)

        # Фильтруем по уровню И сервису
        response = await client.get(
            f"/logs/?level=ERROR&service_id={sample_service.id}&hours=24"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(
            log["level"] == "ERROR" and log["service_id"] == sample_service.id
            for log in data
        )