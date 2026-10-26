from app.models import User
from app.security import hash_password
from tests.conftest import register_and_login


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_password_is_not_returned(client):
    response = client.post("/auth/register", json={"email": "a@example.com", "password": "StrongPassword123!"})
    assert response.status_code == 201
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    login = client.post("/auth/login", json={"email": "a@example.com", "password": "StrongPassword123!"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_duplicate_email_rejected(client):
    payload = {"email": "a@example.com", "password": "StrongPassword123!"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_task_crud_and_filter(client):
    token = register_and_login(client)
    headers = auth(token)
    created = client.post("/tasks", headers=headers, json={"title": "Write tests", "description": "Cover API behavior"})
    assert created.status_code == 201
    task = created.json()
    assert task["status"] == "todo"
    task_id = task["id"]

    listing = client.get("/tasks?task_status=todo", headers=headers)
    assert listing.status_code == 200
    assert [t["id"] for t in listing.json()] == [task_id]

    updated = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    deleted = client.delete(f"/tasks/{task_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=headers).status_code == 404


def test_authentication_required_for_tasks(client):
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"title": "No token"}).status_code == 401


def test_member_cannot_read_another_users_task(client):
    token_a = register_and_login(client, "a@example.com")
    token_b = register_and_login(client, "b@example.com")
    created = client.post("/tasks", headers=auth(token_a), json={"title": "Private task"})
    task_id = created.json()["id"]
    response = client.get(f"/tasks/{task_id}", headers=auth(token_b))
    assert response.status_code == 404


def test_member_cannot_list_all_users(client):
    token = register_and_login(client)
    response = client.get("/users", headers=auth(token))
    assert response.status_code == 403


def test_admin_can_list_users_and_view_all_tasks(client):
    member_token = register_and_login(client, "member@example.com")
    member_task = client.post("/tasks", headers=auth(member_token), json={"title": "Team report"})
    assert member_task.status_code == 201

    # Assign the admin role directly for this isolated authorization test.
    from app.database import get_db
    from app.main import app

    # Use the test database installed by the client fixture, not the local app database.
    test_db_dependency = app.dependency_overrides[get_db]()
    db = next(test_db_dependency)
    try:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
        )
        db.add(admin)
        db.commit()
    finally:
        test_db_dependency.close()

    admin_login = client.post("/auth/login", json={"email": "admin@example.com", "password": "AdminPassword123!"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    user_list = client.get("/users", headers=auth(admin_token))
    assert user_list.status_code == 200
    assert len(user_list.json()) == 2
    tasks = client.get("/tasks", headers=auth(admin_token))
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1


def test_invalid_task_status_filter_rejected(client):
    token = register_and_login(client)
    response = client.get("/tasks?task_status=blocked", headers=auth(token))
    assert response.status_code == 422


def test_invalid_login_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_whitespace_only_task_title_is_rejected(client):
    token = register_and_login(client)
    response = client.post("/tasks", headers=auth(token), json={"title": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title cannot be blank"
