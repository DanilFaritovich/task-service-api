# Запустите одной командой
docker compose up -d --build

# Просмотр логов
docker logs -f tg_bot_api

# Swagger
http://127.0.0.1:8000/docs#/
http://127.0.0.1:8000/redoc#/

# Запуск тестов 
pytest tests/

# Миграция alembic
Создание файла миграции с Base
```bash
alembic revision --autogenerate -m "Inital migration"
```
Создание пустого файла миграции
```bash
alembic revision -m "Inital migration"
```
Деплой миграции в бд
```bash
alembic upgrade head
```
Откат изменений
```bash
alembic downgrade base
```