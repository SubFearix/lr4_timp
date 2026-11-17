# Безопасность образовательного учреждения — система учёта

Веб-приложение с функционалом отчёта ЛР4 (вариант 17 «Безопасность в
охранной деятельности»), переосмысленным под тему «Безопасность
образовательного учреждения»: те же сущности и архитектура (FastAPI +
PostgreSQL бэкенд, React SPA фронтенд, JWT-аутентификация с access +
refresh токенами, настоящая двухфакторная аутентификация одноразовым
кодом по почте, bcrypt-хеширование паролей, пагинация и фильтрация
списков, Docker + docker-compose, CI на GitHub Actions), но термины,
типы объектов/инцидентов и примеры — про школу, а не охранную компанию.

## Структура проекта

```
lr4/
├── backend/                 # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── main.py          # точка входа, CORS, обработчики ошибок
│   │   ├── models.py        # SQLAlchemy-модели (7 сущностей)
│   │   ├── schemas.py       # Pydantic-схемы запросов/ответов
│   │   ├── auth.py          # bcrypt + JWT (access/refresh/pending-2FA)
│   │   ├── otp.py           # генерация/хеширование OTP-кода, отправка письма (SMTP)
│   │   ├── permissions.py   # ролевая модель (admin/operator/user)
│   │   ├── migrations.py    # лёгкие ALTER/CREATE IF NOT EXISTS для апгрейда БД
│   │   ├── crud_router.py   # generic CRUD-роутер (список/CRUD/пагинация/права)
│   │   ├── pagination.py
│   │   └── routers/         # роутеры по сущностям + доп. фильтры
│   ├── db/init.sql          # DDL для ручного/docker-compose разворачивания
│   ├── tests/                # pytest, 23 теста, изолированная SQLite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── api/axios.js      # JWT-интерцептор, авто-refresh, тосты об ошибках
│   │   ├── context/AuthContext.js  # login/register/verifyOtp/resendOtp
│   │   ├── components/EntityCrudPage.js  # generic список+форма+пагинация
│   │   └── pages/             # Login, VerifyOtp, Register, Profile, Incidents, ...
│   ├── nginx.conf            # прод-прокси /api/ → backend:8000
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── .github/workflows/tests.yml
```

## Быстрый запуск (Docker)

```bash
cp .env.example .env      # при желании поменяйте пароли/секрет
docker compose up --build
```

- Фронтенд: http://localhost
- Бэкенд / Swagger-документация: http://localhost:8000/docs
- PostgreSQL: localhost:5432 (данные сохраняются в volume `db_data`)

При первом запуске `backend/db/init.sql` создаёт таблицы в PostgreSQL;
дополнительно приложение само вызывает `Base.metadata.create_all()` при
старте — так что таблицы появятся в любом случае, даже если init.sql не
выполнялся.

## Двухфакторная аутентификация (email OTP)

У каждого сотрудника есть поле «Двухфакторная аутентификация» (включена
по умолчанию). Если она включена, вход происходит в два шага:

1. `POST /login` (логин + пароль) → если пароль верный и 2FA включена,
   сервер НЕ выдаёт токены сразу, а генерирует одноразовый 6-значный код,
   сохраняет в БД его HMAC-хеш (не сам код), отправляет код на почту
   сотрудника и возвращает `pending_token` — короткоживущий JWT
   отдельного типа (`type: "2fa_pending"`), который ни на что другое не
   годится.
2. `POST /login/verify-otp` с `{pending_token, code}` → при верном коде
   выдаёт обычную пару access/refresh токенов. Есть лимит в 5 попыток
   ввода кода и `POST /login/resend-otp` для повторной отправки с
   cooldown 30 секунд (старый код при этом становится недействителен).

**Настройка реальной отправки почты**: заполните `SMTP_HOST`,
`SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` в `.env`
(подходит Яндекс.Почта, Mail.ru, Gmail с паролем приложения и т.п.).
**Если `SMTP_HOST` оставить пустым** (как в `.env.example` по
умолчанию — удобно для локальной проверки без настройки почты), письмо
не уходит в сеть, а код явно пишется в лог приложения с пометкой
`[DEV MODE]`:

```bash
docker compose logs -f backend | grep "DEV MODE"
# или локально без Docker — код появится прямо в консоли uvicorn
```

Отключить 2FA для конкретного сотрудника (например, для сервисного
аккаунта) можно из раздела «Сотрудники» в интерфейсе — это чекбокс в
форме редактирования, изменение сразу действует при следующем входе.

## Роли и права доступа

| Действие | admin | operator | user |
|---|---|---|---|
| Просмотр всех разделов | ✅ | ✅ | ✅ |
| Инциденты / Уязвимости / Журнал реагирования: создание и редактирование | ✅ | ✅ | ❌ |
| Инциденты / Уязвимости / Журнал реагирования: удаление | ✅ | ❌ | ❌ |
| Объекты / Типы уязвимостей / Меры реагирования: изменение | ✅ | ❌ | ❌ |
| Сотрудники: создание, редактирование, удаление, смена ролей | ✅ | ❌ | ❌ |

Права проверяются **на бэкенде** (см. `backend/app/permissions.py` и
параметры `write_dependency`/`delete_dependency` в каждом роутере) — то,
что интерфейс прячет недоступные кнопки, не более чем удобство: прямой
запрос в обход UI с недостаточными правами всё равно получит `403`.

