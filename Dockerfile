# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости приложения
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаём непривилегированного пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Копируем всё содержимое проекта
COPY . .

# Запускаем основной скрипт
CMD ["python", "main.py"]