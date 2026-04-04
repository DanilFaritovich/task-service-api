"""
Тесты для эндпоинтов пользователей
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User


class TestUsers:
    """Тесты для операций с пользователями"""

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient):
        """Тест создания нового пользователя"""
        user_data = {"tg_id": 123456, "username": "test_user", "is_active": True}

        response = await client.post("/users/", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["tg_id"] == 123456
        assert data["username"] == "test_user"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_users(self, client: AsyncClient, sample_user: User):
        """Тест получения списка пользователей"""
        response = await client.get("/users/")

        assert response.status_code == 200
        data = response.json()
        data = data["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, sample_user: User):
        """Тест получения пользователя по ID"""
        response = await client.get(f"/users/{sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["tg_id"] == sample_user.tg_id
        assert data["username"] == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_tg_id(
        self, client: AsyncClient, sample_user: User, db_session: AsyncSession
    ):
        """Тест получения пользователя по ID"""

        response = await client.get(f"/users/tg/{sample_user.tg_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["tg_id"] == sample_user.tg_id
        assert data["username"] == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient):
        """Тест получения несуществующего пользователя"""
        response = await client.get("/users/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, sample_user: User):
        """Тест обновления пользователя"""
        update_data = {"username": "updated_user", "is_active": False}

        response = await client.patch(f"/users/{sample_user.id}", json=update_data)

        assert response.status_code == 200

        get_response = await client.get(f"/users/{sample_user.id}")
        assert get_response.status_code == 200

        data = get_response.json()

        assert data["username"] == "updated_user"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, sample_user: User):
        """Тест удаления пользователя"""
        response = await client.delete(f"/users/{sample_user.id}")

        assert response.status_code == 200

        # Проверяем, что пользователь удалён
        response = await client.get(f"/users/{sample_user.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_duplicate_tg_id(
        self, client: AsyncClient, sample_user: User
    ):
        """Тест создания пользователя с дублирующим tg_id"""
        duplicate_user = {
            "tg_id": sample_user.tg_id,  # Дублирующий tg_id
            "username": "duplicate_user",
            "is_active": True,
        }

        response = await client.post("/users/", json=duplicate_user)

        # Ожидаем ошибку 422, так как tg_id уникален
        assert response.status_code == 422
        assert "already registered" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_tg_id(self, client: AsyncClient):
        """Тест создания пользователя с невалидным tg_id"""
        invalid_user = {
            "tg_id": -1,  # Невалидный tg_id
            "username": "invalid_user",
            "is_active": True,
        }

        response = await client.post("/users/", json=invalid_user)

        assert response.status_code == 422
        assert "greater than or equal to 1" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_username(self, client: AsyncClient):
        """Тест создания пользователя с коротким username"""
        invalid_user = {
            "tg_id": 789012,
            "username": "",  # Пустой username
            "is_active": True,
        }

        response = await client.post("/users/", json=invalid_user)

        assert response.status_code == 422
        assert "string_too_short" in str(response.json()).lower()