**Как получить роль admin.** Самый первый когда-либо зарегистрированный
через `/register` сотрудник автоматически становится администратором
(«главный админ» проекта) — это единственный способ получить роль admin
через публичную регистрацию. Все дальнейшие попытки указать
`role: "admin"` при регистрации отклоняются с `403`; выдать роль admin
кому-то ещё может только уже существующий администратор — через
редактирование сотрудника в разделе «Сотрудники». Так же на бэкенде
запрещено понизить в роли или удалить **последнего** администратора —
иначе управлять системой стало бы некому.

## Валидация

Пароль должен содержать минимум 8 символов, хотя бы одну заглавную и
одну строчную латинскую букву и цифру; телефон — от 10 до 15 цифр
(допустимы `+`, пробелы, скобки и дефисы для форматирования). Проверка
дублируется на фронтенде (мгновенная подсказка) и на бэкенде
(`backend/app/schemas.py`, `field_validator`) — фронтенд-проверку легко
обойти прямым запросом к API, поэтому финальное решение всегда за
сервером.

## Локальный запуск без Docker

**Бэкенд** (нужен доступ к PostgreSQL, либо см. раздел про тесты для SQLite):
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # укажите свою DATABASE_URL
uvicorn app.main:app --reload
```

**Фронтенд**:
```bash
cd frontend
npm install
npm start
```
Дев-сервер CRA проксирует запросы `/api/*` на `http://localhost:8000`
(см. `src/setupProxy.js`), поэтому отдельно настраивать CORS для локальной
разработки не нужно.

## Тесты

```bash
# Бэкенд — 45 тестов на изолированной in-memory SQLite (Postgres не нужен,
# отправка почты замокана фикстурой captured_otp_emails)
cd backend && pytest -v

# Фронтенд
cd frontend && npm test -- --watchAll=false
```

CI (`.github/workflows/tests.yml`) запускает оба набора тестов и сборку
обоих Docker-образов при каждом push/PR.

## Функциональность (сопоставление с отчётом)

| Раздел отчёта | Реализация |
|---|---|
| БД: 7 сущностей, нормализация до 3НФ | `backend/app/models.py`, `backend/db/init.sql` |
| REST API, CRUD на все сущности | `backend/app/crud_router.py` + `routers/*.py` |
| Пагинация (до 5 записей на странице) | `backend/app/pagination.py`, `PAGE_SIZE` во фронтенде |
| Фильтрация (по состоянию/угрозе/статусу и т.д.) | `*_filters()` в каждом роутере, `filters` в конфигах страниц |
| SPA на React, формы добавления/редактирования | `frontend/src/components/EntityCrudPage.js` |
| Детальный просмотр инцидента | `GET /incidents/{id}/detail`, `frontend/src/pages/IncidentDetail.js` |
| JWT: access + refresh токены | `backend/app/auth.py`, `frontend/src/api/axios.js` (авто-refresh) |
| Двухфакторная аутентификация (OTP по почте) | `backend/app/otp.py`, `routers/auth_router.py`, `frontend/src/pages/VerifyOtp.js` |
| Хеширование паролей (bcrypt) | `passlib[bcrypt]` в `backend/app/auth.py` |
| Ролевая модель доступа (admin/operator/user) | `backend/app/permissions.py`, `frontend/src/utils/permissions.js` |
| Валидация пароля и телефона | `backend/app/schemas.py` (field_validator), `frontend/src/utils/validators.js` |
| Глобальная обработка ошибок (400/401/403/404/500) | `frontend/src/components/Toast.js` + `main.py` exception handlers |
| Docker, docker-compose | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| CI/CD (GitHub Actions) | `.github/workflows/tests.yml` |

## Отличия и осознанные исправления по сравнению с текстом отчёта

- В отчёте внешние ключи на `staff` были описаны как `NOT NULL ...
  ON DELETE SET NULL` — это взаимоисключающие условия (колонка не
  допускает NULL, значит при удалении сотрудника СУБД не смогла бы
  выполнить операцию). Здесь исправлено на `ON DELETE RESTRICT`:
  сотрудника нельзя удалить, пока на него ссылаются инциденты,
  уязвимости или записи журнала реагирования — это и корректно
  работает, и не теряет историю данных. Проверено тестом
  `test_deleting_staff_referenced_by_incident_is_restricted`.
- Пароли пользователей нигде не возвращаются через API (поле
  `password_hash` исключено из всех Pydantic-схем ответа).
- Refresh-токен передаётся отдельным полем `refresh_token` (не через
  `Authorization`), а `/refresh` явно проверяет тип токена (`type:
  "refresh"`), чтобы access-токеном нельзя было продлить сессию.
- Одноразовые OTP-коды хранятся в БД в виде HMAC-SHA256 хеша (ключ —
  `SECRET_KEY` приложения), а не в открытом виде — утечка таблицы
  `login_otp` без секретного ключа не позволяет восстановить код.
- Если приложение обновляется поверх уже существующей базы (например,
  контейнер `db` не пересоздавался), `Base.metadata.create_all()` не
  добавляет новые колонки в уже существующие таблицы — только создаёт
  целиком отсутствующие. Поэтому при апгрейде с версии без 2FA возникала
  ошибка `psycopg2.errors.UndefinedColumn: column staff.two_factor_enabled
  does not exist`. Исправлено через `backend/app/migrations.py` —
  идемпотентные `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при каждом
  старте приложения. После обновления кода достаточно перезапустить
  контейнер backend (`docker compose up --build` или `restart backend`).
