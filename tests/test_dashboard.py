"""
Тесты для эндпоинта дашборда
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Service, User


class TestDashboard:
    """Тесты для дашборда"""

    @pytest.mark.asyncio
    async def test_dashboard_stats(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест получения статистики дашборда"""
        # Создаем несколько задач для статистики
        statuses = ["pending", "running", "completed", "failed", "cancelled"]
        for status in statuses:
            task_data = {
                "user_id": sample_user.id,
                "service_id": sample_service.id,
                "task_name": f"Dashboard task {status}",
                "status": status,
            }
            await client.post("/tasks/", json=task_data)

        # Создаем несколько логов
        for i in range(5):
            log_data = {
                "user_id": sample_user.id,
                "source": "dashboard_test",
                "message": f"Test log {i}",
                "level": "INFO",
            }
            await client.post("/logs/", json=log_data)

        response = await client.get("/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # Проверяем основные поля
        assert "total_users" in data
        assert "total_services" in data
        assert "active_services" in data
        assert "tasks_by_status" in data
        assert "total_tasks" in data
        assert "recent_logs" in data
        assert "timestamp" in data

        # Проверяем статистику по задачам
        assert data["total_tasks"] >= 5
        for status in statuses:
            assert status in data["tasks_by_status"]
            if status == "pending":
                assert data["tasks_by_status"][status] >= 1

        # Проверяем недавние логи
        assert len(data["recent_logs"]) <= 10
        if data["recent_logs"]:
            assert "id" in data["recent_logs"][0]
            assert "level" in data["recent_logs"][0]
            assert "message" in data["recent_logs"][0]
            assert "timestamp" in data["recent_logs"][0]

    @pytest.mark.asyncio
    async def test_dashboard_with_no_data(self, client: AsyncClient):
        """Тест получения статистики дашборда без данных"""
        response = await client.get("/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # Проверяем, что все счетчики равны 0 или пусты
        assert data["total_users"] == 0
        assert data["total_services"] == 0
        assert data["active_services"] == 0
        assert all(count == 0 for count in data["tasks_by_status"].values())
        assert data["total_tasks"] == 0
        assert len(data["recent_logs"]) == 0
