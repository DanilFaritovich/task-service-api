# Запустите одной командой
docker compose up -d --build

# Просмотр логов
docker logs -f tg_bot_api

# Swagger
http://127.0.0.1:8000/docs#/

# Запуск тестов 
pytest tests/