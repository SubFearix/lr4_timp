"""Лёгкие идемпотентные миграции для сред, где база уже была развёрнута
до появления новых полей/таблиц (например, добавление 2FA).

`Base.metadata.create_all()` в main.py создаёт только ЦЕЛИКОМ
отсутствующие таблицы и никогда не изменяет уже существующие — поэтому
у тех, кто поднял БД до появления `staff.two_factor_enabled`, колонки не
появится сама и любой INSERT/SELECT с ней упадёт с
`psycopg2.errors.UndefinedColumn`. Здесь — набор ALTER/CREATE ... IF NOT
EXISTS, которые безопасно выполнять при каждом старте приложения: на
уже актуальной схеме они не делают ничего.

Для SQLite (используется только в тестах) миграции не нужны: тестовая БД
создаётся с нуля из актуальных моделей при каждом запуске.
"""
import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("security_app.migrations")

_POSTGRES_STATEMENTS = [
    "ALTER TABLE staff ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT TRUE",
    """
    CREATE TABLE IF NOT EXISTS login_otp (
        id SERIAL PRIMARY KEY,
        staff_id INT NOT NULL REFERENCES staff(id_s) ON DELETE CASCADE,
        code_hash VARCHAR(64) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        expires_at TIMESTAMPTZ NOT NULL,
        attempts INT NOT NULL DEFAULT 0,
        consumed BOOLEAN NOT NULL DEFAULT FALSE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_login_otp_staff_id ON login_otp(staff_id)",
]


def run_lightweight_migrations(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as conn:
        for statement in _POSTGRES_STATEMENTS:
            conn.execute(text(statement))

    logger.info("Лёгкие миграции применены (staff.two_factor_enabled, login_otp).")
