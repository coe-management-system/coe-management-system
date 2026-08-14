from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.dependencies import get_current_user
from app.main import app
from app.models.role import Role
from app.models.timetable import TimetableEvent
from app.models.user import User


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)

_seed = Session(engine)
_seed.add_all(
    [
        Role(id=1, name="faculty"),
        Role(id=2, name="student"),
        TimetableEvent(
            id=1,
            subject_id=101,
            faculty_id=10,
            batch_id=201,
            room_id="101",
            event_date=date(2026, 8, 15),
            start_time=time(10, 0),
            end_time=time(11, 0),
            priority=2,
        ),
        TimetableEvent(
            id=2,
            subject_id=102,
            faculty_id=10,
            batch_id=202,
            room_id="102",
            event_date=date(2026, 8, 15),
            start_time=time(10, 30),
            end_time=time(11, 30),
            priority=2,
        ),
    ]
)
_seed.commit()
_seed.close()

client = TestClient(app)


def override_get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


def override_faculty_user():
    return User(
        id=1,
        username="faculty",
        email="faculty@example.com",
        password_hash="not-used",
        role_id=1,
    )


def override_student_user():
    return User(
        id=2,
        username="student",
        email="student@example.com",
        password_hash="not-used",
        role_id=2,
    )


def unauthenticated():
    app.dependency_overrides.pop(get_current_user, None)


def as_faculty():
    app.dependency_overrides[get_current_user] = override_faculty_user


def as_student():
    app.dependency_overrides[get_current_user] = override_student_user


@pytest.fixture(autouse=True)
def _ensure_dependency_overrides():
    """Re-apply the DB override before every test.

    Another integration module clears all overrides in its teardown, so
    this fixture guarantees the scheduling API always uses the in-memory
    database.
    """
    app.dependency_overrides[get_db] = override_get_db
    yield


def teardown_module():
    app.dependency_overrides.clear()


def test_timetable_requires_authentication():
    unauthenticated()
    response = client.get("/api/v1/timetable")

    assert response.status_code == 401


def test_timetable_returns_events():
    as_faculty()
    response = client.get("/api/v1/timetable")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["faculty_id"] == 10


def test_conflicts_endpoint_returns_structured_conflicts():
    as_faculty()
    response = client.get("/api/v1/scheduling/conflicts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["constraint_type"] == "faculty"
    assert data[0]["severity"] == "hard"
    assert "message" in data[0]


def test_workload_endpoint_reports_overload():
    as_faculty()
    response = client.get("/api/v1/workload?capacity=1")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["faculty_id"] == 10
    assert data[0]["allocated_hours"] == 2.0
    assert data[0]["status"] == "overloaded"


def test_reschedule_requires_token():
    unauthenticated()
    response = client.post(
        "/api/v1/scheduling/reschedule-recommendation",
        json={"event_id": 1},
    )

    assert response.status_code == 401


def test_reschedule_forbidden_for_wrong_role():
    as_student()
    response = client.post(
        "/api/v1/scheduling/reschedule-recommendation",
        json={"event_id": 1},
    )

    assert response.status_code == 403


def test_reschedule_allowed_for_faculty():
    as_faculty()
    response = client.post(
        "/api/v1/scheduling/reschedule-recommendation",
        json={
            "event_id": 1,
            "candidates": [
                {
                    "date": "2026-08-15",
                    "start_time": "11:30",
                    "end_time": "12:30",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recommendation"
    assert data["event_id"] == 1
    assert "reason" in data


def test_what_if_requires_token():
    unauthenticated()
    response = client.post("/api/v1/scheduling/what-if", json={"type": "event_change"})

    assert response.status_code == 401


def test_what_if_does_not_modify_database():
    as_faculty()
    response = client.post(
        "/api/v1/scheduling/what-if",
        json={
            "type": "room_unavailable",
            "resource": "101",
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "11:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["timetable_unchanged"] is True
    assert any(e["id"] == 1 for e in data["affected_events"])

    check = Session(engine)
    rows = check.query(TimetableEvent).all()
    assert len(rows) == 2
    assert rows[0].room_id == "101"
    check.close()


def test_no_feasible_slot_scenario():
    as_faculty()
    response = client.post(
        "/api/v1/scheduling/reschedule-recommendation",
        json={
            "event_id": 1,
            "candidates": [
                {
                    "date": "2026-08-15",
                    "start_time": "10:00",
                    "end_time": "11:00",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NO_FEASIBLE_SLOT"
    assert "reasons" in data
    assert data["reasons"]