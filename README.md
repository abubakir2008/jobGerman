# Germany Jobs & Relocation Platform

Платформа для подбора работы в Германии и сопровождения кандидатов на всех этапах — от поиска вакансии до переезда.

---

## Содержание

- [О проекте](#о-проекте)
- [Роли пользователей](#роли-пользователей)
- [Модули системы](#модули-системы)
- [Архитектура](#архитектура)
- [База данных](#база-данных)
- [API](#api)
- [Бизнес-логика](#бизнес-логика)
- [Технологии](#технологии)
- [Запуск проекта](#запуск-проекта)
- [MVP](#mvp)
<<<<<<< HEAD
=======
- [Расширение функционала (v2)](#расширение-функционала-v2)
>>>>>>> 6a22f13 ([ADD] - notification-crud,  checking documents when the client's status changes)

---

## О проекте

Единый сервис, который:

- соединяет кандидатов и работодателей
- разделяет студентов (сезонная работа) и специалистов (полная занятость)
- сопровождает пользователя на каждом этапе — от отклика до трудоустройства
- предоставляет обучающий контент по темам: виза, интервью, переезд, работа в Германии

---

## Роли пользователей

| Роль                    | Описание                                                               |
| ----------------------- | ---------------------------------------------------------------------- |
| **Candidate (Student)** | Соискатель сезонной работы                                             |
| **Candidate (Worker)**  | Соискатель на полную занятость                                         |
| **Manager**             | Ведёт кандидатов по этапам релокации, контролирует документы и статусы |
| **Admin**               | Управляет вакансиями, категориями, пользователями и обучающим контентом |

---

## Модули системы

### 1. Auth Service

- Регистрация и логин
- JWT-авторизация
- Получение текущего пользователя

### 2. User Management

- Список всех пользователей (только Admin)
- Просмотр пользователя по ID
- Изменение роли пользователя

### 3. Candidate Profile

- Создание и редактирование профиля кандидата
- Поля: тип (`student` / `worker`), уровень языка (A1–C2), опыт, готовность к релокации, контакты

### 4. Job Module

- Вакансии и категории
- Фильтрация по типу: `seasonal` / `full_time`, по категории, с пагинацией
- CRUD вакансий и категорий (Admin)

### 5. Application System

- Отклики на вакансии с сопроводительным письмом
- Статусы: `pending` → `reviewing` → `accepted` / `rejected`
- Отзыв заявки кандидатом

### 6. Relocation Case (ключевая логика)

Система сопровождения кандидата по этапам:

```
applied → interview → documents → visa → relocation → completed
```

- При создании отклика автоматически создаётся кейс
- Менеджер ведёт кейс и переводит по этапам
- Добавление заметок

### 7. Documents Module

- Загрузка документов: `passport`, `cv`, `diploma`, `translation`, `visa`, `other`
- Файлы хранятся в MinIO; в БД — только метаданные (URL, размер, MIME)
- Просмотр и удаление

> **v2:** добавлен тип `visa` — требуется для перехода на этап `visa → relocation`

### 8. Media / Learning Module

Обучающий контент:

| Тип              | Категории                                      |
| ---------------- | ---------------------------------------------- |
| `video`          | `visa`, `interview`, `relocation`, `work_in_germany` |
| `image`          | те же категории                                |
| `document`       | те же категории                                |

- Инструкции (текст) и полезные ссылки (JSON)
- Статус публикации (`is_published`)
- Управление — только Admin

---

## Архитектура

```
app/
├── main.py              # FastAPI app, CORS, lifespan (инициализация MinIO)
├── api/
│   └── v1/
│       └── endpoints/   # Роуты: auth, users, profile, jobs, applications,
│                        #        relocation, documents, media
├── config/
│   ├── config.py        # Все настройки через .env (pydantic-settings)
│   ├── database.py      # Async SQLAlchemy, get_db()
│   └── security.py      # JWT, bcrypt
├── dependencies/
│   └── auth.py          # get_current_user(), require_admin(), require_manager()
├── models/              # SQLAlchemy ORM-модели (таблицы БД)
├── schemas/             # Pydantic-схемы (валидация запросов / ответов)
├── service/             # Бизнес-логика
├── repositories/        # CRUD-запросы к БД
└── storage/
    └── minio.py         # Загрузка и удаление файлов в MinIO
```

Архитектурный паттерн: **Router → Service → Repository → Model**

---

## База данных

**PostgreSQL 16** — таблицы:

| Таблица                  | Назначение                                          |
| ------------------------ | --------------------------------------------------- |
| `users`                  | Аккаунты, роли, статус                              |
| `candidate_profiles`     | Профили кандидатов                                  |
| `jobs`                   | Вакансии (тип, статус, зарплата)                    |
| `job_categories`         | Категории вакансий                                  |
| `applications`           | Отклики кандидатов на вакансии                      |
| `relocation_cases`       | Кейсы сопровождения (этапы, менеджер, дедлайн) *v2* |
| `documents`              | Метаданные загруженных документов                   |
| `media`                  | Обучающий контент                                   |
| `case_stage_history`     | История переходов по этапам кейса *v2*              |
| `notifications`          | Уведомления для кандидатов *v2*                     |
| `chat_messages`          | Сообщения чата кандидат ↔ менеджер *v2*             |

**Новые поля в `relocation_cases` (v2):**
- `stage_deadline` — дата дедлайна текущего этапа (Date, nullable)

**Таблица `case_stage_history` (v2):**

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | PK |
| `case_id` | UUID | FK → relocation_cases |
| `stage` | Enum | Этап на который перешли |
| `changed_by` | UUID | FK → users (менеджер) |
| `changed_at` | DateTime | Дата и время перехода |
| `note` | Text | Заметка менеджера при переходе |

**Таблица `notifications` (v2):**

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users (кандидат) |
| `type` | Enum | `stage_change`, `document_required`, `manager_note` |
| `message` | Text | Текст уведомления |
| `is_read` | Bool | Прочитано или нет |
| `created_at` | DateTime | Дата создания |

> Файлы не хранятся в БД. Используется MinIO (S3-совместимое хранилище). В БД хранятся только `file_url` и метаданные.

Миграции: **Alembic** (async-режим).

---

## API

Базовый префикс: `/api/v1`

### Auth

```
POST   /auth/register          Регистрация (возвращает user + JWT)
POST   /auth/login             Логин (возвращает JWT)
GET    /auth/me                Текущий пользователь (требует токен)
```

### Users (только Admin)

```
GET    /users                  Список пользователей (пагинация)
GET    /users/{user_id}        Пользователь по ID
PATCH  /users/{user_id}/role   Изменить роль
```

### Profile

```
GET    /profile/me             Получить профиль кандидата
POST   /profile/me             Создать профиль
PUT    /profile/me             Обновить профиль
```

### Jobs

```
GET    /jobs                   Список вакансий (фильтр по типу, категории, пагинация)
GET    /jobs/{job_id}          Детали вакансии
GET    /jobs/categories        Список категорий
POST   /jobs/categories        Создать категорию (Admin)
POST   /jobs                   Создать вакансию
PATCH  /jobs/{job_id}          Обновить вакансию
DELETE /jobs/{job_id}          Удалить вакансию
```

### Applications

```
GET    /applications                       Мои отклики
GET    /applications/{application_id}      Детали отклика
POST   /applications                       Создать отклик (+ авто-создание RelocationCase)
PATCH  /applications/{id}/status           Изменить статус заявки
POST   /applications/{id}/withdraw         Отозвать заявку
```

### Relocation Cases

```
GET    /cases                              Все кейсы (Manager / Admin)
GET    /cases/my                           Кейсы текущего менеджера
GET    /cases/{case_id}                    Детали кейса
GET    /cases/by-application/{app_id}      Кейс по ID заявки
PATCH  /cases/{case_id}                    Обновить кейс (этап, менеджер, заметки, дедлайн)
POST   /cases/{case_id}/advance            Перевести на следующий этап (с gate-проверкой)
GET    /cases/{case_id}/requirements       Чеклист требований для следующего этапа (v2)
GET    /cases/{case_id}/history            История переходов по этапам (v2)
```

### Documents

```
GET    /documents                          Мои документы (фильтр по типу)
POST   /documents/upload                   Загрузить документ (multipart)
DELETE /documents/{document_id}            Удалить документ
```

### Media

```
GET    /media                              Список опубликованного контента (фильтр по типу/категории)
GET    /media/{media_id}                   Детали: инструкции + ссылки
POST   /media/upload                       Загрузить контент (Admin, multipart)
PATCH  /media/{media_id}                   Обновить метаданные (Admin)
DELETE /media/{media_id}                   Удалить контент (Admin)
```

### Notifications (v2)

```
GET    /notifications                      Мои уведомления (кандидат)
POST   /notifications/{id}/read            Отметить уведомление прочитанным
```

### Chat — WebSocket (v2)

```
WS     /ws/chat/{case_id}                  Реал-тайм чат (кандидат ↔ менеджер)
GET    /chat/{case_id}/messages            История сообщений (с пагинацией)
POST   /chat/{case_id}/messages/read       Отметить все сообщения прочитанными
```

> Доступ к чату имеют только кандидат кейса и назначенный менеджер. Остальные получают `403 Forbidden`.

### Health

```
GET    /health                             {"status": "ok", "version": "0.1.0"}
```

---

## Бизнес-логика

**Разделение кандидатов по типу:**

- `student` → видит только `seasonal` вакансии
- `worker` → видит только `full_time` вакансии

**Жизненный цикл отклика:**

1. Кандидат создаёт `Application` (статус `pending`)
2. Автоматически создаётся `RelocationCase` (этап `applied`)
3. Менеджер назначается на кейс
4. Менеджер переводит кейс по этапам: `interview` → `documents` → `visa` → `relocation` → `completed`

**Gate-проверки при переходе между этапами (v2):**

| Переход | Обязательное условие |
|--------|----------------------|
| `applied → interview` | Заявка в статусе `reviewing` или `accepted` |
| `interview → documents` | Менеджер добавил заметку (подтверждение интервью) |
| `documents → visa` | Загружены документы: `passport`, `cv`, `diploma` |
| `visa → relocation` | Загружен документ типа `visa` |
| `relocation → completed` | Менеджер явно подтверждает финал (`"confirm": true` в теле запроса) |

При нарушении условия → `400 Bad Request`:
```json
{ "detail": "Required documents missing: visa" }
```

Логика вынесена в `service/relocation_service.py` → функция `check_stage_requirements(case_id, next_stage)`.

**Документы:**

- Только кандидат видит и удаляет свои документы
- Файл удаляется из MinIO при удалении записи из БД

---

## Технологии

| Слой              | Технология                         |
| ----------------- | ---------------------------------- |
| **Framework**     | FastAPI + Uvicorn                  |
| **Язык**          | Python 3.11+                       |
| **ORM**           | SQLAlchemy 2.0 (async)             |
| **БД**            | PostgreSQL 16                      |
| **Миграции**      | Alembic                            |
| **Авторизация**   | JWT (python-jose) + bcrypt         |
| **Хранилище**     | MinIO (S3-совместимое)             |
| **Валидация**     | Pydantic v2                        |
| **Async драйвер** | asyncpg                            |
| **Контейнеры**    | Docker + Docker Compose            |
| **Тесты**         | pytest + pytest-asyncio            |
| **Линтер**        | ruff                               |

---

## Запуск проекта

### Требования

- Docker + Docker Compose

### Первый запуск

```bash
cp .env.example .env
# Заполните .env при необходимости
docker-compose up --build
```

### Последующие запуски

```bash
docker-compose up
```

### Миграции (если нужно применить вручную)

```bash
docker-compose exec app alembic upgrade head
```

### Остановка

```bash
docker-compose down
```

### Полезные ссылки

| Сервис           | URL                           |
| ---------------- | ----------------------------- |
| API документация | http://localhost:8000/docs    |
| Redoc            | http://localhost:8000/redoc   |
| MinIO консоль    | http://localhost:9001         |

---

## MVP

Минимальный рабочий набор функций:

- [x] Регистрация и авторизация (JWT)
- [x] Управление пользователями (Admin)
- [x] Создание и редактирование профиля кандидата
- [x] Вакансии и категории (CRUD)
- [x] Отклики на вакансии
- [x] Система relocation-кейсов с этапами
- [x] Загрузка и хранение документов (MinIO)
- [x] Обучающий медиаконтент (видео, изображения, документы)
- [x] Docker-окружение (app + PostgreSQL + MinIO)

---

<<<<<<< HEAD
=======
---

## Расширение функционала (v2)

Все изменения помечены тегом **v2** в соответствующих разделах выше. Ниже — сводная таблица по приоритетам.

### P0 — Gate-проверки при переходе этапов

**Затронутые файлы:**

| Файл | Изменение |
|------|-----------|
| `models/document.py` | Добавить значение `visa` в enum типов документов |
| `service/relocation_service.py` | Новая функция `check_stage_requirements(case_id, next_stage)` |
| `api/v1/endpoints/relocation.py` | Вызов проверки перед `advance`, возврат `400` с деталями |

**Алгоритм `check_stage_requirements`:**
```
documents → visa:
  проверить наличие документов passport + cv + diploma у кандидата этого кейса
  если хотя бы одного нет → raise HTTPException(400, "Required documents missing: ...")

visa → relocation:
  проверить наличие документа типа visa
  если нет → raise HTTPException(400, "Required documents missing: visa")

relocation → completed:
  проверить поле confirm=true в теле запроса
  если нет → raise HTTPException(400, "Explicit confirmation required")
```

---
>>>>>>> 6a22f13 ([ADD] - notification-crud,  checking documents when the client's status changes)

### P1 — Чеклист требований `GET /cases/:id/requirements`

**Новый эндпоинт** — возвращает список требований для перехода на следующий этап.

**Ответ:**
```json
{
  "current_stage": "documents",
  "next_stage": "visa",
  "can_advance": false,
  "requirements": [
    { "key": "passport", "label": "Паспорт", "done": true },
    { "key": "cv",       "label": "CV",      "done": true },
    { "key": "diploma",  "label": "Диплом",  "done": false }
  ]
}
```

**Затронутые файлы:**
- `service/relocation_service.py` — функция `get_stage_requirements(case_id)`
- `api/v1/endpoints/relocation.py` — новый роут `GET /cases/{case_id}/requirements`
- `schemas/relocation.py` — схема `StageRequirementsResponse`

---

### P1 — История этапов `GET /cases/:id/history`

**Новая таблица** `case_stage_history` + эндпоинт.

**Затронутые файлы:**
- `models/case_stage_history.py` — новая ORM-модель
- `repositories/case_history_repository.py` — `create_history_entry`, `get_history_by_case`
- `service/relocation_service.py` — вызов `create_history_entry` при каждом `advance`
- `api/v1/endpoints/relocation.py` — новый роут `GET /cases/{case_id}/history`
- `schemas/relocation.py` — схема `CaseHistoryItem`
- Alembic-миграция

---

### P2 — Дедлайн этапа

**Поле `stage_deadline`** в таблице `relocation_cases`.

Менеджер при обновлении кейса передаёт:
```json
PATCH /cases/:id
{ "stage_deadline": "2025-06-15" }
```

**Затронутые файлы:**
- `models/relocation_case.py` — поле `stage_deadline: Date | None`
- `schemas/relocation.py` — поле в `RelocationCaseUpdate` и `RelocationCaseResponse`
- Alembic-миграция

---

### P2 — WebSocket Чат

**Новая таблица** `chat_messages` + WebSocket-соединение + REST для истории.

**Таблица `chat_messages`:**

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | PK |
| `case_id` | UUID | FK → relocation_cases |
| `sender_id` | UUID | FK → users |
| `message` | Text | Текст сообщения |
| `is_read` | Bool | Прочитано получателем |
| `created_at` | DateTime | Время отправки |

**WebSocket-протокол (`WS /ws/chat/{case_id}`):**

Авторизация через query-параметр: `?token=<JWT>`

Входящее сообщение от клиента:
```json
{ "message": "Здравствуйте, когда интервью?" }
```

Исходящее сообщение всем участникам чата:
```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "sender_name": "Азиз Каримов",
  "sender_role": "candidate",
  "message": "Здравствуйте, когда интервью?",
  "created_at": "2025-06-01T10:30:00Z"
}
```

**Менеджер видит непрочитанные** — счётчик `unread_count` в списке кейсов.

**Затронутые файлы:**
- `models/chat_message.py` — ORM-модель
- `repositories/chat_repository.py` — `save_message`, `get_messages`, `mark_read`
- `service/chat_service.py` — бизнес-логика, проверка доступа
- `api/v1/endpoints/chat.py` — WebSocket-роут + REST-эндпоинты
- `main.py` — подключить роутер `/chat` и WebSocket
- Alembic-миграция

---

### P2 — Уведомления

**Новая таблица** `notifications` + два эндпоинта.

Уведомления создаются автоматически при:
- Смене этапа (`stage_change`)
- Необходимости загрузить документы (`document_required`)
- Заметке менеджера (`manager_note`)

**Затронутые файлы:**
- `models/notification.py` — новая ORM-модель
- `repositories/notification_repository.py` — `create`, `get_by_user`, `mark_read`
- `service/notification_service.py` — `notify_candidate(user_id, type, message)`
- `service/relocation_service.py` — вызов `notify_candidate` при `advance`
- `api/v1/endpoints/notifications.py` — новый роутер
- `schemas/notification.py` — схемы
- `main.py` — подключить роутер `/notifications`
- Alembic-миграция

---

### Порядок реализации v2

```
1.  Добавить тип visa в Document enum + миграция
2.  Реализовать check_stage_requirements в сервисе
3.  Подключить gate-проверки в /advance
4.  Добавить GET /cases/:id/requirements
5.  Создать модель + репозиторий case_stage_history + миграция
6.  Добавить GET /cases/:id/history
7.  Добавить поле stage_deadline + миграция
8.  Создать модель chat_message + репозиторий + миграция
9.  Реализовать WebSocket WS /ws/chat/{case_id}
10. Добавить REST GET /chat/:id/messages + POST .../read
11. Создать модель + сервис notifications + миграция
12. Подключить роутер /notifications
```

---

MIT © 2025 Germany Jobs Platform
