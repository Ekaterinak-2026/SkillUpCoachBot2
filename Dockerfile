# v2 rebuild 2026-09-22 — cache buster
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные шрифты с кириллицей (для рендера картинок)
RUN apt-get update && apt-get install -y fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код (свежий, из репозитория)
COPY . .

# Запускаем бота
CMD ["python", "main.py"]