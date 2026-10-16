import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.task import Task
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def client():
    """Provides a FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def clean_db():
    """Ensures test database is clean before and after tests."""
    db = SessionLocal()
    # Delete test tasks first
    db.query(Task).delete()
    # Delete test users
    db.query(User).filter(
        User.email.in_([
            "tester_alpha@example.com",
            "tester_beta@example.com",
            "tester_gamma@example.com"
        ])
    ).delete()
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.query(Task).delete()
    db.query(User).filter(
        User.email.in_([
            "tester_alpha@example.com",
            "tester_beta@example.com",
            "tester_gamma@example.com"
        ])
    ).delete()
    db.commit()
    db.close()


# -----------------------------------------------------------------------------
# 1. Root & Health Endpoint Tests
# -----------------------------------------------------------------------------
def test_root_endpoint_serves_homepage(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "TaskFlow" in res.text
    # Verify links to Sign In exist on the homepage
    assert "login.html" in res.text


def test_api_info_endpoint(client):
    res = client.get("/api")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] == "online"


def test_html_page_routes(client):
    # Test direct clean routes
    for path in ["/login.html", "/login", "/dashboard.html", "/dashboard", "/index.html", "/register"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


# -----------------------------------------------------------------------------
# 2. Registration Tests
# -----------------------------------------------------------------------------
def test_user_registration_success(client, clean_db):
    res = client.post("/api/v1/auth/register", json={
        "name": "Alpha User",
        "email": "tester_alpha@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["user"]["email"] == "tester_alpha@example.com"
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


def test_user_registration_duplicate_email(client):
    # Case-insensitive duplicate email attempt
    res = client.post("/api/v1/auth/register", json={
        "name": "Duplicate Alpha",
        "email": "TESTER_ALPHA@EXAMPLE.COM",
        "password": "NewPassword123!"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()


def test_user_registration_invalid_inputs(client):
    # Invalid email
    res1 = client.post("/api/v1/auth/register", json={
        "name": "Bad Email",
        "email": "not-valid-email",
        "password": "Password123!"
    })
    assert res1.status_code == 422

    # Short password
    res2 = client.post("/api/v1/auth/register", json={
        "name": "Short Pwd",
        "email": "short@example.com",
        "password": "123"
    })
    assert res2.status_code == 422

    # Empty name
    res3 = client.post("/api/v1/auth/register", json={
        "name": "   ",
        "email": "emptyname@example.com",
        "password": "Password123!"
    })
    assert res3.status_code == 422


# -----------------------------------------------------------------------------
# 3. Login & Authentication Tests
# -----------------------------------------------------------------------------
def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "tester_alpha@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "tester_alpha@example.com"


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "tester_alpha@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_login_nonexistent_user(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 4. Protected Route & Token Validation Tests
# -----------------------------------------------------------------------------
def test_protected_me_endpoint_with_valid_token(client):
    # Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "tester_alpha@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "tester_alpha@example.com"


def test_protected_me_endpoint_missing_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_protected_me_endpoint_malformed_token(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad.token.string"})
    assert res.status_code == 401


def test_protected_me_endpoint_expired_token(client):
    # Retrieve user ID
    db = SessionLocal()
    user = db.query(User).filter(User.email == "tester_alpha@example.com").first()
    user_id = user.id
    db.close()

    # Generate token expired 1 minute ago
    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(minutes=-1))
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 5. Task CRUD & Ownership Security Tests
# -----------------------------------------------------------------------------
def test_task_crud_and_ownership(client):
    # 1. Register User Beta
    res_b = client.post("/api/v1/auth/register", json={
        "name": "Beta User",
        "email": "tester_beta@example.com",
        "password": "Password123!"
    })
    assert res_b.status_code == 201

    # 2. Get tokens for Alpha and Beta
    token_a = client.post("/api/v1/auth/login", json={
        "email": "tester_alpha@example.com",
        "password": "Password123!"
    }).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    token_b = client.post("/api/v1/auth/login", json={
        "email": "tester_beta@example.com",
        "password": "Password123!"
    }).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Alpha creates Task 1
    create_res = client.post("/api/v1/tasks/", json={
        "title": "Alpha Task Alpha",
        "description": "Task for Alpha",
        "priority": "high",
        "status": "pending"
    }, headers=headers_a)
    assert create_res.status_code == 201
    task_a = create_res.json()
    task_id = task_a["id"]

    # 4. View single task by Owner (Alpha)
    get_res = client.get(f"/api/v1/tasks/{task_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Alpha Task Alpha"

    # 5. Ownership Security Check: Beta attempts to VIEW Alpha's task -> 403 Forbidden
    beta_view = client.get(f"/api/v1/tasks/{task_id}", headers=headers_b)
    assert beta_view.status_code == 403

    # 6. Ownership Security Check: Beta attempts to EDIT Alpha's task -> 403 Forbidden
    beta_edit = client.put(f"/api/v1/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_b)
    assert beta_edit.status_code == 403

    # 7. Ownership Security Check: Beta attempts to DELETE Alpha's task -> 403 Forbidden
    beta_del = client.delete(f"/api/v1/tasks/{task_id}", headers=headers_b)
    assert beta_del.status_code == 403

    # 8. Data Isolation: Beta's task list must be empty
    beta_list = client.get("/api/v1/tasks/", headers=headers_b).json()
    assert len(beta_list) == 0

    # 9. Owner (Alpha) updates the task
    update_res = client.put(f"/api/v1/tasks/{task_id}", json={
        "status": "completed"
    }, headers=headers_a)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "completed"

    # 10. Owner (Alpha) deletes the task
    del_res = client.delete(f"/api/v1/tasks/{task_id}", headers=headers_a)
    assert del_res.status_code == 200

    # 11. Subsequent get returns 404
    get_404 = client.get(f"/api/v1/tasks/{task_id}", headers=headers_a)
    assert get_404.status_code == 404


# -----------------------------------------------------------------------------
# 6. Task Metrics & Search/Filter Tests
# -----------------------------------------------------------------------------
def test_task_metrics_and_search_filters(client):
    token = client.post("/api/v1/auth/login", json={
        "email": "tester_alpha@example.com",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clean existing tasks for alpha
    existing_tasks = client.get("/api/v1/tasks/", headers=headers).json()
    for t in existing_tasks:
        client.delete(f"/api/v1/tasks/{t['id']}", headers=headers)

    # Create 3 tasks with distinct priorities, statuses, and due dates
    # Task 1: Pending & due tomorrow
    due_future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    client.post("/api/v1/tasks/", json={
        "title": "Backend Optimization",
        "description": "Refactor database queries",
        "priority": "high",
        "status": "pending",
        "due_date": due_future
    }, headers=headers)

    # Task 2: Completed
    client.post("/api/v1/tasks/", json={
        "title": "Frontend Setup",
        "description": "HTML CSS JS",
        "priority": "low",
        "status": "completed"
    }, headers=headers)

    # Task 3: Overdue (due 3 days ago)
    due_past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    client.post("/api/v1/tasks/", json={
        "title": "Deploy Documentation",
        "description": "Write API docs",
        "priority": "medium",
        "status": "pending",
        "due_date": due_past
    }, headers=headers)

    # 1. Verify Metrics
    metrics = client.get("/api/v1/tasks/metrics", headers=headers).json()
    assert metrics["total"] == 3
    assert metrics["pending"] == 2
    assert metrics["completed"] == 1
    assert metrics["overdue"] == 1

    # 2. Verify Search
    search_res = client.get("/api/v1/tasks/?search=optimization", headers=headers).json()
    assert len(search_res) == 1
    assert search_res[0]["title"] == "Backend Optimization"

    # 3. Verify Status Filter
    filter_completed = client.get("/api/v1/tasks/?status=completed", headers=headers).json()
    assert len(filter_completed) == 1
    assert filter_completed[0]["title"] == "Frontend Setup"

    # 4. Verify Priority Filter
    filter_high = client.get("/api/v1/tasks/?priority=high", headers=headers).json()
    assert len(filter_high) == 1
    assert filter_high[0]["title"] == "Backend Optimization"


# -----------------------------------------------------------------------------
# 7. Frontend Static Routes Tests
# -----------------------------------------------------------------------------
def test_frontend_static_assets(client):
    assets = [
        "/frontend/index.html",
        "/frontend/login.html",
        "/frontend/dashboard.html",
        "/frontend/css/style.css",
        "/frontend/js/auth.js",
        "/frontend/js/register.js",
        "/frontend/js/login.js",
        "/frontend/js/dashboard.js"
    ]
    for asset in assets:
        res = client.get(asset)
        assert res.status_code == 200, f"Asset failed: {asset}"
