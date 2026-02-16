"""
Тесты для эндпоинтов сервисов
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Service


class TestServices:
    """Тесты для операций с сервисами"""

    @pytest.mark.asyncio
    async def test_create_service(self, client: AsyncClient):
        """Тест создания нового сервиса"""
        service_data = {
            "name": "image_processor",
            "display_name": "Image Processor",
            "description": "Process images",
            "is_active": True,
            "is_blocked": False,
            "max_concurrent_tasks": 5,
            "timeout_seconds": 300
        }

        response = await client.post("/services/", json=service_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "image_processor"
        assert data["display_name"] == "Image Processor"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_services(self, client: AsyncClient, sample_service: Service):
        """Тест получения списка сервисов"""
        response = await client.get("/services/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_service_by_id(self, client: AsyncClient, sample_service: Service):
        """Тест получения сервиса по ID"""
        response = await client.get(f"/services/{sample_service.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_service.id
        assert data["name"] == sample_service.name

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, client: AsyncClient):
        """Тест получения несуществующего сервиса"""
        response = await client.get("/services/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_service(self, client: AsyncClient, sample_service: Service):
        """Тест обновления сервиса"""
        update_data = {
            "display_name": "Updated Service",
            "description": "Updated description",
            "max_concurrent_tasks": 10
        }

        response = await client.put(f"/services/{sample_service.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Service"
        assert data["max_concurrent_tasks"] == 10

    @pytest.mark.asyncio
    async def test_delete_service(self, client: AsyncClient, sample_service: Service):
        """Тест удаления сервиса"""
        response = await client.delete(f"/services/{sample_service.id}")

        assert response.status_code == 204

        # Проверяем, что сервис удалён
        response = await client.get(f"/services/{sample_service.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_active_services(self, client: AsyncClient):
        """Тест фильтрации активных сервисов"""
        # Создаём активный и неактивный сервисы
        active_service = {
            "name": "active_service",
            "display_name": "Active",
            "is_active": True
        }
        inactive_service = {
            "name": "inactive_service",
            "display_name": "Inactive",
            "is_active": False
        }

        await client.post("/services/", json=active_service)
        await client.post("/services/", json=inactive_service)

        response = await client.get("/services/?only_active=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(service["is_active"] for service in data)

    @pytest.mark.asyncio
    async def test_block_service(self, client: AsyncClient, sample_service: Service):
        """Тест блокировки сервиса"""
        response = await client.post(f"/services/{sample_service.id}/block")

        assert response.status_code == 200
        data = response.json()
        assert data["is_blocked"] is True

    @pytest.mark.asyncio
    async def test_unblock_service(self, client: AsyncClient, sample_service: Service):
        """Тест разблокировки сервиса"""
        # Сначала блокируем
        await client.post(f"/services/{sample_service.id}/block")

        # Затем разблокируем
        response = await client.post(f"/services/{sample_service.id}/unblock")

        assert response.status_code == 200
        data = response.json()
        assert data["is_blocked"] is False

    @pytest.mark.asyncio
    async def test_create_service_duplicate(self, client: AsyncClient, sample_service: Service):
        """Тест создания сервиса с дублирующим именем"""
        duplicate_service = {
            "name": sample_service.name,  # Дублирующее имя
            "display_name": "Duplicate",
            "is_active": True
        }

        response = await client.post("/services/", json=duplicate_service)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()