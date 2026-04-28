# E2E Test Report — EduBridge Backend

**Дата:** 2026-04-28  
**Версия сервера:** 0.1.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Результат:** ✅ 79 / 79 тестов прошли

---

## Сводка

| Секция | Тестов | Статус |
|--------|--------|--------|
| 1. AUTH | 11 | ✅ |
| 2. ADMIN — Пользователи | 8 | ✅ |
| 3. PROFILE | 6 | ✅ |
| 4. JOBS | 12 | ✅ |
| 5. APPLICATIONS | 12 | ✅ |
| 6. RELOCATION CASES | 18 | ✅ |
| 7. NOTIFICATIONS | 6 | ✅ |
| 8. CHAT | 6 | ✅ |
| **Итого** | **79** | **✅ 0 failed** |

---

## 1. AUTH

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Регистрация worker | `POST /auth/register` | 201 | ✅ |
| 2 | Регистрация student | `POST /auth/register` | 201 | ✅ |
| 3 | Регистрация будущего менеджера | `POST /auth/register` | 201 | ✅ |
| 4 | Дубликат email | `POST /auth/register` | 400 | ✅ |
| 5 | Логин worker | `POST /auth/login` | 200 | ✅ |
| 6 | Логин вернул access_token | `POST /auth/login` | — | ✅ |
| 7 | Неверный пароль | `POST /auth/login` | 401 | ✅ |
| 8 | GET /auth/me с токеном | `GET /auth/me` | 200 | ✅ |
| 9 | Роль по умолчанию: candidate | `GET /auth/me` | — | ✅ |
| 10 | GET /auth/me без токена | `GET /auth/me` | 403 | ✅ |
| 11 | Логин admin | `POST /auth/login` | 200 | ✅ |

---

## 2. ADMIN — Пользователи

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Список пользователей (admin) | `GET /users` | 200 | ✅ |
| 2 | Пользователей в БД | `GET /users` | — | ✅ |
| 3 | Список пользователей (не-admin) | `GET /users` | 403 | ✅ |
| 4 | Получить пользователя по ID | `GET /users/{id}` | 200 | ✅ |
| 5 | Пользователь не найден | `GET /users/99999` | 404 | ✅ |
| 6 | Повышение роли до manager | `PATCH /users/{id}/role` | 200 | ✅ |
| 7 | Роль успешно изменена | `PATCH /users/{id}/role` | — | ✅ |
| 8 | Повышение несуществующего | `PATCH /users/99999/role` | 404 | ✅ |

---

## 3. PROFILE

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Создание профиля worker | `POST /profile/me` | 201 | ✅ |
| 2 | Создание профиля student | `POST /profile/me` | 201 | ✅ |
| 3 | Дубликат профиля | `POST /profile/me` | 400 | ✅ |
| 4 | Получить профиль | `GET /profile/me` | 200 | ✅ |
| 5 | Обновить профиль | `PUT /profile/me` | 200 | ✅ |
| 6 | language_level обновлён до B2 | `PUT /profile/me` | — | ✅ |

---

## 4. JOBS

> Все эндпоинты вакансий работают **без авторизации** (публичные).

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Создание категории | `POST /jobs/categories` | 201 | ✅ |
| 2 | Список категорий | `GET /jobs/categories` | 200 | ✅ |
| 3 | Создание seasonal вакансии | `POST /jobs` | 201 | ✅ |
| 4 | Создание full_time вакансии | `POST /jobs` | 201 | ✅ |
| 5 | Список вакансий | `GET /jobs` | 200 | ✅ |
| 6 | Найдено вакансий в БД | `GET /jobs` | — | ✅ |
| 7 | Фильтр по seasonal | `GET /jobs?job_type=seasonal` | 200 | ✅ |
| 8 | Корректность фильтра seasonal | `GET /jobs?job_type=seasonal` | — | ✅ |
| 9 | Фильтр по full_time | `GET /jobs?job_type=full_time` | 200 | ✅ |
| 10 | Получить вакансию по ID | `GET /jobs/{id}` | 200 | ✅ |
| 11 | Вакансия не найдена | `GET /jobs/99999` | 404 | ✅ |
| 12 | Обновить вакансию | `PATCH /jobs/{id}` | 200 | ✅ |

---

## 5. APPLICATIONS

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Отклик worker на full_time | `POST /applications` | 201 | ✅ |
| 2 | RelocationCase создан автоматически | `POST /applications` | — | ✅ |
| 3 | Начальный этап: applied | `POST /applications` | — | ✅ |
| 4 | Отклик student на seasonal | `POST /applications` | 201 | ✅ |
| 5 | Дубликат отклика | `POST /applications` | 400 | ✅ |
| 6 | Список откликов | `GET /applications` | 200 | ✅ |
| 7 | Количество откликов | `GET /applications` | — | ✅ |
| 8 | Получить отклик по ID | `GET /applications/{id}` | 200 | ✅ |
| 9 | Изменить статус → reviewing | `PATCH /applications/{id}/status` | 200 | ✅ |
| 10 | Статус заявки: reviewing | `PATCH /applications/{id}/status` | — | ✅ |
| 11 | Отозвать student отклик | `PATCH /applications/{id}/status` | 200 | ✅ |
| 12 | Статус изменён на withdrawn | `PATCH /applications/{id}/status` | — | ✅ |

---

