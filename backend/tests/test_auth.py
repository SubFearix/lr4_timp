from tests.conftest import login_with_otp


def test_register_creates_staff_without_exposing_password(client):
    payload = {
        "surname": "Петров",
        "name": "Пётр",
        "position": "Завуч по безопасности",
        "phonenum": "+79990001122",
        "email": "petrov@example.com",
        "login": "petrov",
        "password": "AnotherPass1",
    }
    response = client.post("/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["login"] == "petrov"
    assert data["two_factor_enabled"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_login_returns_409(client, registered_staff):
    duplicate = dict(registered_staff)
    duplicate["email"] = "other@example.com"
    response = client.post("/register", json=duplicate)
    assert response.status_code == 409


def test_login_wrong_password_returns_401(client, registered_staff):
    response = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_with_correct_password_requires_otp(client, registered_staff, captured_otp_emails):
    response = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": registered_staff["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requires_otp"] is True
    assert body["access_token"] is None
    assert body["pending_token"]
    assert body["masked_email"].startswith("i")  # ivanov@example.com -> i***v@example.com
    assert "@example.com" in body["masked_email"]
    # код действительно "отправлен" (перехвачен фикстурой) на почту сотрудника
    assert registered_staff["email"] in captured_otp_emails


def test_verify_otp_with_correct_code_returns_tokens(client, registered_staff, captured_otp_emails):
    tokens = login_with_otp(
        client, captured_otp_emails,
        registered_staff["login"], registered_staff["password"], registered_staff["email"],
    )
    assert tokens["requires_otp"] is False
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_verify_otp_with_wrong_code_returns_401_and_keeps_pending_valid(client, registered_staff, captured_otp_emails):
    login_resp = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": registered_staff["password"]},
    )
    pending_token = login_resp.json()["pending_token"]

    wrong_resp = client.post("/login/verify-otp", json={"pending_token": pending_token, "code": "000000"})
    assert wrong_resp.status_code == 401
    assert "Осталось попыток" in wrong_resp.json()["detail"]

    # правильный код всё ещё принимается (одна неверная попытка не сжигает код)
    correct_code = captured_otp_emails[registered_staff["email"]]
    good_resp = client.post("/login/verify-otp", json={"pending_token": pending_token, "code": correct_code})
    assert good_resp.status_code == 200


def test_verify_otp_locks_after_max_attempts(client, registered_staff, captured_otp_emails):
    login_resp = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": registered_staff["password"]},
    )
    pending_token = login_resp.json()["pending_token"]

    for _ in range(5):
        resp = client.post("/login/verify-otp", json={"pending_token": pending_token, "code": "000000"})
        assert resp.status_code == 401

    locked_resp = client.post(
        "/login/verify-otp",
        json={"pending_token": pending_token, "code": captured_otp_emails[registered_staff["email"]]},
    )
    assert locked_resp.status_code == 429


def test_verify_otp_rejects_access_token_as_pending_token(client, auth_headers):
    access_token = auth_headers["Authorization"].split(" ")[1]
    response = client.post("/login/verify-otp", json={"pending_token": access_token, "code": "123456"})
    assert response.status_code == 401


def test_resend_otp_issues_new_code_and_invalidates_old_one(client, registered_staff, captured_otp_emails, monkeypatch):
    from app.config import get_settings
    # снимаем cooldown, иначе повторная отправка сразу после логина будет
    # заблокирована лимитом — это отдельно проверяется другим тестом
    monkeypatch.setattr(get_settings(), "otp_resend_cooldown_seconds", 0)

    login_resp = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": registered_staff["password"]},
    )
    body = login_resp.json()
    old_code = captured_otp_emails[registered_staff["email"]]

    resend_resp = client.post("/login/resend-otp", json={"pending_token": body["pending_token"]})
    assert resend_resp.status_code == 200
    new_code = captured_otp_emails[registered_staff["email"]]
    assert new_code != old_code

    # старый код больше не работает
    old_attempt = client.post("/login/verify-otp", json={"pending_token": body["pending_token"], "code": old_code})
    assert old_attempt.status_code in (400, 401)

    # новый код работает
    new_attempt = client.post("/login/verify-otp", json={"pending_token": body["pending_token"], "code": new_code})
    assert new_attempt.status_code == 200


def test_resend_otp_respects_cooldown(client, registered_staff, captured_otp_emails):
    login_resp = client.post(
        "/login",
        data={"username": registered_staff["login"], "password": registered_staff["password"]},
    )
    pending_token = login_resp.json()["pending_token"]

    # код уже "отправлен" во время /login — немедленный повтор должен
    # быть заблокирован cooldown'ом (по умолчанию 30 сек)
    resend_resp = client.post("/login/resend-otp", json={"pending_token": pending_token})
    assert resend_resp.status_code == 429
    assert "Подождите" in resend_resp.json()["detail"]


def test_profile_requires_auth(client):
    response = client.get("/profile")
    assert response.status_code == 401


def test_profile_returns_current_user(client, auth_headers):
    response = client.get("/profile", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["login"] == "ivanov"


def test_staff_without_2fa_logs_in_directly(client):
    payload = {
        "surname": "Кузнецова",
        "name": "Анна",
        "position": "Секретарь",
        "phonenum": "+79995554433",
        "email": "kuznetsova@example.com",
        "login": "kuznetsova",
        "password": "SecretaryPass1",
        "two_factor_enabled": False,
    }
    reg_resp = client.post("/register", json=payload)
    assert reg_resp.status_code == 201
    assert reg_resp.json()["two_factor_enabled"] is False

    login_resp = client.post("/login", data={"username": payload["login"], "password": payload["password"]})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["requires_otp"] is False
    assert body["access_token"]


def test_refresh_returns_new_access_token(client, registered_staff, captured_otp_emails):
    tokens = login_with_otp(
        client, captured_otp_emails,
        registered_staff["login"], registered_staff["password"], registered_staff["email"],
    )
    response = client.post("/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_access_token(client, auth_headers):
    access_token = auth_headers["Authorization"].split(" ")[1]
    response = client.post("/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401
