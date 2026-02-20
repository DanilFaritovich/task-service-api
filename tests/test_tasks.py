"""
Тесты для эндпоинтов задач
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Service, Task, User


def _extract_fastcrud_data(response_json: dict | list) -> list:
    """
    Вспомогательная функция для извлечения списка данных из ответа fastcrud.
    fastcrud возвращает {"data": [...], "total_count": N}, а тесты ожидают список.
    """
    if isinstance(response_json, dict) and "data" in response_json:
        return response_json["data"]
    return response_json if isinstance(response_json, list) else []


class TestTasks:
    """Тесты для операций с задачами"""

    @pytest.mark.asyncio
    async def test_create_task(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест создания новой задачи"""
        task_data = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Image processing",
            "status": "pending",
            "error_message": None,
            "result_data": None,
        }

        response = await client.post("/tasks", json=task_data)  # Без слеша в конце

        assert response.status_code == 200  # fastcrud возвращает 200, не 201
        data = response.json()
        assert data["user_id"] == sample_user.id
        assert data["service_id"] == sample_service.id
        assert data["task_name"] == "Image processing"
        assert data["status"] == "pending"
        assert "id" in data
        assert data["id"] > 0

    @pytest.mark.asyncio
    async def test_get_tasks(self, client: AsyncClient, sample_task: Task):
        """Тест получения списка задач"""
        response = await client.get("/tasks")  # Без слеша в конце

        assert response.status_code == 200
        data = response.json()

        # 🔥 fastcrud возвращает {"data": [...], "total_count": N}
        tasks = _extract_fastcrud_data(data)

        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        # Проверка структуры элемента
        assert "id" in tasks[0]
        assert "task_name" in tasks[0]

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, client: AsyncClient, sample_task: Task):
        """Тест получения задачи по ID"""
        response = await client.get(f"/tasks/{sample_task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task.id
        assert data["user_id"] == sample_task.user_id
        assert data["task_name"] == sample_task.task_name

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        """Тест получения несуществующей задачи"""
        response = await client.get("/tasks/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, client: AsyncClient, sample_task: Task):
        """Тест обновления задачи"""
        update_data = {
            "task_name": "Updated task name",
            "status": "completed",
            "result_data": {"processed": True, "output_file": "result.jpg"},
        }

        # Выполняем обновление
        response = await client.patch(f"/tasks/{sample_task.id}", json=update_data)
        assert response.status_code == 200

        # 🔥 Проверяем результат через отдельный GET-запрос
        # (fastcrud 0.21 не возвращает тело ответа на PATCH)
        get_response = await client.get(f"/tasks/{sample_task.id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["task_name"] == "Updated task name"
        assert data["status"] == "completed"
        assert data["result_data"] == {"processed": True, "output_file": "result.jpg"}

    @pytest.mark.asyncio
    async def test_delete_task(self, client: AsyncClient, sample_task: Task):
        """Тест удаления задачи"""
        response = await client.delete(f"/tasks/{sample_task.id}")

        # 🔥 fastcrud 0.21 возвращает 200, а не 204
        assert response.status_code == 200

        # Проверяем, что задача удалена
        response = await client.get(f"/tasks/{sample_task.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_task_invalid_status(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест создания задачи с невалидным статусом"""
        invalid_task = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Invalid status task",
            "status": "invalid_status",  # Невалидный статус
        }

        response = await client.post("/tasks", json=invalid_task)

        assert response.status_code == 422
        data = response.json()

        # 🔥 Pydantic v2: проверяем 'enum' вместо 'value_error'
        detail = data.get("detail", [])
        assert any(
            err.get("type") == "enum" or "enum" in str(err.get("msg", "")).lower()
            for err in detail
        ), f"Ожидали ошибку валидации enum, получили: {detail}"

    @pytest.mark.asyncio
    async def test_create_task_invalid_user(
        self, client: AsyncClient, sample_service: Service
    ):
        """Тест создания задачи с несуществующим пользователем"""
        invalid_task = {
            "user_id": 999999,  # Несуществующий пользователь
            "service_id": sample_service.id,
            "task_name": "Invalid user task",
            "status": "pending",
        }

        response = await client.post("/tasks", json=invalid_task)

        # 🔥 Благодаря глобальному обработчику IntegrityError в main.py
        # ForeignKeyViolation теперь возвращается как 400, а не 500
        assert response.status_code == 400
        detail = response.json().get("detail", "").lower()
        assert (
            "does not exist" in detail
            or "foreign key" in detail
            or "integrity" in detail
        )

    @pytest.mark.asyncio
    async def test_create_task_invalid_service(
        self, client: AsyncClient, sample_user: User
    ):
        """Тест создания задачи с несуществующим сервисом"""
        invalid_task = {
            "user_id": sample_user.id,
            "service_id": 999999,  # Несуществующий сервис
            "task_name": "Invalid service task",
            "status": "pending",
        }

        response = await client.post("/tasks", json=invalid_task)

        assert response.status_code == 400
        detail = response.json().get("detail", "").lower()
        assert (
            "does not exist" in detail
            or "foreign key" in detail
            or "integrity" in detail
        )

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест получения задач по статусу"""
        # Создаем задачи с разными статусами
        statuses = ["pending", "running", "completed"]
        for status in statuses:
            task_data = {
                "user_id": sample_user.id,
                "service_id": sample_service.id,
                "task_name": f"Task {status}",
                "status": status,
            }
            await client.post("/tasks", json=task_data)

        # Проверяем получение задач по статусу
        for status in statuses:
            response = await client.get(f"/tasks/status/{status}")
            assert response.status_code == 200
            data = response.json()

            # 🔥 Извлекаем список из ответа fastcrud
            tasks = _extract_fastcrud_data(data)
            assert all(task["status"] == status for task in tasks), (
                f"Не все задачи имеют статус {status}: {[t['status'] for t in tasks]}"
            )

    @pytest.mark.asyncio
    async def test_get_tasks_by_invalid_status(self, client: AsyncClient):
        """Тест получения задач с невалидным статусом"""
        response = await client.get("/tasks/status/invalid_status")
        assert response.status_code == 400
        detail = response.json().get("detail", "").lower()
        assert "invalid status" in detail

    @pytest.mark.asyncio
    async def test_get_tasks_pagination(
        self, client: AsyncClient, sample_user: User, sample_service: Service
    ):
        """Тест пагинации задач"""
        # Создаем больше задач, чем лимит по умолчанию
        for i in range(15):
            task_data = {
                "user_id": sample_user.id,
                "service_id": sample_service.id,
                "task_name": f"Pagination task {i}",
                "status": "pending",
            }
            await client.post("/tasks", json=task_data)

        # Проверяем пагинацию
        response = await client.get("/tasks?page=1&size=10")  # Без слеша
        assert response.status_code == 200
        data = response.json()

        # 🔥 Извлекаем список из ответа fastcrud
        tasks = _extract_fastcrud_data(data)
        assert len(tasks) == 10, f"Ожидали 10 задач, получили {len(tasks)}"

        response = await client.get("/tasks?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        tasks = _extract_fastcrud_data(data)
        assert len(tasks) >= 5, f"Ожидали >= 5 задач, получили {len(tasks)}"
