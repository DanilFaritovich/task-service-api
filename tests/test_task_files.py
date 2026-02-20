"""
Тесты для эндпоинтов файлов задач
"""

import pytest
from httpx import AsyncClient

from backend.database.models import Task, TaskFile


class TestTaskFiles:
    """Тесты для операций с файлами задач"""

    @pytest.mark.asyncio
    async def test_create_task_file(self, client: AsyncClient, sample_task: Task):
        """Тест создания нового файла задачи"""
        task_file_data = {
            "task_id": sample_task.id,
            "file_path": "/uploads/image.jpg",
            "file_size": 102400,
            "file_hash": "a1b2c3d4e5f6",
        }

        response = await client.post("/task-files/", json=task_file_data)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == sample_task.id
        assert data["file_path"] == "/uploads/image.jpg"
        assert data["file_size"] == 102400
        assert data["file_hash"] == "a1b2c3d4e5f6"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_task_files(
        self, client: AsyncClient, sample_task_file: TaskFile
    ):
        """Тест получения списка файлов задач"""
        response = await client.get("/task-files/")

        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_task_file_by_id(
        self, client: AsyncClient, sample_task_file: TaskFile
    ):
        """Тест получения файла задачи по ID"""
        response = await client.get(f"/task-files/{sample_task_file.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task_file.id
        assert data["task_id"] == sample_task_file.task_id
        assert data["file_path"] == sample_task_file.file_path

    @pytest.mark.asyncio
    async def test_get_task_file_not_found(self, client: AsyncClient):
        """Тест получения несуществующего файла задачи"""
        response = await client.get("/task-files/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task_file(
        self, client: AsyncClient, sample_task_file: TaskFile
    ):
        """Тест обновления файла задачи"""
        update_data = {
            "file_path": "/uploads/processed.jpg",
            "file_size": 204800,
            "file_hash": "f6e5d4c3b2a1",
        }

        response = await client.patch(
            f"/task-files/{sample_task_file.id}", json=update_data
        )

        assert response.status_code == 200

        response = await client.get(f"/task-files/{sample_task_file.id}")
        assert response.status_code == 200

        data = response.json()

        assert data["file_path"] == "/uploads/processed.jpg"
        assert data["file_size"] == 204800
        assert data["file_hash"] == "f6e5d4c3b2a1"

    @pytest.mark.asyncio
    async def test_delete_task_file(
        self, client: AsyncClient, sample_task_file: TaskFile
    ):
        """Тест удаления файла задачи"""
        response = await client.delete(f"/task-files/{sample_task_file.id}")

        assert response.status_code == 200

        # Проверяем, что файл задачи удален
        response = await client.get(f"/task-files/{sample_task_file.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_task_file_invalid_task(self, client: AsyncClient):
        """Тест создания файла задачи с несуществующей задачей"""
        invalid_file = {
            "task_id": 999999,  # Несуществующая задача
            "file_path": "/uploads/invalid.jpg",
            "file_size": 102400,
            "file_hash": "a1b2c3",
        }

        response = await client.post("/task-files/", json=invalid_file)

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_task_file_invalid_path(
        self, client: AsyncClient, sample_task: Task
    ):
        """Тест создания файла задачи с невалидным путем"""
        invalid_file = {
            "task_id": sample_task.id,
            "file_path": "",  # Пустой путь
            "file_size": 102400,
            "file_hash": "a1b2c3",
        }

        response = await client.post("/task-files/", json=invalid_file)

        assert response.status_code == 422
        assert "string_too_short" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_create_task_file_negative_size(
        self, client: AsyncClient, sample_task: Task
    ):
        """Тест создания файла задачи с отрицательным размером"""
        invalid_file = {
            "task_id": sample_task.id,
            "file_path": "/uploads/negative.jpg",
            "file_size": -100,  # Отрицательный размер
            "file_hash": "a1b2c3",
        }

        response = await client.post("/task-files/", json=invalid_file)

        assert response.status_code == 422
        assert "greater than or equal to 0" in str(response.json()).lower()
