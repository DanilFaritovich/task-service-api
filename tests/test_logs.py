"""
Тесты для эндпоинтов логов
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Log, User


class TestLogs:
    """Тесты для операций с логами"""

    @pytest.mark.asyncio
    async def test_create_log(self, client: AsyncClient, sample_user: User):
        """Тест создания нового лога"""
        log_data = {
            "user_id": sample_user.id,
            "source": "task_processor",
            "message": "Task started successfully",
            "level": "INFO",
            "context_data": {"task_id": 123},
        }

        response = await client.post("/logs/", json=log_data)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == sample_user.id
        assert data["source"] == "task_processor"
        assert data["message"] == "Task started successfully"
        assert data["level"] == "INFO"
        assert data["context_data"] == {"task_id": 123}
        assert "id" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_logs(self, client: AsyncClient, sample_log: Log):
        """Тест получения списка логов"""
        response = await client.get("/logs/")

        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_log_by_id(self, client: AsyncClient, sample_log: Log):
        """Тест получения лога по ID"""
        response = await client.get(f"/logs/{sample_log.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_log.id
        assert data["user_id"] == sample_log.user_id
        assert data["message"] == sample_log.message

    @pytest.mark.asyncio
    async def test_get_log_not_found(self, client: AsyncClient):
        """Тест получения несуществующего лога"""
        response = await client.get("/logs/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_log_invalid_level(
        self, client: AsyncClient, sample_user: User
    ):
        """Тест создания лога с невалидным уровнем"""
        invalid_log = {
            "user_id": sample_user.id,
            "source": "invalid_logger",
            "message": "Invalid level test",
            "level": "INVALID_LEVEL",  # Невалидный уровень
        }

        response = await client.post("/logs/", json=invalid_log)

        assert response.status_code == 422
        assert "enum" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_log_invalid_user(self, client: AsyncClient):
        """Тест создания лога с несуществующим пользователем"""
        invalid_log = {
            "user_id": 999999,  # Несуществующий пользователь
            "source": "invalid_user_logger",
            "message": "Invalid user test",
            "level": "ERROR",
        }

        response = await client.post("/logs/", json=invalid_log)

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_log_not_allowed(self, client: AsyncClient, sample_log: Log):
        """Тест попытки обновления лога (должно быть запрещено)"""
        update_data = {"message": "Updated message"}

        response = await client.put(f"/logs/{sample_log.id}", json=update_data)

        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.asyncio
    async def test_delete_log_not_allowed(self, client: AsyncClient, sample_log: Log):
        """Тест попытки удаления лога (должно быть запрещено)"""
        response = await client.delete(f"/logs/{sample_log.id}")

        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.asyncio
    async def test_create_log_missing_required_fields(
        self, client: AsyncClient, sample_user: User
    ):
        """Тест создания лога с отсутствующими обязательными полями"""
        # Пропущено поле message
        invalid_log = {
            "user_id": sample_user.id,
            "source": "missing_field_logger",
            "level": "INFO",
        }

        response = await client.post("/logs/", json=invalid_log)

        assert response.status_code == 422
        assert "field required" in str(response.json()).lower()
