# Carousel Gen

## Приложение (основной стек)

Стек: backend, frontend, postgres, minio. Файл по умолчанию: `docker-compose.yml`.

### Подготовка

1. Скопируйте `backend/.env.example` в `backend/.env`, при необходимости заполните переменные.

   ```bash
   cp backend/.env.example backend/.env
   ```

   PowerShell:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

Миграции БД применяются при старте backend.

### Запуск приложения

- **В фоне** (сервисы работают, логи в консоль не выводятся):

  ```bash
  docker compose up -d
  ```

  Первый раз или после изменения образов — с пересборкой:

  ```bash
  docker compose up --build -d
  ```

- **С выводом в консоль** (логи всех сервисов в текущем терминале, остановка по Ctrl+C):

  ```bash
  docker compose up
  ```

  С пересборкой:

  ```bash
  docker compose up --build
  ```

### Остановка приложения

- **Остановить контейнеры** (данные в тома сохраняются):

  ```bash
  docker compose down
  ```

- **Остановить и удалить тома** (полная очистка данных БД, MinIO и т.д.):

  ```bash
  docker compose down -v
  ```

| Сервис   | Адрес |
|----------|-------|
| Backend  | http://localhost:8000 |
| Swagger  | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Postgres | localhost:5432 |
| MinIO API | http://localhost:9000 |
| MinIO консоль | http://localhost:9001 |

---

## Тестирование

Тесты используют БД `carousel_test` и файл `docker-compose.test.yml`. Порядок запуска: **postgres** → **migrate** (миграции) → **backend** (pytest). Переменные окружения — из `backend/.env.test` (значения из compose имеют приоритет).

### Подготовка к тестам

Перед первым запуском создайте тестовый конфиг:

```bash
cp backend/.env.test.example backend/.env.test
```

PowerShell:

```powershell
Copy-Item backend\.env.test.example backend\.env.test
```

В `.env.test` уже указан `DATABASE_URL` для Docker (`postgres:5432`).

### Запуск тестов

- **В фоне** (postgres, migrate, backend поднимаются; backend один раз запускает pytest и завершается). Результаты — в логах:

  ```bash
  docker compose -f docker-compose.test.yml up -d
  docker compose -f docker-compose.test.yml logs backend
  ```

### Остановка тестового стека

- **Остановить контейнеры** (тестовая БД в томе сохраняется):

  ```bash
  docker compose -f docker-compose.test.yml down
  ```

- **Остановить и удалить тома** (очистить тестовую БД и тома):

  ```bash
  docker compose -f docker-compose.test.yml down -v
  ```
