import pytest


# Тесты, не требующие БД
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_create_application_validation(client):
    # невалидные данные (отрицательная сумма) - код 422
    resp = await client.post("/applications", json={
        "applicant_name": "Тест",
        "amount": -500,
        "monthly_income": 100000,
        "purpose": "Проверка",
        "term_months": 12,
    })
    assert resp.status_code == 422


# Тесты с БД
async def test_create_and_get_application(client):
    # создаём заявку
    resp = await client.post("/applications", json={
        "applicant_name": "Иван Петров",
        "amount": 3000000,
        "monthly_income": 150000,
        "purpose": "Ипотека",
        "term_months": 240,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["applicant_name"] == "Иван Петров"
    assert data["status"] == "pending"
    app_id = data["id"]

    # получаем её обратно
    resp = await client.get(f"/applications/{app_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == app_id


async def test_get_nonexistent_application(client):
    resp = await client.get("/applications/9999")
    assert resp.status_code == 404


# --- Тест анализа с моком агента ---
async def test_analyze_application(client, mock_agent):
    # создаём заявку
    resp = await client.post("/applications", json={
        "applicant_name": "Иван Петров",
        "amount": 3000000,
        "monthly_income": 150000,
        "purpose": "Ипотека",
        "term_months": 240,
    })
    app_id = resp.json()["id"]

    # запускаем анализ (агент замокан = мгновенно)
    resp = await client.post(f"/applications/{app_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["decision"]["decision"] == "approved"
    assert data["decision"]["reasoning"] == "Тестовое решение"