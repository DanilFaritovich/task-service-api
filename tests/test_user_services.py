"""
Тесты для эндпоинтов конфигураций пользователей сервисов
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Service, User, UserService


class TestUserServices:
    """Тесты для операций с конфигурациями пользователей сервисов"""

    @pytest.mark.asyncio
    async def test_create_user_service(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест создания новой конфигурации пользователя для сервиса"""
        user_service_data = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "config_data": {"quality": "high", "size": "large"},
            "is_enabled": True,
        }

        response = await client.post("/user-services/", json=user_service_data)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == sample_user.id
        assert data["service_id"] == sample_service.id
        assert data["config_data"] == {"quality": "high", "size": "large"}
        assert data["is_enabled"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_user_services(
        self, client: AsyncClient, sample_user_service: UserService
    ):
        """Тест получения списка конфигураций"""
        response = await client.get("/user-services/")

        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_user_service_by_id(
        self, client: AsyncClient, sample_user_service: UserService
    ):
        """Тест получения конфигурации по ID"""
        response = await client.get(f"/user-services/{sample_user_service.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user_service.id
        assert data["user_id"] == sample_user_service.user_id
        assert data["service_id"] == sample_user_service.service_id

    @pytest.mark.asyncio
    async def test_get_user_service_not_found(self, client: AsyncClient):
        """Тест получения несуществующей конфигурации"""
        response = await client.get("/user-services/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_service(
        self, client: AsyncClient, sample_user_service: UserService
    ):
        """Тест обновления конфигурации"""
        update_data = {
            "config_data": {"quality": "medium", "size": "medium"},
            "is_enabled": False,
        }

        response = await client.patch(
            f"/user-services/{sample_user_service.id}", json=update_data
        )

        assert response.status_code == 200

        response = await client.get(f"/user-services/{sample_user_service.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["config_data"] == {"quality": "medium", "size": "medium"}
        assert data["is_enabled"] is False

    @pytest.mark.asyncio
    async def test_delete_user_service(
        self, client: AsyncClient, sample_user_service: UserService
    ):
        """Тест удаления конфигурации"""
        response = await client.delete(f"/user-services/{sample_user_service.id}")

        assert response.status_code == 200

        # Проверяем, что конфигурация удалена
        response = await client.get(f"/user-services/{sample_user_service.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_service_duplicate(
        self, client: AsyncClient, sample_user_service: UserService
    ):
        """Тест создания дублирующей конфигурации"""
        duplicate_data = {
            "user_id": sample_user_service.user_id,
            "service_id": sample_user_service.service_id,
            "config_data": {"quality": "low"},
            "is_enabled": True,
        }

        response = await client.post("/user-services/", json=duplicate_data)

        # Ожидаем ошибку 409 из-за уникального ограничения
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_user_service_invalid_user(
        self, client: AsyncClient, sample_service: Service
    ):
        """Тест создания конфигурации с несуществующим пользователем"""
        invalid_data = {
            "user_id": 999999,  # Несуществующий пользователь
            "service_id": sample_service.id,
            "config_data": {"quality": "high"},
            "is_enabled": True,
        }

        response = await client.post("/user-services/", json=invalid_data)

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_user_service_invalid_service(
        self, client: AsyncClient, sample_user: User
    ):
        """Тест создания конфигурации с несуществующим сервисом"""
        invalid_data = {
            "user_id": sample_user.id,
            "service_id": 999999,  # Несуществующий сервис
            "config_data": {"quality": "high"},
            "is_enabled": True,
        }

        response = await client.post("/user-services/", json=invalid_data)

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()
