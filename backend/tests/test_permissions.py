"""Тесты ролевой модели и валидации, добавленные по итогам ревью:
1. Валидация пароля и телефона.
2. Разные роли имеют доступ к разному функционалу (не только на UI, но
   и на бэкенде — сотрудник не может понизить администратора).
3. С ролью admin можно зарегистрироваться только один раз (bootstrap
   первого администратора); дальше роль admin выдаёт только admin.
"""
from tests.conftest import login_with_otp


def _register_and_login(client, captured_otp_emails, login, password="StrongPass1", role=None, email=None):
    payload = {
        "surname": "Тестов",
        "name": "Тест",
        "position": "Сотрудник",
        "phonenum": "+79990000001",
        "email": email or f"{login}@example.com",
        "login": login,
        "password": password,
    }
    if role is not None:
        payload["role"] = role
    reg_resp = client.post("/register", json=payload)
    return reg_resp, payload


# ------------------------------------------------------------------
# 1. Валидация пароля и телефона
# ------------------------------------------------------------------
def test_register_rejects_weak_password_without_uppercase(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "+79990000000", "email": "weak1@example.com",
        "login": "weak1", "password": "alllower1",
    })
    assert resp.status_code == 422


def test_register_rejects_weak_password_without_digit(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "+79990000000", "email": "weak2@example.com",
        "login": "weak2", "password": "NoDigitsHere",
    })
    assert resp.status_code == 422


def test_register_rejects_too_short_password(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "+79990000000", "email": "weak3@example.com",
        "login": "weak3", "password": "Ab1",
    })
    assert resp.status_code == 422


def test_register_accepts_strong_password(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "+79990000000", "email": "strong@example.com",
        "login": "strongpass", "password": "GoodPass1",
    })
    assert resp.status_code == 201


def test_register_rejects_invalid_phone_letters(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "not-a-phone", "email": "phone1@example.com",
        "login": "phone1", "password": "GoodPass1",
    })
    assert resp.status_code == 422


def test_register_rejects_phone_too_short(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "12345", "email": "phone2@example.com",
        "login": "phone2", "password": "GoodPass1",
    })
    assert resp.status_code == 422


def test_register_accepts_valid_phone_with_formatting(client):
    resp = client.post("/register", json={
        "surname": "Т", "name": "Т", "position": "П",
        "phonenum": "+7 (900) 123-45-67", "email": "phone3@example.com",
        "login": "phone3", "password": "GoodPass1",
    })
    assert resp.status_code == 201


# ------------------------------------------------------------------
# 2. Ролевая модель: разный функционал для разных ролей
# ------------------------------------------------------------------
def test_first_registered_user_becomes_admin_automatically(client):
    resp, _ = _register_and_login(client, None, "firstuser")
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


def test_second_user_cannot_self_assign_admin_role(client, captured_otp_emails):
    _register_and_login(client, captured_otp_emails, "firstadmin")  # первый -> admin (bootstrap)
    resp, _ = _register_and_login(client, captured_otp_emails, "wannabe_admin", role="admin")
    assert resp.status_code == 403


def test_second_user_defaults_to_user_role(client, captured_otp_emails):
    _register_and_login(client, captured_otp_emails, "firstadmin2")
    resp, _ = _register_and_login(client, captured_otp_emails, "plainuser")
    assert resp.status_code == 201
    assert resp.json()["role"] == "user"


def test_second_user_can_self_register_as_operator(client, captured_otp_emails):
    _register_and_login(client, captured_otp_emails, "firstadmin3")
    resp, _ = _register_and_login(client, captured_otp_emails, "opuser", role="operator")
    assert resp.status_code == 201
    assert resp.json()["role"] == "operator"


