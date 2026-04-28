# Структура проекта

```
server/
├── app/
│   ├── main.py                               # FastAPI app, CORS, lifespan (инициализация MinIO)
│   │
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── router.py                 # Регистрация всех роутеров
│   │           ├── auth_router.py            # POST /auth/register, /login; GET /auth/me
│   │           ├── user_router.py            # GET/PATCH /users (Admin)
│   │           ├── profile_router.py         # GET/POST/PUT /profile/me
│   │           ├── job_router.py             # CRUD /jobs и /jobs/categories
│   │           ├── application_router.py     # Отклики на вакансии
│   │           ├── relocation_router.py      # Кейсы сопровождения /cases
│   │           ├── document_router.py        # Загрузка документов /documents
│   │           └── media_router.py           # Обучающий контент /media
│   │
│   ├── config/
│   │   ├── config.py                         # Настройки через .env (pydantic-settings)
│   │   ├── database.py                       # Async SQLAlchemy, get_db()
│   │   └── security.py                       # JWT токены, bcrypt хэширование
│   │
│   ├── dependencies/
│   │   └── auth.py                           # get_current_user(), require_admin(), require_manager()
│   │
│   ├── models/                               # SQLAlchemy ORM-модели (таблицы БД)
│   │   ├── base.py                           # Base + TimestampMixin (created_at, updated_at)
│   │   ├── user.py                           # User, CandidateProfile
│   │   ├── job.py                            # Job, JobCategory
│   │   ├── application.py                    # Application
│   │   ├── relocation.py                     # RelocationCase
│   │   ├── document.py                       # Document
│   │   ├── media.py                          # Media
│   │   └── models_docs.md                    # Документация по моделям
│   │
│   ├── schemas/                              # Pydantic-схемы (валидация запросов / ответов)
│   │   ├── auth.py                           # Token, LoginRequest, RegisterRequest
│   │   ├── user.py                           # UserCreate, UserResponse, RoleUpdate
│   │   ├── profile.py                        # ProfileCreate, ProfileUpdate, ProfileResponse
│   │   ├── job.py                            # JobCreate, JobUpdate, JobResponse, CategoryCreate
│   │   ├── appliction.py                     # ApplicationCreate, ApplicationResponse, StatusUpdate
│   │   ├── relocation.py                     # CaseUpdate, CaseResponse
│   │   ├── document.py                       # DocumentResponse
│   │   └── media.py                          # MediaCreate, MediaUpdate, MediaResponse
│   │
│   ├── service/                              # Бизнес-логика
│   │   ├── auth_service.py
│   │   ├── profile_service.py
│   │   ├── job_service.py
│   │   ├── application_service.py            # При отклике авто-создаёт RelocationCase
│   │   ├── relocation_service.py
│   │   ├── document_service.py
│   │   └── media_service.py
│   │
│   ├── repositories/                         # CRUD-запросы к БД (Data Access Layer)
│   │   ├── user_repository.py
│   │   ├── profeli_repository.py
│   │   ├── job_repositore.py
│   │   ├── application_repository.py
│   │   ├── relocation_repository.py
│   │   ├── document_repository.py
│   │   └── media_repository.py
│   │
│   └── storage/
│       └── minio.py                          # MinIO клиент: upload, delete файлов
│
├── alembic/
│   ├── env.py                                # Async конфиг миграций
│   └── versions/
│       └── 7eafcd7b2d4b_initial.py           # Начальная миграция (все таблицы)
│
├── .env                                      # Переменные окружения (не в git)
├── .gitignore
├── alembic.ini                               # Конфиг Alembic
├── docker-compose.yml                        # Оркестрация: app + PostgreSQL + MinIO
├── dockerfile                                # Сборка образа приложения
└── pyproject.toml                            # Зависимости (Poetry)
```

---

## Что за что отвечает

### `app/main.py`

Создаёт FastAPI приложение, подключает роутер, настраивает CORS и lifespan — при старте приложения создаётся MinIO bucket, если его нет.

### `app/config/config.py`

Читает переменные из `.env` через pydantic-settings. Все настройки (DATABASE_URL, SECRET_KEY, MinIO) в одном месте.

### `app/config/database.py`

