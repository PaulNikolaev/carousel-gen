# Carousel Gen

## Запуск проекта

1. Подготовка: скопируйте `backend/.env.example` в `backend/.env` и при необходимости заполните переменные.
2. Запуск: `docker compose up` (или `docker compose up --build`).
3. Миграции БД применяются при старте backend (entrypoint).

Порты:

- backend: 8000
- frontend: 3000
- postgres: 5432
- minio: 9000 (API), 9001 (консоль)

## Тестирование

Тесты используют отдельную инфраструктуру и БД `carousel_test`.

### Запуск тестов в Docker (рекомендуется)

1. Подготовка: скопируйте шаблон тестового окружения:
   ```bash
   cp backend/.env.test.example backend/.env.test
   ```
2. Запуск тестовых сервисов (PostgreSQL для тестов):
   ```bash
   docker compose -f docker-compose.test.yml up -d postgres
   ```
3. Запуск pytest:
   ```bash
   docker compose -f docker-compose.test.yml run --rm backend
   ```
   (В `docker-compose.test.yml` для сервиса backend уже задана команда `python -m pytest tests -v`.)
4. Завершение:
   ```bash
   docker compose -f docker-compose.test.yml down
   ```

### Локальный запуск pytest (без полного Docker-окружения)

1. `cd backend`
2. Скопируйте `backend/.env.test.example` в `backend/.env.test` и при необходимости отредактируйте.
3. Установите зависимости: `pip install -r requirements.txt -r requirements-dev.txt`
4. Поднимите только тестовый Postgres: `docker compose -f docker-compose.test.yml up -d postgres`
5. В `backend/.env.test` задайте подключение к БД на хосте, например:
   `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/carousel_test`
   (порт 5433 — маппинг тестового контейнера postgres.)
6. Примените миграции: `alembic upgrade head`
7. Запуск тестов: `python -m pytest tests -v`

Файл `backend/.env.test` в репозиторий не коммитится; в репозитории хранится только шаблон `backend/.env.test.example`.
