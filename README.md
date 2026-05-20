
# Semantic Search API

REST-сервис семантического поиска по базе вопросов и ответов. Принимает текстовый запрос на естественном языке, находит наиболее близкие по смыслу записи в векторной базе данных и возвращает топ-N результатов с оценкой релевантности.

## Содержание

- [Стек технологий](#стек-технологий)
- [Структура проекта](#структура-проекта)
- [Архитектура](#архитектура)
- [Запуск](#запуск)
- [API](#api)
- [Примечания](#примечания)

---

## Стек технологий

| Компонент           | Технология                                      |
|---------------------|-------------------------------------------------|
| Web-фреймворк       | FastAPI 0.115+, Uvicorn                         |
| Очередь задач       | Celery 5, Redis (брокер + backend результатов)  |
| Векторная БД        | Qdrant                                          |
| Реляционная БД      | PostgreSQL 16, SQLAlchemy 2 (asyncpg)           |
| Эмбеддинг-модель    | `paraphrase-multilingual-MiniLM-L12-v2` (384d)  |
| Управление зависим. | uv, pyproject.toml                              |
| Контейнеризация     | Docker, Docker Compose                          |
| Миграции            | Alembic                                         |
| Python              | 3.14                                            |


---

## Структура проекта

```
.
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── ingest.py           # Эндпоинт запуска загрузки данных
│   │       └── search.py           # Эндпоинт семантического поиска
│   ├── core/
│   │   ├── config.py               # Настройки через pydantic-settings
│   │   └── logging.py              # Конфигурация структурированного логирования
│   ├── domain/
│   │   ├── entities.py             # QAPair, VectorPoint — чистые датаклассы
│   │   ├── exceptions.py           # Иерархия доменных ошибок
│   │   └── interfaces/
│   │       ├── data_loader.py      # AbstractDataLoader
│   │       ├── embedder.py         # AbstractEmbedder
│   │       ├── stats_repository.py # AbstractStatsRepository
│   │       └── vector_store.py     # AbstractVectorStore
│   ├── infrastructure/
│   │   ├── csv/
│   │   │   └── data_loader.py      # CsvDataLoader — чтение CSV
│   │   ├── embedder/
│   │   │   └── embedder.py         # SentenceTransformerEmbedder
│   │   ├── postgres/
│   │   │   ├── base.py             # Ленивый движок SQLAlchemy, get_db()
│   │   │   ├── models/
│   │   │   │   └── query_stat.py   # ORM-модель QueryStat
│   │   │   └── repositories/
│   │   │       └── stats.py        # StatsRepository
│   │   └── qdrant/
│   │       └── vector_store.py     # QdrantVectorStore
│   ├── services/
│   │   ├── ingest_service.py       # Инкрементальная синхронизация данных
│   │   └── search_service.py       # Поиск с сохранением статистики
│   ├── tasks/
│   │   ├── celery_app.py           # Экземпляр Celery
│   │   └── ingest_task.py          # Celery-задача ingest_data
│   ├── dependencies.py             # FastAPI Depends-провайдеры
│   └── main.py                     # create_app(), lifespan, обработчики ошибок
├── alembic/
│   ├── env.py                      # Конфигурация Alembic
│   └── versions/
│       └── 3f8a1c2d4e5b_*.py       # Миграция: создание таблицы query_stats
├── data/
│   └── qa_pairs.csv                # Источник данных (разделитель «|»)
├── docker-compose.yml              # Dev-окружение
├── docker-compose.prod.yml         # Prod-оверрайды (включая migrate-сервис)
├── Dockerfile                      # Dev-образ (hot-reload, source mount)
├── Dockerfile.prod                 # Prod-образ (multi-stage, без монтирования)
├── Makefile                        # Основной интерфейс управления
├── pyproject.toml                  # Зависимости и настройки проекта
└── alembic.ini                     # Конфигурация Alembic 
```

---
## Архитектура

Проект реализован по **луковой архитектуре** (Onion Architecture): зависимости направлены строго внутрь, бизнес-логика не зависит от инфраструктуры.

```
┌─────────────────────────────────────────────────────┐
│  Presentation  (app/api/v1)                         │
│  Валидация и маршрутизация                          │
├─────────────────────────────────────────────────────┤
│  Application   (app/services/)                      │
│  IngestService, SearchService — сценарии исп.       │
├─────────────────────────────────────────────────────┤
│  Domain        (app/domain/)                        │
│  Сущности, абстрактные интерфейсы, доменные ошибки  │
├─────────────────────────────────────────────────────┤
│  Infrastructure (app/infrastructure/)               │
│  Конкретные реализации: Qdrant,                     │
│                         PostgreSQL, Embedder, CSV   │
└─────────────────────────────────────────────────────┘
```
---

## Запуск

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

### Требования

- Docker ≥ 24
- Docker Compose ≥ 2.20

### Dev-окружение

В dev-режиме исходный код монтируется в контейнер — изменения применяются без пересборки.
Миграции запускаются вручную командой `make migrate`.

```bash
# 1. Создать .env
cp .env.example .env   # заполнить POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

# 2. Поднять все сервисы
make dev

# 3. В отдельном терминале — применить миграции
make migrate

# 4. Загрузить данные в Qdrant
curl http://localhost:8000/api/v1/ingest

# 5. Проверить поиск
curl -X POST http://localhost:8000/api/v1/search \
     -H "Content-Type: application/json" \
     -d '{"query": "Как получить справку о доходах?"}'
```

### Prod-окружение

В prod-режиме миграции выполняются автоматически отдельным `migrate`-сервисом до старта приложения.

```bash
make prod
```

### Все make-команды

```
make dev           Запустить dev-окружение (hot-reload)
make prod          Запустить prod-окружение
make down          Остановить dev-контейнеры (тома сохраняются)

make migrate       Применить миграции 
make logs          Логи сервиса app
make logs-worker   Логи Celery-воркера
make logs-all      Логи всех сервисов
```

---

## API

Интерактивная документация: [http://localhost:8000/docs](http://localhost:8000/docs)

### `GET /api/v1/ingest`

Ставит в очередь Celery-задачу инкрементальной синхронизации данных из CSV в Qdrant.

**Ответ `200`:**
```json
{
  "task_id": "d98f075f-e9f7-490c-a430-cf7e3ad5bcd0",
  "status": "queued"
}
```

### `POST /api/v1/search`

Семантический поиск по базе вопросов и ответов.

**Тело запроса:**
```json
{ "query": "Как получить справку о доходах?" }
```

**Ответ `200`:**
```json
{
  "results": [
    {
      "question": "Как получить справку о доходах?",
      "answer": "Оформите заявку через HR Portal...",
      "score": 0.92
    }
  ]
}
```

**Коды ошибок:**

| Код | Причина                                |
|-----|----------------------------------------|
| 503 | Qdrant, эмбеддинг-модель или CSV недоступны |
| 500 | Необработанная внутренняя ошибка       |

---

## Примечания


### Синхронные библиотеки в async-контексте

`sentence-transformers` - синхронная. Все вызовы к ней обёрнуты в `asyncio.to_thread()`, что не блокирует event loop и сохраняет конкурентный подход FastAPI.

### Инкрементальный алгоритм ingest

Двухуровневая проверка: UUID5(question) - для идентификации записи, SHA256(question + answer) - для проверки целостности. Эмбеддинги пересчитываются только для новых или изменённых записей. При повторных запусках без изменений данных - ноль вычислений.

### Синглтоны и управление жизненным циклом

**FastAPI**: embedding-модель и `AsyncQdrantClient` создаются один раз через `@lru_cache` - на весь жизненный цикл процесса. Повторная загрузка модели при каждом запросе недопустима по производительности.

**Celery-воркер**: использует сигнал `worker_process_init` - после fork каждого воркер-процесса создаётся выделенный `asyncio` event loop и `AsyncQdrantClient`. Задачи запускаются через `loop.run_until_complete()`, а не `asyncio.run()`: `asyncio.run()` закрывает loop после каждого вызова, что инвалидирует внутренний `httpx`-пул соединений клиента. Постоянный loop позволяет переиспользовать пул — latency повторных задач падает. При завершении процесса `worker_process_shutdown` корректно закрывает клиент и loop.

### Применение миграций

В dev-режиме - `make migrate` (alembic upgrade head внутри контейнера app). В prod - отдельный `migrate`-сервис с `restart: "no"`, который стартует раньше `app` и `worker` через `depends_on: service_completed_successfully`, что делает запуск детерминированным.

### CPU-only PyTorch

Через `[tool.uv.sources]` в `pyproject.toml` подключён индекс `pytorch-cpu`. Образ уменьшается с ~2.5 ГБ до ~250 МБ — GPU в контейнерах не используется.