Async подключение к PostgreSQL через SQLAlchemy + asyncpg. Экспортирует `get_db()` — dependency для FastAPI эндпоинтов.

### `app/config/security.py`

Хэширование паролей через bcrypt и работа с JWT токенами (создание и верификация).

### `app/dependencies/auth.py`

FastAPI dependencies:
- `get_current_user()` — декодирует JWT и возвращает текущего пользователя
- `require_admin()` — разрешает только роль `admin`
- `require_manager()` — разрешает роли `manager` и `admin`

### `app/models/`

SQLAlchemy ORM-модели = таблицы в БД. Каждая модель в отдельном файле. `base.py` содержит `TimestampMixin` — добавляет `created_at` / `updated_at` ко всем моделям.

### `app/schemas/`

Pydantic v2-схемы для валидации. Разделены на Request-схемы (`Create`, `Update`) и Response-схемы. Это контракт API для клиента.

### `app/repositories/`

Весь SQL-код (SELECT, INSERT, UPDATE, DELETE). Сервисы не пишут запросы напрямую — только через репозитории.

### `app/service/`

Бизнес-логика. Пример: при отклике на вакансию `application_service` создаёт `Application` и сразу `RelocationCase`. Сервисы вызывают репозитории и оркестрируют операции.

### `app/api/v1/endpoints/`

FastAPI роутеры. Каждый модуль — отдельный файл. Роут только принимает запрос, валидирует схему и вызывает сервис.

### `app/storage/minio.py`

Клиент для MinIO (S3-совместимое хранилище). Загружает файлы и удаляет. В БД хранится только `file_url` и метаданные — сам файл только в MinIO.

### `alembic/`

Система миграций БД. Каждое изменение модели — новая версия. `env.py` настроен для async-режима.

---

## Переменные окружения (`.env`)

| Переменная                   | Описание                                     |
| ---------------------------- | -------------------------------------------- |
| `SECRET_KEY`                 | Секрет для подписи JWT токенов               |
| `ALGORITHM`                  | Алгоритм JWT (default: HS256)                |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Срок жизни токена в минутах (default: 30)    |
| `DATABASE_URL`               | postgresql+asyncpg://user:pass@host/dbname   |
| `MINIO_ENDPOINT`             | Адрес MinIO (default: minio:9000)            |
| `MINIO_ACCESS_KEY`           | Логин MinIO                                  |
| `MINIO_SECRET_KEY`           | Пароль MinIO                                 |
| `MINIO_BUCKET_NAME`          | Название bucket для файлов                   |
| `MINIO_USE_SSL`              | Использовать SSL (default: False)            |
| `DEBUG`                      | Режим отладки (True / False)                 |
| `APP_NAME`                   | Название приложения                          |
| `APP_VERSION`                | Версия приложения                            |

---

## Docker сервисы

| Сервис  | Контейнер              | Порт(ы)      | Назначение             |
| ------- | ---------------------- | ------------ | ---------------------- |
| `app`   | germany_jobs_app       | `8000`       | FastAPI (hot reload)   |
| `db`    | germany_jobs_db        | `5432`       | PostgreSQL 16          |
| `minio` | germany_jobs_minio     | `9000`, `9001` | MinIO API + консоль  |

Все сервисы имеют health check — зависимые сервисы запускаются только после готовности зависимостей.

---

## Запуск

```bash
# Первый запуск
cp .env.example .env
docker-compose up --build

# Последующие запуски
docker-compose up

# Применить миграции вручную
docker-compose exec app alembic upgrade head

# Остановка
docker-compose down
```

| Сервис           | URL                        |
| ---------------- | -------------------------- |
| API документация | http://localhost:8000/docs |
| Redoc            | http://localhost:8000/redoc |
| MinIO консоль    | http://localhost:9001      |

---

## Поток данных (пример: отклик на вакансию)

```
POST /api/v1/applications
        │
        ▼
application_router.py       ← валидация схемы ApplicationCreate
        │
        ▼
application_service.py      ← бизнес-логика:
        │                      1. создать Application
        │                      2. создать RelocationCase (этап: applied)
        ▼
application_repository.py   ← INSERT в таблицы applications + relocation_cases
relocation_repository.py
        │
        ▼
PostgreSQL (asyncpg)
```
