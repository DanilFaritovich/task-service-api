"""
Тесты для эндпоинтов сервисов (Services)
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Service


class TestServices:
    """Тесты для операций с сервисами"""

    @pytest.mark.asyncio
    async def test_create_service(self, client: AsyncClient):
        """Тест создания нового сервиса"""
        service_data = {
            "name": "new_service",
            "display_name": "New Service Display",
            "description": "Test description",
            "is_active": True,
            "is_blocked": False,
            "max_concurrent_tasks": 5,
            "timeout_seconds": 600,
        }

        response = await client.post("/services/", json=service_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new_service"
        assert data["display_name"] == "New Service Display"
        assert data["is_active"] is True
        assert data["max_concurrent_tasks"] == 5
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_services(self, client: AsyncClient, sample_service: Service):
        """Тест получения списка сервисов"""
        response = await client.get("/services/")

        assert response.status_code == 200
        data = response.json()
        # fastapi-crud-router обычно возвращает {"data": [...], "count": ...}
        assert "data" in data
        items = data["data"]
        assert isinstance(items, list)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_get_service_by_id(
        self, client: AsyncClient, sample_service: Service
    ):
        """Тест получения сервиса по ID"""
        response = await client.get(f"/services/{sample_service.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_service.id
        assert data["name"] == sample_service.name
        assert data["display_name"] == sample_service.display_name
        assert data["is_active"] == sample_service.is_active

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, client: AsyncClient):
        """Тест получения несуществующего сервиса"""
        response = await client.get("/services/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_service(self, client: AsyncClient, sample_service: Service):
        """Тест обновления сервиса"""
        update_data = {
            "display_name": "Updated Display Name",
            "is_active": False,
            "max_concurrent_tasks": 10,
        }

        response = await client.patch(
            f"/services/{sample_service.id}", json=update_data
        )

        assert response.status_code == 200

        # Проверяем, что изменения применились
        get_response = await client.get(f"/services/{sample_service.id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["display_name"] == "Updated Display Name"
        assert data["is_active"] is False
        assert data["max_concurrent_tasks"] == 10

    @pytest.mark.asyncio
    async def test_delete_service(self, client: AsyncClient, sample_service: Service):
        """Тест удаления сервиса"""
        response = await client.delete(f"/services/{sample_service.id}")

        assert response.status_code == 200

        # Проверяем, что сервис удалён
        response = await client.get(f"/services/{sample_service.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_service_duplicate_name(
        self, client: AsyncClient, sample_service: Service
    ):
        """Тест создания сервиса с дублирующим name"""
        duplicate_service = {
            "name": sample_service.name,  # Дублирующее имя (уникальное поле)
            "display_name": "Duplicate Service",
            "is_active": True,
        }

        response = await client.post("/services/", json=duplicate_service)

        # Ожидаем ошибку валидации или конфликта (зависит от реализации CRUD, обычно 422 или 400)
        assert response.status_code in [422, 400, 409]
        # Проверка на наличие сообщения об ошибке (уникальность)
        response_text = str(response.json()).lower()
        assert "unique" in response_text or "already" in response_text

    @pytest.mark.asyncio
    async def test_create_service_invalid_max_concurrent_tasks(
        self, client: AsyncClient
    ):
        """Тест создания сервиса с невалидным max_concurrent_tasks (меньше 1)"""
        invalid_service = {
            "name": "invalid_tasks_service",
            "display_name": "Invalid Tasks",
            "max_concurrent_tasks": 0,  # Должно быть >= 1
        }

        response = await client.post("/services/", json=invalid_service)

        assert response.status_code == 422
        assert "greater than or equal to 1" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_service_invalid_timeout_seconds(self, client: AsyncClient):
        """Тест создания сервиса с невалидным timeout_seconds (больше максимума)"""
        invalid_service = {
            "name": "invalid_timeout_service",
            "display_name": "Invalid Timeout",
            "timeout_seconds": 100000,  # Должно быть <= 86400
        }

        response = await client.post("/services/", json=invalid_service)

        assert response.status_code == 422
        assert "less than or equal to 86400" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_service_name_too_long(self, client: AsyncClient):
        """Тест создания сервиса с слишком длинным name"""
        invalid_service = {
            "name": "a" * 101,  # Максимум 100 символов
            "display_name": "Long Name Service",
        }

        response = await client.post("/services/", json=invalid_service)

        assert response.status_code == 422
        assert "string_too_long" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_update_service_forbidden_fields(
        self, client: AsyncClient, sample_service: Service
    ):
        """Тест обновления с передачей лишних полей (extra='forbid' в ServiceUpdate)"""
        update_data = {
            "display_name": "New Name",
            "unknown_field": "should_fail",  # Это поле не разрешено
        }

        response = await client.patch(
            f"/services/{sample_service.id}", json=update_data
        )

        # В схеме ServiceUpdate указано model_config = ConfigDict(extra="forbid")
        assert response.status_code == 422
        assert "extra_forbidden" in str(response.json()).lower()
