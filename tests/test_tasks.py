"""
Тесты для эндпоинтов задач
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Task, User, Service


class TestTasks:
    """Тесты для операций с задачами"""

    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient, sample_user: User, sample_service: Service):
        """Тест создания новой задачи"""
        task_data = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Test Task Creation",
            "status": "pending"
        }

        response = await client.post("/tasks/", json=task_data)

        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "Test Task Creation"
        assert data["status"] == "pending"
        assert data["user_id"] == sample_user.id
        assert data["service_id"] == sample_service.id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_tasks(self, client: AsyncClient, sample_task: Task):
        """Тест получения списка задач"""
        response = await client.get("/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, client: AsyncClient, sample_task: Task):
        """Тест получения задачи по ID"""
        response = await client.get(f"/tasks/{sample_task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task.id
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
            "status": "running",
            "error_message": None
        }

        response = await client.put(f"/tasks/{sample_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_update_task_with_result(self, client: AsyncClient, sample_task: Task):
        """Тест обновления задачи с результатом"""
        update_data = {
            "status": "completed",
            "result_data": {
                "output_path": "/path/to/output",
                "processing_time": 2.5
            }
        }

        response = await client.put(f"/tasks/{sample_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result_data"]["output_path"] == "/path/to/output"

    @pytest.mark.asyncio
    async def test_filter_tasks_by_user(self, client: AsyncClient, sample_user: User, sample_service: Service):
        """Тест фильтрации задач по пользователю"""
        # Создаём несколько задач
        task1 = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Task 1",
            "status": "pending"
        }
        task2 = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Task 2",
            "status": "completed"
        }

        await client.post("/tasks/", json=task1)
        await client.post("/tasks/", json=task2)

        response = await client.get(f"/tasks/?user_id={sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(task["user_id"] == sample_user.id for task in data)

    @pytest.mark.asyncio
    async def test_filter_tasks_by_status(self, client: AsyncClient, sample_task: Task):
        """Тест фильтрации задач по статусу"""
        response = await client.get("/tasks/?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(task["status"] == "pending" for task in data)

    @pytest.mark.asyncio
    async def test_create_task_file(self, client: AsyncClient, sample_task: Task):
        """Тест добавления файла к задаче"""
        file_data = {
            "task_id": sample_task.id,
            "file_path": "/uploads/test_file.jpg",
            "file_size": 1024000,
            "file_hash": "abc123def456"
        }

        response = await client.post(f"/tasks/{sample_task.id}/files", json=file_data)

        assert response.status_code == 201
        data = response.json()
        assert data["file_path"] == "/uploads/test_file.jpg"
        assert data["task_id"] == sample_task.id

    @pytest.mark.asyncio
    async def test_get_task_files(self, client: AsyncClient, sample_task: Task):
        """Тест получения файлов задачи"""
        # Создаём файл
        await client.post(
            f"/tasks/{sample_task.id}/files",
            json={
                "task_id": sample_task.id,
                "file_path": "/uploads/file1.jpg"
            }
        )

        response = await client.get(f"/tasks/{sample_task.id}/files")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_running_tasks_count(self, client: AsyncClient, sample_service: Service, sample_user: User):
        """Тест получения количества запущенных задач"""
        # Создаём запущенную задачу
        task_data = {
            "user_id": sample_user.id,
            "service_id": sample_service.id,
            "task_name": "Running Task",
            "status": "running"
        }

        await client.post("/tasks/", json=task_data)

        response = await client.get(f"/tasks/running/count/{sample_service.id}")

        assert response.status_code == 200
        data = response.json()
        assert "running_tasks_count" in data
        assert data["running_tasks_count"] >= 1