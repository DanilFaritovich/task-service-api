"""
Тесты для эндпоинта здоровья
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


class TestHealth:
    """Тесты для проверки здоровья приложения"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Тест проверки здоровья приложения"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Проверяем основные поля
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "database" in data

        # Проверяем статус БД
        assert data["database"]["status"] == "healthy"
        assert "response_time_ms" in data["database"]
        assert data["database"]["type"] == "PostgreSQL"

    @pytest.mark.asyncio
    async def test_health_check_with_db_failure(self, client: AsyncClient):
        """Тест: БД недоступна → статус degraded"""

        from backend.api.deps import get_db  # уточните путь!
        from backend.api.main import app

        # 1. Мокаем сессию
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        # 2. Подменяем зависимость — возвращаем СЕССИЮ, а не генератор!
        app.dependency_overrides[get_db] = lambda: mock_session

        try:
            response = await client.get("/health")
            data = response.json()

            assert response.status_code == 200
            assert data["status"] == "degraded"
            assert data["database"]["status"] == "unhealthy"
            assert "error" in data["database"]
            assert "connection failed" in data["database"]["error"].lower()
        finally:
            # 3. Обязательно чистим overrides!
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Тест корневого эндпоинта"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Проверяем основные поля
        assert data["message"] == "Task Service API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
        assert data["health"] == "/health"