def _make_user_with_role(client, captured_otp_emails, admin_headers, login, role):
    """Создаёт сотрудника с заданной ролью через админский /staff и
    возвращает его заголовки авторизации."""
    create_resp = client.post(
        "/staff",
        json={
            "surname": "Ролев", "name": login, "position": "Тест",
            "phonenum": "+79990000002", "email": f"{login}@example.com",
            "login": login, "password": "RolePass1", "role": role,
            "two_factor_enabled": False,
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    login_resp = client.post("/login", data={"username": login, "password": "RolePass1"})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["requires_otp"] is False
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_plain_user_cannot_change_anyones_role(client, auth_headers, registered_staff, captured_otp_emails):
    # auth_headers = первый пользователь (admin, ivanov). Создаём рядового
    # сотрудника с ролью user и проверяем, что ОН не может изменить роль
    # администратора (или чью-либо ещё) — тот самый баг из ревью.
    profile = client.get("/profile", headers=auth_headers).json()
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "sotrudnik", "user")

    resp = client.put(
        f"/staff/{profile['id_s']}",
        json={"role": "user"},
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_plain_user_cannot_create_staff(client, auth_headers, captured_otp_emails):
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "sotrudnik2", "user")
    resp = client.post(
        "/staff",
        json={
            "surname": "Х", "name": "Х", "position": "Х",
            "phonenum": "+79990000003", "email": "hacker@example.com",
            "login": "hacker", "password": "HackerPass1", "role": "admin",
        },
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_plain_user_cannot_delete_staff(client, auth_headers, captured_otp_emails):
    victim_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "victim", "operator")
    victim_id = client.get("/profile", headers=victim_headers).json()["id_s"]
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "attacker", "user")

    resp = client.delete(f"/staff/{victim_id}", headers=user_headers)
    assert resp.status_code == 403


def test_admin_can_promote_user_to_admin(client, auth_headers, captured_otp_emails):
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "promoteme", "user")
    user_id = client.get("/profile", headers=user_headers).json()["id_s"]

    resp = client.put(f"/staff/{user_id}", json={"role": "admin"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_last_admin_cannot_be_demoted(client, auth_headers, registered_staff):
    profile = client.get("/profile", headers=auth_headers).json()
    resp = client.put(f"/staff/{profile['id_s']}", json={"role": "user"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "администратор" in resp.json()["detail"].lower()


def test_last_admin_cannot_be_deleted(client, auth_headers, registered_staff):
    profile = client.get("/profile", headers=auth_headers).json()
    resp = client.delete(f"/staff/{profile['id_s']}", headers=auth_headers)
    assert resp.status_code == 400


def test_demoting_admin_is_allowed_when_another_admin_remains(client, auth_headers, captured_otp_emails):
    # Делаем "promoteme" вторым админом, после чего первого можно понизить.
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "secondadmin", "user")
    second_id = client.get("/profile", headers=user_headers).json()["id_s"]
    client.put(f"/staff/{second_id}", json={"role": "admin"}, headers=auth_headers)

    profile = client.get("/profile", headers=auth_headers).json()
    resp = client.put(f"/staff/{profile['id_s']}", json={"role": "user"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "user"


def test_operator_can_create_incident_but_not_delete(client, auth_headers, captured_otp_emails):
    obj_resp = client.post("/objects", json={"obj_name": "Корпус", "obj_type": "Учебный корпус"}, headers=auth_headers)
    obj_id = obj_resp.json()["id_obj"]
    operator_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "operator1", "operator")
    operator_id = client.get("/profile", headers=operator_headers).json()["id_s"]

    create_resp = client.post(
        "/incidents",
        json={
            "id_obj": obj_id, "id_s": operator_id, "inc_type": "Пожар",
            "inc_date": "2026-08-01", "inc_time": "09:00:00",
            "threat_lvl": 5, "state": "новый",
        },
        headers=operator_headers,
    )
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["id_inc"]

    delete_resp = client.delete(f"/incidents/{inc_id}", headers=operator_headers)
    assert delete_resp.status_code == 403


def test_plain_user_cannot_create_incident(client, auth_headers, captured_otp_emails):
    obj_resp = client.post("/objects", json={"obj_name": "Корпус", "obj_type": "Учебный корпус"}, headers=auth_headers)
    obj_id = obj_resp.json()["id_obj"]
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "readonlyuser", "user")
    user_id = client.get("/profile", headers=user_headers).json()["id_s"]

    resp = client.post(
        "/incidents",
        json={
            "id_obj": obj_id, "id_s": user_id, "inc_type": "Пожар",
            "inc_date": "2026-08-01", "inc_time": "09:00:00",
            "threat_lvl": 5, "state": "новый",
        },
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_plain_user_can_still_view_incidents(client, auth_headers, captured_otp_emails):
    user_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "viewer1", "user")
    resp = client.get("/incidents", headers=user_headers)
    assert resp.status_code == 200


def test_operator_cannot_manage_objects(client, auth_headers, captured_otp_emails):
    operator_headers = _make_user_with_role(client, captured_otp_emails, auth_headers, "operator2", "operator")
    resp = client.post(
        "/objects",
        json={"obj_name": "Новый корпус", "obj_type": "Учебный корпус"},
        headers=operator_headers,
    )
    assert resp.status_code == 403
