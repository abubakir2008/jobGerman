# 📦 Models — Документация

Все модели находятся в `app/models/`. Каждая модель = таблица в PostgreSQL.

---

## 📁 Файлы

| Файл             | Таблица(ы)                    |
| ---------------- | ----------------------------- |
| `base.py`        | — (базовый класс + миксин)    |
| `user.py`        | `users`, `candidate_profiles` |
| `job.py`         | `jobs`, `job_categories`      |
| `application.py` | `applications`                |
| `relocation.py`  | `relocation_cases`            |
| `document.py`    | `documents`                   |
| `media.py`       | `media`                       |

---

## 🗂 base.py

**`Base`** — базовый класс для всех моделей (DeclarativeBase).

**`TimestampMixin`** — миксин, добавляет в таблицу два поля:

- `created_at` — дата создания записи
- `updated_at` — дата последнего обновления

Используется во всех моделях.

---

## 👤 user.py

### `User` → таблица `users`

| Поле              | Тип      | Описание                  |
| ----------------- | -------- | ------------------------- |
| `id`              | int      | Первичный ключ            |
| `email`           | str      | Уникальный email (индекс) |
| `hashed_password` | str      | Хэш пароля (bcrypt)       |
| `full_name`       | str      | Полное имя                |
| `role`            | UserRole | Роль пользователя         |
| `is_active`       | bool     | Активен ли аккаунт        |

**Enum `UserRole`:** `candidate` / `manager` / `admin`

**Связи:**

- `profile` → один `CandidateProfile`
- `applications` → список `Application`
- `managed_cases` → список `RelocationCase` (если менеджер)

---

### `CandidateProfile` → таблица `candidate_profiles`

Расширенный профиль кандидата. Создаётся отдельно после регистрации.

| Поле                | Тип           | Описание          |
| ------------------- | ------------- | ----------------- |
| `user_id`           | int           | FK → users        |
| `user_type`         | UserType      | Тип кандидата     |
| `language_level`    | LanguageLevel | Уровень немецкого |
| `experience_years`  | int           | Лет опыта         |
| `profession`        | str           | Профессия         |
| `about`             | text          | О себе            |
| `ready_to_relocate` | bool          | Готов к переезду  |
| `phone`             | str           | Телефон           |
| `country` / `city`  | str           | Местоположение    |

**Enum `UserType`:** `student` / `worker`

**Enum `LanguageLevel`:** `A1` / `A2` / `B1` / `B2` / `C1` / `C2`

> `student` → видит только `seasonal` вакансии
> `worker` → видит только `full_time` вакансии

---

## 💼 job.py

### `JobCategory` → таблица `job_categories`

| Поле          | Тип  | Описание                      |
| ------------- | ---- | ----------------------------- |
| `name`        | str  | Название категории            |
| `slug`        | str  | URL-slug (уникальный, индекс) |
| `description` | text | Описание                      |

---

### `Job` → таблица `jobs`

| Поле              | Тип       | Описание                  |
| ----------------- | --------- | ------------------------- |
| `category_id`     | int       | FK → job_categories       |
| `title`           | str       | Название вакансии         |
| `description`     | text      | Описание                  |
| `requirements`    | text      | Требования                |
| `job_type`        | JobType   | Тип вакансии (индекс)     |
| `status`          | JobStatus | Статус вакансии           |
| `location`        | str       | Город/регион в Германии   |
| `salary_min/max`  | decimal   | Вилка зарплаты            |
| `salary_currency` | str       | Валюта (по умолчанию EUR) |
| `slots`           | int       | Количество мест           |
| `is_active`       | bool      | Активна ли вакансия       |

**Enum `JobType`:** `seasonal` / `full_time`

**Enum `JobStatus`:** `active` / `closed` / `draft`

---

## 📝 application.py

### `Application` → таблица `applications`

Отклик кандидата на вакансию.

| Поле           | Тип               | Описание                |
| -------------- | ----------------- | ----------------------- |
| `candidate_id` | int               | FK → users              |
| `job_id`       | int               | FK → jobs               |
| `status`       | ApplicationStatus | Статус отклика (индекс) |
| `cover_letter` | text              | Сопроводительное письмо |

**Enum `ApplicationStatus`:** `pending` → `reviewing` → `accepted` / `rejected` / `withdrawn`

**Связи:**

- `candidate` → `User`
- `job` → `Job`
- `relocation_case` → один `RelocationCase` (создаётся автоматически)

---

## 🚀 relocation.py

### `RelocationCase` → таблица `relocation_cases`

Кейс сопровождения кандидата. Создаётся автоматически при отклике.

| Поле             | Тип             | Описание                   |
| ---------------- | --------------- | -------------------------- |
| `application_id` | int             | FK → applications (unique) |
| `manager_id`     | int             | FK → users (менеджер)      |
| `stage`          | RelocationStage | Текущий этап (индекс)      |
| `notes`          | text            | Заметки менеджера          |

**Enum `RelocationStage`:**

```
applied → interview → documents → visa → relocation → completed
```

---

## 📄 document.py

### `Document` → таблица `documents`

Документы кандидата. Файл хранится в MinIO, в БД только ссылка.

| Поле           | Тип          | Описание                |
| -------------- | ------------ | ----------------------- |
| `candidate_id` | int          | FK → candidate_profiles |
| `doc_type`     | DocumentType | Тип документа           |
| `file_name`    | str          | Оригинальное имя файла  |
| `file_url`     | str          | Ссылка на файл в MinIO  |
| `file_size`    | int          | Размер в байтах         |
| `mime_type`    | str          | MIME тип файла          |

**Enum `DocumentType`:** `passport` / `cv` / `diploma` / `translation` / `other`

---

## 🎬 media.py

### `Media` → таблица `media`

Обучающий контент для кандидатов (видео, фото, инструкции).

| Поле            | Тип           | Описание                |
| --------------- | ------------- | ----------------------- |
| `title`         | str           | Заголовок               |
| `description`   | text          | Описание                |
| `media_type`    | MediaType     | Тип контента            |
| `category`      | MediaCategory | Категория (индекс)      |
| `file_url`      | str           | Ссылка на файл в MinIO  |
| `file_name`     | str           | Имя файла               |
| `file_size`     | int           | Размер в байтах         |
| `mime_type`     | str           | MIME тип                |
| `thumbnail_url` | str           | Превью (для видео)      |
| `is_published`  | bool          | Опубликован ли материал |

**Enum `MediaType`:** `video` / `image` / `document`

**Enum `MediaCategory`:** `visa` / `interview` / `relocation` / `work_in_germany`
