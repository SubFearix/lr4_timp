def test_objects_require_authentication(client):
    response = client.get("/objects")
    assert response.status_code == 401


def test_object_full_crud_cycle(client, auth_headers):
    create_resp = client.post(
        "/objects",
        json={"obj_name": "Склад №1", "obj_type": "Склад", "location": "ул. Ленина, 10"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    obj_id = create_resp.json()["id_obj"]

    list_resp = client.get("/objects", headers=auth_headers)
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["page_size"] == 5

    get_resp = client.get(f"/objects/{obj_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["obj_name"] == "Склад №1"

    update_resp = client.put(
        f"/objects/{obj_id}",
        json={"obj_name": "Склад №1 (реконструкция)"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["obj_name"] == "Склад №1 (реконструкция)"

    delete_resp = client.delete(f"/objects/{obj_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    missing_resp = client.get(f"/objects/{obj_id}", headers=auth_headers)
    assert missing_resp.status_code == 404


def test_objects_pagination_and_filtering(client, auth_headers):
    for i in range(7):
        client.post(
            "/objects",
            json={"obj_name": f"Объект {i}", "obj_type": "Офис" if i % 2 == 0 else "Склад"},
            headers=auth_headers,
        )

    page1 = client.get("/objects?page=1&page_size=5", headers=auth_headers).json()
    assert len(page1["items"]) == 5
    assert page1["pages"] == 2

    page2 = client.get("/objects?page=2&page_size=5", headers=auth_headers).json()
    assert len(page2["items"]) == 2

    filtered = client.get("/objects?obj_type=Офис", headers=auth_headers).json()
    assert filtered["total"] == 4
    assert all(item["obj_type"] == "Офис" for item in filtered["items"])
