from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.routes.attendance import faculty_required
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import app
from app.models.attendance import Attendance
from app.models.role import Role
from app.models.user import User


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def override_get_db():
    yield MagicMock()


def override_faculty_user():
    return User(
        id=1,
        username="faculty",
        email="faculty@coe.local",
        password_hash="not-used",
        role_id=2,
    )


def override_admin_user():
    return User(
        id=2,
        username="admin",
        email="admin@coe.local",
        password_hash="not-used",
        role_id=1,
    )


def override_student_user():
    return User(
        id=3,
        username="student",
        email="student@coe.local",
        password_hash="not-used",
        role_id=3,
    )


def test_record_attendance_requires_authentication():
    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/api/v1/attendance",
        json={
            "student_id": 1,
            "subject_id": 101,
            "session_date": "2026-08-13",
            "status": "PRESENT",
        },
    )

    assert response.status_code == 401


def test_record_attendance_allows_faculty():
    db = MagicMock()
    db.scalar.return_value = None

    def refresh_attendance(attendance):
        attendance.id = 1

    db.refresh.side_effect = refresh_attendance

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    response = client.post(
        "/api/v1/attendance",
        json={
            "student_id": 1,
            "subject_id": 101,
            "session_date": "2026-08-13",
            "status": "PRESENT",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["student_id"] == 1
    assert data["subject_id"] == 101
    assert data["session_date"] == "2026-08-13"
    assert data["status"] == "PRESENT"

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_record_attendance_rejects_non_faculty():
    db = MagicMock()

    db.scalar.return_value = Role(
        id=3,
        name="student",
    )

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_student_user

    response = client.post(
        "/api/v1/attendance",
        json={
            "student_id": 1,
            "subject_id": 101,
            "session_date": "2026-08-13",
            "status": "PRESENT",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_record_attendance_rejects_duplicate():
    db = MagicMock()

    db.scalar.return_value = Attendance(
        id=1,
        student_id=1,
        subject_id=101,
        session_date=date(2026, 8, 13),
        status="PRESENT",
    )

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    response = client.post(
        "/api/v1/attendance",
        json={
            "student_id": 1,
            "subject_id": 101,
            "session_date": "2026-08-13",
            "status": "PRESENT",
        },
    )

    assert response.status_code == 409
    assert "already recorded" in response.json()["detail"]


def test_bulk_record_attendance():
    db = MagicMock()

    db.scalars.return_value.all.return_value = []

    def refresh_attendance(attendance):
        if attendance.student_id == 1:
            attendance.id = 1
        else:
            attendance.id = 2

    db.refresh.side_effect = refresh_attendance

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "subject_id": 101,
            "session_date": "2026-08-13",
            "records": [
                {
                    "student_id": 1,
                    "status": "PRESENT",
                },
                {
                    "student_id": 2,
                    "status": "ABSENT",
                },
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == 1
    assert data[0]["student_id"] == 1
    assert data[0]["status"] == "PRESENT"

    assert data[1]["id"] == 2
    assert data[1]["student_id"] == 2
    assert data[1]["status"] == "ABSENT"

    db.add_all.assert_called_once()
    db.commit.assert_called_once()
    assert db.refresh.call_count == 2


def test_bulk_record_rejects_duplicate_students():
    db = MagicMock()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "subject_id": 101,
            "session_date": "2026-08-13",
            "records": [
                {
                    "student_id": 1,
                    "status": "PRESENT",
                },
                {
                    "student_id": 1,
                    "status": "ABSENT",
                },
            ],
        },
    )

    assert response.status_code == 409
    assert "Duplicate student IDs" in response.json()["detail"]


def test_attendance_summary():
    db = MagicMock()

    records = [
        Attendance(
            id=1,
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 10),
            status="PRESENT",
        ),
        Attendance(
            id=2,
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 11),
            status="PRESENT",
        ),
        Attendance(
            id=3,
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 12),
            status="ABSENT",
        ),
        Attendance(
            id=4,
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 13),
            status="EXCUSED",
        ),
    ]

    db.scalars.return_value.all.return_value = records

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    response = client.get(
        "/api/v1/attendance/summary",
        params={
            "student_id": 1,
            "subject_id": 101,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["student_id"] == 1
    assert data["subject_id"] == 101
    assert data["attended_sessions"] == 2
    assert data["eligible_sessions"] == 3
    assert data["attendance_percentage"] == 66.67