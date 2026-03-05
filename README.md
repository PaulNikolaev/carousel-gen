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

Тесты используют БД `carousel_test` и `docker-compose.test.yml`. Порядок запуска: **postgres** → **migrate** (миграции) → **backend** (pytest). Переменные окружения берутся из `backend/.env.test` (значения из compose переопределяют при необходимости).

Перед первым запуском создайте тестовый конфиг:

```bash
cp backend/.env.test.example backend/.env.test
```

PowerShell:

```powershell
Copy-Item backend\.env.test.example backend\.env.test
```

В `.env.test` уже указан `DATABASE_URL` для Docker (`postgres:5432`); для локального pytest без compose см. раздел «Локальный запуск pytest».

### Одна команда (в фоне)

```bash
docker compose -f docker-compose.test.yml up -d
```

Поднимаются postgres, migrate и backend; backend один раз запускает pytest и завершается. Результаты тестов смотрите в логах:

```bash
docker compose -f docker-compose.test.yml logs backend
```

### Одна команда (вывод в консоль, код выхода = код pytest)

```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

Вывод тестов идёт в консоль; после завершения pytest compose останавливается с тем же кодом выхода (0 = успех).

### Остановка

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
