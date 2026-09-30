import datetime
import os
import shutil

import pytest


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(upload_dir))
    monkeypatch.setenv("SECRET_KEY", "pytest-secret-key-not-for-prod")
    monkeypatch.setenv("TEACHER_INVITE_CODE", "TEACH-2026")
    monkeypatch.setenv("APP_ENV", "local")

    # backend.app builds a module-level `app` on import; force a fresh import
    # per test so each test gets its own isolated Settings/DB/Storage.
    import sys
    for mod in list(sys.modules):
        if mod.startswith("backend") or mod.startswith("cloud"):
            del sys.modules[mod]
    from backend.app import create_app
    from backend.config import Settings
    flask_app = create_app(Settings.from_env())
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, name, email, password, role, invite_code=None):
    payload = {"name": name, "email": email, "password": password, "role": role}
    if invite_code:
        payload["teacher_invite_code"] = invite_code
    return client.post("/api/register", json=payload)


@pytest.fixture()
def teacher_headers(client):
    r = register(client, "Dr. Asha Rao", "asha@example.edu", "TeachPass123", "teacher", "TEACH-2026")
    token = r.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def student_headers(client):
    r = register(client, "Rohit Kumar", "rohit@example.edu", "StudentPass123", "student")
    token = r.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def course_id(client, teacher_headers):
    r = client.post("/api/courses", json={"course_name": "Cloud Computing 101"}, headers=teacher_headers)
    return r.get_json()["course_id"]


def future_iso(days=2):
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).isoformat().replace("+00:00", "Z")


def past_iso(days=2):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat().replace("+00:00", "Z")


@pytest.fixture()
def assignment_id(client, teacher_headers, course_id):
    r = client.post("/api/assignments", json={
        "course_id": course_id, "title": "Assignment 1", "description": "desc",
        "deadline": future_iso(), "max_marks": 100, "allowed_file_types": "pdf,docx",
        "max_file_size_mb": 5,
    }, headers=teacher_headers)
    return r.get_json()["assignment_id"]
