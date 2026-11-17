-- Инициализация схемы БД PostgreSQL для предметной области
-- «Безопасность образовательного учреждения». Выполняется автоматически
-- контейнером postgres при первом старте (docker-entrypoint-initdb.d).
-- Приложение также умеет создавать эти таблицы само при старте
-- (Base.metadata.create_all), этот файл — для полного соответствия
-- физическому проектированию из отчёта и для ручного разворачивания БД.

CREATE TABLE IF NOT EXISTS object (
    id_obj SERIAL PRIMARY KEY,
    obj_name VARCHAR(100) NOT NULL,
    obj_type VARCHAR(50) NOT NULL,
    location VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS staff (
    id_s SERIAL PRIMARY KEY,
    surname VARCHAR(30) NOT NULL,
    name VARCHAR(30) NOT NULL,
    patronymic VARCHAR(30),
    position VARCHAR(100) NOT NULL,
    phonenum VARCHAR(20) NOT NULL,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    two_factor_enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS vulnerability_type (
    id_vultype SERIAL PRIMARY KEY,
    type_name VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS response_measure (
    id_meas SERIAL PRIMARY KEY,
    meas_name VARCHAR(150) NOT NULL,
    time_reg INT
);

-- Примечание: в исходном отчёте ЛР4 ссылки на staff были описаны как
-- "NOT NULL ... ON DELETE SET NULL" — противоречивое условие (колонка не
-- допускает NULL, но при удалении сотрудника СУБД попыталась бы его
-- проставить). Здесь исправлено на ON DELETE RESTRICT: сотрудника нельзя
-- удалить, пока на него ссылаются инциденты/уязвимости/записи журнала.
CREATE TABLE IF NOT EXISTS incident (
    id_inc SERIAL PRIMARY KEY,
    id_obj INT NOT NULL REFERENCES object(id_obj) ON DELETE CASCADE,
    id_s INT NOT NULL REFERENCES staff(id_s) ON DELETE RESTRICT,
    inc_type VARCHAR(100) NOT NULL,
    inc_date DATE NOT NULL,
    inc_time TIME NOT NULL,
    threat_lvl INT NOT NULL CHECK (threat_lvl BETWEEN 1 AND 10),
    state VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS vulnerability (
    id_vul SERIAL PRIMARY KEY,
    id_s INT NOT NULL REFERENCES staff(id_s) ON DELETE RESTRICT,
    id_vultype INT NOT NULL REFERENCES vulnerability_type(id_vultype) ON DELETE RESTRICT,
    sw_ver VARCHAR(50),
    fix_status VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS response_log (
    id_log SERIAL PRIMARY KEY,
    id_inc INT NOT NULL REFERENCES incident(id_inc) ON DELETE CASCADE,
    id_meas INT NOT NULL REFERENCES response_measure(id_meas) ON DELETE RESTRICT,
    id_s INT NOT NULL REFERENCES staff(id_s) ON DELETE RESTRICT,
    date_exec DATE NOT NULL,
    time_exec TIME NOT NULL,
    result TEXT
);

-- Одноразовые коды для двухфакторной аутентификации по почте (см.
-- app/otp.py). Коды хранятся в виде HMAC-хеша, а не в открытом виде.
CREATE TABLE IF NOT EXISTS login_otp (
    id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL REFERENCES staff(id_s) ON DELETE CASCADE,
    code_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    consumed BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_login_otp_staff_id ON login_otp(staff_id);
