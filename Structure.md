# 📁 Структура проекта

```
germany-jobs/
├── app/
│   ├── main.py                  # Точка входа. FastAPI app, CORS, lifespan
│   │
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/       # Роуты (auth, jobs, profile, и т.д.)
│   │
│   ├── core/
│   │   ├── config.py            # Все настройки через .env (pydantic-settings)
│   │   ├── database.py          # Подключение к PostgreSQL, get_db()
│   │   └── security.py          # JWT токены, хэширование паролей
│   │
│   ├── models/                  # SQLAlchemy модели (таблицы БД)
│   │
│   ├── schemas/                 # Pydantic схемы (валидация запросов/ответов)
│   │
│   ├── services/                # Бизнес-логика
│   │
│   ├── repositories/            # Запросы к БД (CRUD)
│   │
│   └── storage/
│       └── minio.py             # Клиент MinIO: upload, delete файлов
│
├── alembic/
│   ├── env.py                   # Конфиг миграций (async)
│   └── versions/                # Файлы миграций
│
├── .env                         # Переменные окружения (не в git)
├── .env.example                 # Шаблон .env
├── .gitignore
├── alembic.ini                  # Конфиг Alembic
├── docker-compose.yml           # Запуск app + PostgreSQL + MinIO
├── Dockerfile                   # Сборка образа приложения
└── pyproject.toml               # Зависимости (Poetry)
```

---

## 🔍 Что за что отвечает

### `app/main.py`

Создаёт FastAPI приложение. Здесь подключаются роуты, CORS и lifespan (запуск/остановка — например инициализация MinIO bucket).

### `app/core/config.py`

Читает переменные из `.env` файла. Все настройки проекта в одном месте — DATABASE_URL, SECRET_KEY, параметры MinIO и т.д.

### `app/core/database.py`

Асинхронное подключение к PostgreSQL через SQLAlchemy. Экспортирует `get_db()` — dependency для FastAPI эндпоинтов.

### `app/core/security.py`

Две вещи: хэширование паролей через bcrypt и работа с JWT токенами (создание и проверка).

### `app/models/`

SQLAlchemy модели = таблицы в базе данных. Каждая модель — отдельный файл (`user.py`, `job.py` и т.д.).

### `app/schemas/`

Pydantic схемы для валидации данных. Отдельно для запросов (`UserCreate`) и ответов (`UserResponse`). Это то, что видит клиент.

### `app/repositories/`

Весь код работы с БД (SELECT, INSERT, UPDATE, DELETE). Сервисы не пишут SQL напрямую — они вызывают репозитории.

### `app/services/`

Бизнес-логика. Например: при отклике на вакансию автоматически создаётся `RelocationCase` и назначается менеджер. Это происходит здесь.

### `app/api/v1/endpoints/`

FastAPI роуты. Каждый модуль — отдельный файл (`auth.py`, `jobs.py`, `profile.py`). Роуты только принимают запрос и вызывают сервис.

### `app/storage/minio.py`

Клиент для работы с MinIO (аналог S3). Загрузка и удаление файлов. В БД хранится только ссылка на файл, сам файл — в MinIO.

### `alembic/`

Система миграций БД. Каждое изменение модели — новая миграция. Так БД всегда синхронизирована с кодом.

---

## ⚙️ Переменные окружения (`.env`)

| Переменная          | Описание                        |
| ------------------- | ------------------------------- |
| `SECRET_KEY`        | Секрет для подписи JWT токенов  |
| `DATABASE_URL`      | Строка подключения к PostgreSQL |
| `MINIO_ENDPOINT`    | Адрес MinIO сервера             |
| `MINIO_ACCESS_KEY`  | Логин MinIO                     |
| `MINIO_SECRET_KEY`  | Пароль MinIO                    |
| `MINIO_BUCKET_NAME` | Название bucket для файлов      |
| `DEBUG`             | Режим отладки (True/False)      |

---

## 🐳 Docker сервисы

| Сервис  | Порт   | Описание               |
| ------- | ------ | ---------------------- |
| `app`   | `8000` | FastAPI приложение     |
| `db`    | `5432` | PostgreSQL база данных |
| `minio` | `9000` | MinIO API              |
| `minio` | `9001` | MinIO веб-консоль      |

---

## 🚀 Запуск

```bash
# Первый запуск
cp .env.example .env
docker-compose up --build

# Последующие запуски
docker-compose up

# Остановка
Ctrl+C
# или
docker-compose down
```

API документация: `http://localhost:8000/docs`
MinIO консоль: `http://localhost:9001`
