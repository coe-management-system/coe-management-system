import io
from unittest.mock import MagicMock

import openpyxl
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.api.routes.imports import faculty_required
from app.main import app
from app.models.user import User

client = TestClient(app)


def override_get_db():
    yield MagicMock()


def override_faculty_user():
    return User(
        id=2,
        username="faculty1",
        email="faculty1@example.com",
        password_hash="not-used",
        role_id=1,
    )


app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()


def make_valid_excel_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Roll No", "Name", "Email", "Department", "Batch", "Group"])
    ws.append(["CSE201", "Test Student", "test@example.com", "CSE", "2026", "4A"])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_upload_requires_authentication():
    files = {"file": ("students.xlsx", make_valid_excel_bytes(),
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/imports", files=files)
    assert response.status_code == 401


def test_upload_rejects_non_excel_extension():
    app.dependency_overrides[faculty_required] = override_faculty_user
    files = {"file": ("students.txt", b"not an excel file", "text/plain")}
    response = client.post("/api/v1/imports", files=files)
    assert response.status_code == 400
    assert "Excel" in response.json()["detail"]


def test_upload_rejects_empty_file():
    app.dependency_overrides[faculty_required] = override_faculty_user
    files = {"file": ("students.xlsx", b"",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/imports", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_corrupt_workbook():
    app.dependency_overrides[faculty_required] = override_faculty_user
    files = {"file": ("students.xlsx", b"this is not a real xlsx file at all",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/imports", files=files)
    assert response.status_code == 400
    assert "not a valid" in response.json()["detail"].lower()


def test_get_import_not_found():
    app.dependency_overrides[faculty_required] = override_faculty_user

    mock_db = MagicMock()
    mock_db.get.return_value = None

    def override_db_returns_none():
        yield mock_db

    app.dependency_overrides[get_db] = override_db_returns_none
    response = client.get("/api/v1/imports/99999")
    assert response.status_code == 404
    app.dependency_overrides[get_db] = override_get_db


def test_get_import_errors_not_found():
    app.dependency_overrides[faculty_required] = override_faculty_user
    mock_db = MagicMock()
    mock_db.get.return_value = None

    def override_db_returns_none():
        yield mock_db

    app.dependency_overrides[get_db] = override_db_returns_none
    response = client.get("/api/v1/imports/99999/errors")
    assert response.status_code == 404
    app.dependency_overrides[get_db] = override_get_db


def test_get_import_errors_before_validation_returns_empty():
    app.dependency_overrides[faculty_required] = override_faculty_user
    mock_job = MagicMock()
    mock_job.id = 1
    mock_job.validation_result = None
    mock_db = MagicMock()
    mock_db.get.return_value = mock_job

    def override_db_with_job():
        yield mock_db

    app.dependency_overrides[get_db] = override_db_with_job
    response = client.get("/api/v1/imports/1/errors")
    assert response.status_code == 200
    assert response.json() == {"import_id": 1, "errors": []}
    app.dependency_overrides[get_db] = override_get_db


def test_get_import_errors_after_validation_lists_non_valid_rows():
    app.dependency_overrides[faculty_required] = override_faculty_user
    mock_job = MagicMock()
    mock_job.id = 1
    mock_job.validation_result = '{"records": [' \
        '{"row": 2, "category": "VALID", "field_errors": [], "reference_errors": []},' \
        '{"row": 3, "category": "INVALID", "field_errors": [{"field": "email", "error": "bad format"}], "reference_errors": []},' \
        '{"row": 4, "category": "REFERENCE_ERROR", "field_errors": [], "reference_errors": [{"field": "department", "value": "XX", "error_code": "UNKNOWN_DEPARTMENT", "message": "not found"}]}' \
        ']}'
    mock_db = MagicMock()
    mock_db.get.return_value = mock_job

    def override_db_with_job():
        yield mock_db

    app.dependency_overrides[get_db] = override_db_with_job
    response = client.get("/api/v1/imports/1/errors")
    assert response.status_code == 200
    body = response.json()
    assert body["import_id"] == 1
    assert len(body["errors"]) == 2
    assert all(e["category"] != "VALID" for e in body["errors"])
    rows = {e["row"] for e in body["errors"]}
    assert rows == {3, 4}
    app.dependency_overrides[get_db] = override_get_db