## 6. RELOCATION CASES

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Кандидат GET /cases | `GET /cases` | 403 | ✅ |
| 2 | Менеджер GET /cases | `GET /cases` | 200 | ✅ |
| 3 | GET /cases/my (кандидат) | `GET /cases/my` | 200 | ✅ |
| 4 | Получить кейс по ID | `GET /cases/{id}` | 200 | ✅ |
| 5 | Кейс по application ID | `GET /cases/by-application/{app_id}` | 200 | ✅ |
| 6 | Требования для следующего этапа | `GET /cases/{id}/requirements` | 200 | ✅ |
| 7 | Текущий applied, следующий interview | `GET /cases/{id}/requirements` | — | ✅ |
| 8 | Advance: applied → interview | `POST /cases/{id}/advance` | 200 | ✅ |
| 9 | Этап изменён на interview | `POST /cases/{id}/advance` | — | ✅ |
| 10 | interview→documents без заметок | `POST /cases/{id}/advance` | 400 | ✅ |
| 11 | PATCH /cases/{id} — добавить заметки | `PATCH /cases/{id}` | 200 | ✅ |
| 12 | Advance: interview → documents | `POST /cases/{id}/advance` | 200 | ✅ |
| 13 | Этап изменён на documents | `POST /cases/{id}/advance` | — | ✅ |
| 14 | documents→visa без документов | `POST /cases/{id}/advance` | 400 | ✅ |
| 15 | Неверный переход этапа | `PATCH /cases/{id}` | 400 | ✅ |
| 16 | История этапов | `GET /cases/{id}/history` | 200 | ✅ |
| 17 | Записей в истории: 2 | `GET /cases/{id}/history` | — | ✅ |
| 18 | Кейс не найден | `GET /cases/99999` | 404 | ✅ |

---

## 7. NOTIFICATIONS

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Список уведомлений | `GET /notifications` | 200 | ✅ |
| 2 | Количество уведомлений: 2 | `GET /notifications` | — | ✅ |
| 3 | Отметить уведомление прочитанным | `POST /notifications/{id}/read` | 200 | ✅ |
| 4 | Отметить все прочитанными | `POST /notifications/read-all` | 200 | ✅ |
| 5 | Все уведомления прочитаны | `POST /notifications/read-all` | — | ✅ |
| 6 | GET /notifications без токена | `GET /notifications` | 403 | ✅ |

---

## 8. CHAT

| # | Тест | Endpoint | Ожидаемый статус | Результат |
|---|------|----------|-----------------|-----------|
| 1 | Сообщения чата | `GET /chat/{case_id}/messages` | 200 | ✅ |
| 2 | Сообщений в чате: 0 | `GET /chat/{case_id}/messages` | — | ✅ |
| 3 | Пагинация сообщений | `GET /chat/{case_id}/messages?limit=10&offset=0` | 200 | ✅ |
| 4 | Отметить сообщения прочитанными | `POST /chat/{case_id}/messages/read` | 200 | ✅ |
| 5 | GET /chat без токена | `GET /chat/{case_id}/messages` | 403 | ✅ |

---

## Покрытые эндпоинты

| Метод | Путь | Секция |
|-------|------|--------|
| `POST` | `/auth/register` | AUTH |
| `POST` | `/auth/login` | AUTH |
| `GET` | `/auth/me` | AUTH |
| `GET` | `/users` | ADMIN |
| `GET` | `/users/{id}` | ADMIN |
| `PATCH` | `/users/{id}/role` | ADMIN |
| `POST` | `/profile/me` | PROFILE |
| `GET` | `/profile/me` | PROFILE |
| `PUT` | `/profile/me` | PROFILE |
| `POST` | `/jobs/categories` | JOBS |
| `GET` | `/jobs/categories` | JOBS |
| `POST` | `/jobs` | JOBS |
| `GET` | `/jobs` | JOBS |
| `GET` | `/jobs/{id}` | JOBS |
| `PATCH` | `/jobs/{id}` | JOBS |
| `POST` | `/applications` | APPLICATIONS |
| `GET` | `/applications` | APPLICATIONS |
| `GET` | `/applications/{id}` | APPLICATIONS |
| `PATCH` | `/applications/{id}/status` | APPLICATIONS |
| `GET` | `/cases` | RELOCATION |
| `GET` | `/cases/my` | RELOCATION |
| `GET` | `/cases/{id}` | RELOCATION |
| `GET` | `/cases/by-application/{app_id}` | RELOCATION |
| `GET` | `/cases/{id}/requirements` | RELOCATION |
| `POST` | `/cases/{id}/advance` | RELOCATION |
| `PATCH` | `/cases/{id}` | RELOCATION |
| `GET` | `/cases/{id}/history` | RELOCATION |
| `GET` | `/notifications` | NOTIFICATIONS |
| `POST` | `/notifications/{id}/read` | NOTIFICATIONS |
| `POST` | `/notifications/read-all` | NOTIFICATIONS |
| `GET` | `/chat/{case_id}/messages` | CHAT |
| `POST` | `/chat/{case_id}/messages/read` | CHAT |
| `GET` | `/health` | — |

---

## Проверенные бизнес-правила

- Новый пользователь получает роль `candidate` по умолчанию
- Только `admin` может менять роли пользователей
- Вакансии доступны без авторизации
- При создании отклика автоматически создаётся `RelocationCase` с этапом `applied`
- Переход `applied → interview` требует статус заявки `reviewing` или `accepted`
- Переход `interview → documents` требует наличия заметок у кейса
- Переход `documents → visa` требует загруженных документов (passport, cv, diploma)
- Произвольный переход этапов возвращает `400`
- Уведомления создаются автоматически при изменении этапа кейса
- Все защищённые эндпоинты возвращают `403` без токена (`HTTPBearer`)
