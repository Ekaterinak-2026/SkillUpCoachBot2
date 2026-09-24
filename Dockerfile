# v2 rebuild 2026-09-22 — cache buster
FROM python:3.11-slim

WORKDIR /app


# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код (свежий, из репозитория)
COPY . .

# Запускаем бота
CMD ["python", "main.py"]