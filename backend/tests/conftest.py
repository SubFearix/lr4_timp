"""Тестовая конфигурация: подменяет боевую PostgreSQL на изолированную
in-memory SQLite базу для каждого запуска тестов, чтобы CI не зависел от
поднятого сервера БД."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.otp as otp_module
from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def fresh_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def captured_otp_emails(monkeypatch):
    """Перехватывает отправку OTP-писем вместо реального SMTP: тесты не
    должны стучаться в сеть. Возвращает {email: последний_код}."""
    codes = {}

    def fake_send_otp_email(to_email, full_name, code):
        codes[to_email] = code

    monkeypatch.setattr(otp_module, "send_otp_email", fake_send_otp_email)
    return codes


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_staff(client):
    payload = {
        "surname": "Иванов",
        "name": "Иван",
        "position": "Охранник",
        "phonenum": "+79990000000",
        "email": "ivanov@example.com",
        "login": "ivanov",
        "password": "StrongPass1",
    }
    response = client.post("/register", json=payload)
    assert response.status_code == 201
    return payload


def login_with_otp(client, captured_otp_emails, login_value, password, email):
    """Проходит полный цикл входа: логин/пароль → OTP-код → токены."""
    login_resp = client.post("/login", data={"username": login_value, "password": password})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["requires_otp"] is True
    code = captured_otp_emails[email]
    verify_resp = client.post(
        "/login/verify-otp",
        json={"pending_token": body["pending_token"], "code": code},
    )
    assert verify_resp.status_code == 200
    return verify_resp.json()


@pytest.fixture
def auth_headers(client, registered_staff, captured_otp_emails):
    tokens = login_with_otp(
        client, captured_otp_emails,
        registered_staff["login"], registered_staff["password"], registered_staff["email"],
    )
    return {"Authorization": f"Bearer {tokens['access_token']}"}
