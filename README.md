# Carousel Gen

## Запуск проекта

1. Скопируйте `backend/.env.example` в `backend/.env`, при необходимости заполните переменные.

   ```bash
   cp backend/.env.example backend/.env
   ```

   PowerShell:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

2. Запуск:

   ```bash
   docker compose up --build
   ```

3. Миграции БД применяются при старте backend.

| Сервис   | Адрес |
|----------|-------|
| Backend  | http://localhost:8000 |
| Swagger  | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Postgres | localhost:5432 |
| MinIO API | http://localhost:9000 |
| MinIO консоль | http://localhost:9001 |

## Тестирование

Тесты используют БД `carousel_test` и `docker-compose.test.yml`. Сервис `migrate` применяет миграции (`alembic upgrade head`) при старте.

1. Скопируйте шаблон тестового окружения:

   ```bash
   cp backend/.env.test.example backend/.env.test
   ```

   PowerShell:

   ```powershell
   Copy-Item backend\.env.test.example backend\.env.test
   ```

2. Поднимите стек и запустите тесты:

   ```bash
   docker compose -f docker-compose.test.yml up -d
   docker compose -f docker-compose.test.yml run --rm backend
   ```

   При `up -d` поднимается postgres, сервис `migrate` выполняет `alembic upgrade head` и завершается; при необходимости тесты запускают отдельно через `run --rm backend`.

3. Остановка:

   ```bash
   docker compose -f docker-compose.test.yml down
   ```

## Локальный запуск pytest

1. `cd backend`
2. Скопируйте `backend/.env.test.example` в `backend/.env.test`, в нём укажите `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/carousel_test`.
3. Установите зависимости и поднимите тестовый Postgres:

   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   docker compose -f docker-compose.test.yml up -d postgres
   ```

4. Миграции и тесты:

   ```bash
   alembic upgrade head
   python -m pytest tests -v
   ```
