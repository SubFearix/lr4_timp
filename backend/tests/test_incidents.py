def _create_object(client, headers, name="Офис"):
    resp = client.post("/objects", json={"obj_name": name, "obj_type": "Офис"}, headers=headers)
    return resp.json()["id_obj"]


def test_incident_create_and_detail(client, auth_headers, registered_staff):
    obj_id = _create_object(client, auth_headers)
    profile = client.get("/profile", headers=auth_headers).json()

    create_resp = client.post(
        "/incidents",
        json={
            "id_obj": obj_id,
            "id_s": profile["id_s"],
            "inc_type": "Проникновение",
            "inc_date": "2026-08-01",
            "inc_time": "13:45:00",
            "threat_lvl": 7,
            "state": "новый",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["id_inc"]

    detail_resp = client.get(f"/incidents/{inc_id}/detail", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["related_object"]["obj_name"] == "Офис"
    assert detail["responsible"]["login"] == profile["login"]


def test_incident_invalid_threat_level_rejected(client, auth_headers, registered_staff):
    obj_id = _create_object(client, auth_headers)
    profile = client.get("/profile", headers=auth_headers).json()
    resp = client.post(
        "/incidents",
        json={
            "id_obj": obj_id,
            "id_s": profile["id_s"],
            "inc_type": "Проникновение",
            "inc_date": "2026-08-01",
            "inc_time": "13:45:00",
            "threat_lvl": 42,
            "state": "новый",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_incident_filtering_by_state(client, auth_headers, registered_staff):
    obj_id = _create_object(client, auth_headers)
    profile = client.get("/profile", headers=auth_headers).json()
    for state in ["новый", "закрыт", "новый"]:
        client.post(
            "/incidents",
            json={
                "id_obj": obj_id,
                "id_s": profile["id_s"],
                "inc_type": "Проникновение",
                "inc_date": "2026-08-01",
                "inc_time": "10:00:00",
                "threat_lvl": 3,
                "state": state,
            },
            headers=auth_headers,
        )
    filtered = client.get("/incidents?state=новый", headers=auth_headers).json()
    assert filtered["total"] == 2


def test_deleting_staff_referenced_by_incident_is_restricted(client, auth_headers, registered_staff):
    obj_id = _create_object(client, auth_headers)
    # registered_staff (ivanov) — единственный админ; удалять его нельзя
    # по отдельной причине ("последний администратор", см.
    # test_permissions.py), поэтому для проверки именно FK-ограничения
    # используем второго сотрудника, ответственного за инцидент.
    second_resp = client.post(
        "/staff",
        json={
            "surname": "Смирнов", "name": "Пётр", "position": "Охранник",
            "phonenum": "+79995550011", "email": "smirnov@example.com",
            "login": "smirnov", "password": "SmirnovPass1", "role": "operator",
        },
        headers=auth_headers,
    )
    assert second_resp.status_code == 201
    second_id = second_resp.json()["id_s"]

    client.post(
        "/incidents",
        json={
            "id_obj": obj_id,
            "id_s": second_id,
            "inc_type": "Проникновение",
            "inc_date": "2026-08-01",
            "inc_time": "10:00:00",
            "threat_lvl": 3,
            "state": "новый",
        },
        headers=auth_headers,
    )
    delete_resp = client.delete(f"/staff/{second_id}", headers=auth_headers)
    assert delete_resp.status_code == 409


def test_deleting_object_cascades_its_incidents(client, auth_headers, registered_staff):
    obj_id = _create_object(client, auth_headers)
    profile = client.get("/profile", headers=auth_headers).json()
    inc_resp = client.post(
        "/incidents",
        json={
            "id_obj": obj_id,
            "id_s": profile["id_s"],
            "inc_type": "Проникновение",
            "inc_date": "2026-08-01",
            "inc_time": "10:00:00",
            "threat_lvl": 3,
            "state": "новый",
        },
        headers=auth_headers,
    )
    inc_id = inc_resp.json()["id_inc"]
    delete_resp = client.delete(f"/objects/{obj_id}", headers=auth_headers)
    assert delete_resp.status_code == 204
    missing_resp = client.get(f"/incidents/{inc_id}", headers=auth_headers)
    assert missing_resp.status_code == 404
