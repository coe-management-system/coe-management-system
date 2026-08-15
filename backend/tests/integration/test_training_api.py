from datetime import date, datetime
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.routes.training import faculty_required
from app.core.database import get_db
from app.main import app
from app.models.batch import Batch
from app.models.coe import CoE
from app.models.company import Company
from app.models.faculty import Faculty
from app.models.group import Group
from app.models.technology import Technology
from app.models.training import TrainingProgram, TrainingSession
from app.models.user import User


client = TestClient(app)

mock_db = MagicMock()


def override_get_db():
    yield mock_db


def override_faculty_user():
    return User(
        id=1,
        role_id=1,
    )


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    yield

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(faculty_required, None)

def refresh_side_effect(obj):
    if isinstance(obj, TrainingProgram):
        obj.id = 1
    elif isinstance(obj, TrainingSession):
        obj.id = 1


def reset_mock_db():
    mock_db.reset_mock(
        return_value=True,
        side_effect=True,
    )
    mock_db.refresh.side_effect = refresh_side_effect




# -------------------------------------------------------------------
# Mock objects
# -------------------------------------------------------------------

def make_coe():
    return CoE(
        id=1,
        name="Cloud Computing CoE",
        status="active",
    )


def make_company():
    return Company(
        id=1,
        name="Amazon Web Services",
        type="Technology",
    )


def make_technology():
    return Technology(
        id=1,
        name="AWS",
    )


def make_program():
    return TrainingProgram(
        id=1,
        name="AWS Fundamentals",
        description="Cloud training",
        coe_id=1,
        company_id=1,
        technology_id=1,
        start_date=date(2026, 8, 15),
        end_date=date(2026, 8, 30),
        planned_hours=40,
    )


def make_faculty():
    return Faculty(
        id=1,
    )


def make_batch():
    return Batch(
        id=1,
    )


def make_group():
    return Group(
        id=1,
    )


def make_session():
    return TrainingSession(
        id=1,
        program_id=1,
        batch_id=1,
        group_id=None,
        title="AWS Introduction",
        faculty_id=1,
        start_at=datetime(2026, 8, 15, 10, 0),
        end_at=datetime(2026, 8, 15, 12, 0),
        hours=2,
    )


# -------------------------------------------------------------------
# Training Program - Create
# -------------------------------------------------------------------

def test_create_training_program():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is CoE:
            return make_coe()

        if model is Company:
            return make_company()

        if model is Technology:
            return make_technology()

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "AWS Fundamentals",
            "description": "Cloud training",
            "coe_id": 1,
            "company_id": 1,
            "technology_id": 1,
            "start_date": "2026-08-15",
            "end_date": "2026-08-30",
            "planned_hours": 40,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "AWS Fundamentals"
    assert data["description"] == "Cloud training"
    assert data["coe_id"] == 1
    assert data["company_id"] == 1
    assert data["technology_id"] == 1
    assert data["planned_hours"] == 40


def test_create_training_program_missing_coe():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is CoE:
            return None

        if model is Company:
            return make_company()

        if model is Technology:
            return make_technology()

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "AWS Fundamentals",
            "description": None,
            "coe_id": 999,
            "company_id": 1,
            "technology_id": 1,
            "start_date": "2026-08-15",
            "end_date": "2026-08-30",
            "planned_hours": 40,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CoE not found"


def test_create_training_program_missing_company():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is CoE:
            return make_coe()

        if model is Company:
            return None

        if model is Technology:
            return make_technology()

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "AWS Fundamentals",
            "description": None,
            "coe_id": 1,
            "company_id": 999,
            "technology_id": 1,
            "start_date": "2026-08-15",
            "end_date": "2026-08-30",
            "planned_hours": 40,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Company not found"


def test_create_training_program_missing_technology():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is CoE:
            return make_coe()

        if model is Company:
            return make_company()

        if model is Technology:
            return None

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "AWS Fundamentals",
            "description": None,
            "coe_id": 1,
            "company_id": 1,
            "technology_id": 999,
            "start_date": "2026-08-15",
            "end_date": "2026-08-30",
            "planned_hours": 40,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Technology not found"


def test_create_training_program_invalid_dates():
    reset_mock_db()

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "Invalid Program",
            "description": None,
            "coe_id": 1,
            "company_id": 1,
            "technology_id": 1,
            "start_date": "2026-08-30",
            "end_date": "2026-08-15",
            "planned_hours": 40,
        },
    )

    assert response.status_code == 422

    assert any(
        error["msg"]
        == "Value error, end_date cannot be earlier than start_date"
        for error in response.json()["detail"]
    )


def test_create_training_program_invalid_hours():
    reset_mock_db()

    response = client.post(
        "/api/v1/training/programs",
        json={
            "name": "Invalid Program",
            "description": None,
            "coe_id": 1,
            "company_id": 1,
            "technology_id": 1,
            "start_date": "2026-08-15",
            "end_date": "2026-08-30",
            "planned_hours": 0,
        },
    )

    assert response.status_code == 422


# -------------------------------------------------------------------
# Training Program - Get
# -------------------------------------------------------------------

