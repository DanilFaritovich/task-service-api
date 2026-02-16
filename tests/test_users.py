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
        user_data = {
            "tg_id": 987654321,
            "username": "new_user"
        }

        response = await client.post("/users/", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["tg_id"] == 987654321
        assert data["username"] == "new_user"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_users(self, client: AsyncClient, sample_user: User):
        """Тест получения списка пользователей"""
        response = await client.get("/users/")

        assert response.status_code == 200
        data = response.json()
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

    @pytest.mark.asyncio
    async def test_get_user_by_tg_id(self, client: AsyncClient, sample_user: User):
        """Тест получения пользователя по Telegram ID"""
        response = await client.get(f"/users/tg/{sample_user.tg_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["tg_id"] == sample_user.tg_id

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient):
        """Тест получения несуществующего пользователя"""
        response = await client.get("/users/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, sample_user: User):
        """Тест обновления пользователя"""
        update_data = {
            "username": "updated_username",
            "is_active": False
        }

        response = await client.put(f"/users/{sample_user.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updated_username"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, sample_user: User):
        """Тест удаления пользователя"""
        response = await client.delete(f"/users/{sample_user.id}")

        assert response.status_code == 204

        # Проверяем, что пользователь удалён
        response = await client.get(f"/users/{sample_user.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, client: AsyncClient, sample_user: User):
        """Тест создания пользователя с дублирующим tg_id"""
        duplicate_user = {
            "tg_id": sample_user.tg_id,  # Дублирующий tg_id
            "username": "duplicate"
        }

        response = await client.post("/users/", json=duplicate_user)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_partial_update_user(self, client: AsyncClient, sample_user: User):
        """Тест частичного обновления пользователя"""
        # Обновляем только одно поле
        response = await client.put(
            f"/users/{sample_user.id}",
            json={"username": "partial_update"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "partial_update"
        # Проверяем, что другие поля не изменились
        assert data["tg_id"] == sample_user.tg_id