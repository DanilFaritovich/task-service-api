# Stage 1: Build
FROM python:3.14-slim AS builder

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.14-slim

# Установка только необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser
USER appuser

# Копирование зависимостей из builder stage
COPY --from=builder /home/appuser/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Копирование приложения
WORKDIR /app
COPY --chown=appuser:appuser . .

# Проверка подключения к БД перед запуском
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Экспозиция порта
EXPOSE 8000

# Запуск приложения
CMD ["/wait-for-it.sh", "db:5432", "--", "python", "main.py"]