def test_get_training_programs():
    reset_mock_db()

    mock_db.scalars.return_value.all.return_value = [
        make_program()
    ]

    response = client.get(
        "/api/v1/training/programs",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["name"] == "AWS Fundamentals"


def test_get_training_programs_with_filters():
    reset_mock_db()

    mock_db.scalars.return_value.all.return_value = [
        make_program()
    ]

    response = client.get(
        "/api/v1/training/programs",
        params={
            "coe_id": 1,
            "company_id": 1,
            "technology_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 1


def test_get_training_program():
    reset_mock_db()

    mock_db.get.return_value = make_program()

    response = client.get(
        "/api/v1/training/programs/1",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "AWS Fundamentals"


def test_get_training_program_not_found():
    reset_mock_db()

    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/training/programs/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training program not found"


# -------------------------------------------------------------------
# Training Session - Create
# -------------------------------------------------------------------

def test_schedule_training_session():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is TrainingProgram:
            return make_program()

        if model is Faculty:
            return make_faculty()

        if model is Batch:
            return make_batch()

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 1,
            "batch_id": 1,
            "group_id": None,
            "title": "AWS Introduction",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["program_id"] == 1
    assert data["faculty_id"] == 1
    assert data["batch_id"] == 1
    assert data["title"] == "AWS Introduction"
    assert data["hours"] == 2


def test_schedule_training_session_missing_program():
    reset_mock_db()

    mock_db.get.return_value = None

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 999,
            "faculty_id": 1,
            "batch_id": 1,
            "group_id": None,
            "title": "AWS Introduction",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Training program not found"


def test_schedule_training_session_missing_faculty():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is TrainingProgram:
            return make_program()

        if model is Faculty:
            return None

        if model is Batch:
            return make_batch()

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 999,
            "batch_id": 1,
            "group_id": None,
            "title": "AWS Introduction",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Faculty not found"


def test_schedule_training_session_missing_batch():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is TrainingProgram:
            return make_program()

        if model is Faculty:
            return make_faculty()

        if model is Batch:
            return None

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 1,
            "batch_id": 999,
            "group_id": None,
            "title": "AWS Introduction",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Batch not found"


def test_schedule_training_session_missing_group():
    reset_mock_db()

    def get_side_effect(model, object_id):
        if model is TrainingProgram:
            return make_program()

        if model is Faculty:
            return make_faculty()

        if model is Batch:
            return make_batch()

        if model is Group:
            return None

        return None

    mock_db.get.side_effect = get_side_effect

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 1,
            "batch_id": 1,
            "group_id": 999,
            "title": "AWS Introduction",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Group not found"


def test_schedule_training_session_invalid_times():
    reset_mock_db()

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 1,
            "batch_id": 1,
            "group_id": None,
            "title": "Invalid Session",
            "start_at": "2026-08-15T12:00:00",
            "end_at": "2026-08-15T10:00:00",
            "hours": 2,
        },
    )

    assert response.status_code == 422

    assert any(
        error["msg"]
        == "Value error, end_at must be later than start_at"
        for error in response.json()["detail"]
    )


def test_schedule_training_session_invalid_hours():
    reset_mock_db()

    response = client.post(
        "/api/v1/training/sessions",
        json={
            "program_id": 1,
            "faculty_id": 1,
            "batch_id": 1,
            "group_id": None,
            "title": "Invalid Session",
            "start_at": "2026-08-15T10:00:00",
            "end_at": "2026-08-15T12:00:00",
            "hours": 0,
        },
    )

    assert response.status_code == 422


# -------------------------------------------------------------------
# Training Session - Get
# -------------------------------------------------------------------

def test_get_training_sessions():
    reset_mock_db()

    mock_db.scalars.return_value.all.return_value = [
        make_session()
    ]

    response = client.get(
        "/api/v1/training/sessions",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["program_id"] == 1


def test_get_training_session():
    reset_mock_db()

    mock_db.get.return_value = make_session()

    response = client.get(
        "/api/v1/training/sessions/1",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "AWS Introduction"


def test_get_training_session_not_found():
    reset_mock_db()

    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/training/sessions/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training session not found"


# -------------------------------------------------------------------
# Training Completion
# -------------------------------------------------------------------

def test_get_training_completion():
    reset_mock_db()

    program = make_program()

    sessions = [
        TrainingSession(
            id=1,
            program_id=1,
            batch_id=1,
            group_id=None,
            title="Introduction",
            faculty_id=1,
            start_at=datetime(2026, 8, 15, 10, 0),
            end_at=datetime(2026, 8, 15, 12, 0),
            hours=2,
        ),
        TrainingSession(
            id=2,
            program_id=1,
            batch_id=1,
            group_id=None,
            title="EC2",
            faculty_id=1,
            start_at=datetime(2026, 8, 16, 10, 0),
            end_at=datetime(2026, 8, 16, 13, 0),
            hours=3,
        ),
    ]

    mock_db.get.return_value = program
    mock_db.scalars.return_value.all.return_value = sessions

    response = client.get(
        "/api/v1/training/programs/1/completion",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["program_id"] == 1
    assert data["planned_hours"] == 40
    assert data["completed_hours"] == 5
    assert data["completion_percentage"] == 12.5
    assert data["session_count"] == 2


def test_get_training_completion_program_not_found():
    reset_mock_db()

    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/training/programs/999999/completion",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training program not found"