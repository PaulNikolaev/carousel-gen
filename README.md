# Carousel Gen

## Описание

MVP для генерации каруселей под соцсети (например, Instagram): создание из текста, видео или ссылок, настройка формата (количество слайдов, язык, стиль), генерация слайдов через LLM, редактор (шаблон, фон, макет, шапка/подвал, типографика) и экспорт в набор изображений (PNG). Интерфейс — десктоп и мобильный (Nuxt/Vue), бэкенд — FastAPI, хранилище — PostgreSQL и MinIO.

**Основные возможности:**

- Создание карусели из текста, видео или списка ссылок
- Формат: 6–10 слайдов, язык (RU/EN/FR), пример стиля текста для LLM
- Асинхронная генерация слайдов (очередь, статусы, оценка токенов)
- Редактор: переключение слайдов, правка текста, дизайн (шаблон, фон, макет, шапка/подвал, шрифт), «применить ко всем» / только к выбранному слайду
- Экспорт карусели в ZIP с PNG-слайдами и скачивание по ссылке

---

## Как запустить

Стек: **backend** (FastAPI), **frontend** (Nuxt), **PostgreSQL**, **MinIO**. Конфигурация по умолчанию: `docker-compose.yml`.

### Подготовка

1. Скопируйте `backend/.env.example` в `backend/.env` и при необходимости задайте переменные (БД, MinIO, LLM API и т.д.):

   ```bash
   cp backend/.env.example backend/.env
   ```

   PowerShell:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

Миграции БД выполняются при старте backend.

### Запуск

- **В фоне** (сервисы в контейнерах, логи не в консоль):

  ```bash
  docker compose up -d
  ```

  Первый запуск или после изменений в коде/образах — с пересборкой:

  ```bash
  docker compose up --build -d
  ```

- **С логами в консоль** (остановка по Ctrl+C):

  ```bash
  docker compose up
  ```

  С пересборкой:

  ```bash
  docker compose up --build
  ```

### Остановка

- Остановить контейнеры (данные в томах сохраняются):

  ```bash
  docker compose down
  ```

- Остановить и удалить тома (полная очистка БД и MinIO):

  ```bash
  docker compose down -v
  ```

### Адреса сервисов

| Сервис      | Адрес |
|------------|--------|
| Backend    | http://localhost:8000 |
| Swagger UI| http://localhost:8000/docs |
| Frontend   | http://localhost:3000 |
| PostgreSQL| localhost:5432 |
| MinIO API  | http://localhost:9000 |
| MinIO консоль | http://localhost:9001 |

Если в `backend/.env` задан `API_KEY`, все запросы к API (кроме `/api/v1/health`) должны содержать заголовок `X-API-Key: <значение API_KEY>`.

---

## Примеры запросов (curl)

Базовый URL API: `http://localhost:8000/api/v1`. Если включён API key, добавьте в каждый запрос: `-H "X-API-Key: YOUR_API_KEY"`.

### Проверка работы API

```bash
curl -s http://localhost:8000/api/v1/health
# {"status":"ok"}
```

### Создание карусели (черновик)

```bash
curl -s -X POST http://localhost:8000/api/v1/carousels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Моя карусель",
    "source_type": "text",
    "source_payload": {"text": "Текст поста для разбивки на слайды..."},
    "format": {"slides_count": 8, "language": "ru", "style_hint": "Короткие фразы, дружелюбный тон"},
    "language": "ru"
  }'
```

В ответе — объект карусели с `id`, `status: "draft"` и т.д.

### Список каруселей

```bash
curl -s "http://localhost:8000/api/v1/carousels?limit=10"
# с фильтром по статусу:
curl -s "http://localhost:8000/api/v1/carousels?status=ready&limit=5"
```

### Получить карусель по ID

```bash
CAROUSEL_ID="<uuid из ответа создания>"
curl -s "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID"
```

### Дизайн карусели (текущий слайд)

```bash
# дизайн по умолчанию (без слайда)
curl -s "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/design"

# дизайн для конкретного слайда (effective = база + overrides слайда)
curl -s "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/design?slide_id=$SLIDE_ID"
```

### Обновить дизайн

```bash
# только для текущего слайда (передать slide_id)
curl -s -X PATCH "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/design?slide_id=$SLIDE_ID" \
  -H "Content-Type: application/json" \
  -d '{"typography": {"font_size": 18, "font_weight": "bold"}}'

# применить ко всем слайдам
curl -s -X PATCH "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/design?apply_to_all=true" \
  -H "Content-Type: application/json" \
  -d '{"template": "minimal", "layout": {"padding": 32}}'
```

### Запуск генерации слайдов

```bash
curl -s -X POST http://localhost:8000/api/v1/generations \
  -H "Content-Type: application/json" \
  -d "{\"carousel_id\": \"$CAROUSEL_ID\"}"
# 202, в теле — generation id и статус
```

### Статус генерации

```bash
GEN_ID="<id из ответа POST /generations>"
curl -s "http://localhost:8000/api/v1/generations/$GEN_ID"
# status: queued | running | done | failed; при done — result со слайдами
```

### Запуск экспорта в PNG (ZIP)

```bash
curl -s -X POST http://localhost:8000/api/v1/exports \
  -H "Content-Type: application/json" \
  -d "{\"carousel_id\": \"$CAROUSEL_ID\"}"
# 202, в теле — export id
```

### Статус экспорта и ссылка на скачивание

```bash
EXPORT_ID="<id из ответа POST /exports>"
curl -s "http://localhost:8000/api/v1/exports/$EXPORT_ID"
# status: pending | running | done | failed; при done — download_url
```

### Слайды карусели (список, обновление текста)

```bash
# список слайдов
curl -s "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/slides"

# обновить текст слайда
curl -s -X PATCH "http://localhost:8000/api/v1/carousels/$CAROUSEL_ID/slides/$SLIDE_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "Новый заголовок", "body": "Новый текст", "footer": "Подвал"}'
```

Полная схема API и все параметры — в [Swagger UI](http://localhost:8000/docs).

---

## Тестирование

Тесты используют БД `carousel_test` и файл `docker-compose.test.yml`. Порядок: **postgres** → **migrate** → **backend** (pytest). Переменные — из `backend/.env.test` (приоритет у переменных из compose).

### Подготовка к тестам

```bash
cp backend/.env.test.example backend/.env.test
```

PowerShell:

```powershell
Copy-Item backend\.env.test.example backend\.env.test
```

### Запуск тестов

```bash
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml logs backend
```

### Остановка тестового стека

```bash
docker compose -f docker-compose.test.yml down
# с удалением томов:
docker compose -f docker-compose.test.yml down -v
```
