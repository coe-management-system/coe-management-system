from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.import_service import ImportService


def create_db():
    db = MagicMock()

    def add_side_effect(obj):
        # Simulate SQLAlchemy assigning an ID after flush.
        if obj.__class__.__name__ == "ImportJob":
            obj.id = 1

    db.add.side_effect = add_side_effect
    return db


def create_department():
    department = MagicMock()
    department.id = 1
    department.code = "CSE"
    return department


def create_batch():
    batch = MagicMock()
    batch.id = 1
    batch.year = 2026
    batch.department_id = 1
    return batch


def create_group():
    group = MagicMock()
    group.id = 1
    group.name = "4A"
    group.batch_id = 1
    return group


@patch("app.services.import_service.run_import")
def test_successful_student_import(mock_run_import, tmp_path):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE999",
                "name": "New Student",
                "email": "new@example.com",
                "department": "CSE",
                "batch": "2026",
                "group": "4A",
            }
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [],
    }

    db = create_db()

    department = create_department()
    batch = create_batch()
    group = create_group()

    db.scalar.side_effect = [
        department,
        batch,
        group,
        None,
    ]

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["total_rows"] == 1
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 0
    assert result["duplicate_rows"] == 0

    assert result["imported_students"] == ["CSE999"]
    assert result["skipped_existing"] == []
    assert result["reference_errors"] == []
    assert result["validation_errors"] == []

    db.commit.assert_called_once()

    assert not file_path.exists()


@patch("app.services.import_service.run_import")
def test_existing_student_is_skipped(mock_run_import, tmp_path):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE102",
                "name": "Existing Student",
                "email": "existing@example.com",
                "department": "CSE",
                "batch": "2026",
                "group": "4A",
            }
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [],
    }

    db = create_db()

    department = create_department()
    batch = create_batch()
    group = create_group()
    existing_student = MagicMock()

    db.scalar.side_effect = [
        department,
        batch,
        group,
        existing_student,
    ]

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["imported_students"] == []
    assert result["skipped_existing"] == ["CSE102"]

    db.commit.assert_called_once()


@patch("app.services.import_service.run_import")
def test_missing_department_creates_reference_error(
    mock_run_import,
    tmp_path,
):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE103",
                "name": "Student",
                "email": "student@example.com",
                "department": "IT",
                "batch": "2026",
                "group": "4B",
            }
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [],
    }

    db = create_db()

    # Department lookup returns nothing.
    db.scalar.return_value = None

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["imported_students"] == []

    assert result["reference_errors"] == [
        {
            "roll_no": "CSE103",
            "field": "department",
            "value": "IT",
            "error": "Department not found",
        }
    ]

    db.commit.assert_called_once()


@patch("app.services.import_service.run_import")
def test_duplicate_record_is_not_imported(
    mock_run_import,
    tmp_path,
):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE101",
                "name": "Rahul Kumar",
                "email": "rahul@example.com",
                "department": "CSE",
                "batch": "2026",
                "group": "4A",
            },
            {
                "roll_no": "CSE101",
                "name": "Rahul K",
                "email": "rahulk@example.com",
                "department": "CSE",
                "batch": "2026",
                "group": "4A",
            },
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [
            {
                "roll_no": "CSE101",
                "rows": [2, 9],
            }
        ],
    }

    db = create_db()

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["total_rows"] == 2
    assert result["valid_rows"] == 2
    assert result["duplicate_rows"] == 1
    assert result["imported_students"] == []

    # No database reference lookups should happen because
    # the records were identified as duplicates first.
    db.scalar.assert_not_called()


@patch("app.services.import_service.run_import")
def test_validation_errors_are_preserved(
    mock_run_import,
    tmp_path,
):
    validation_errors = [
        {
            "row": 6,
            "field": "department",
            "error": "Missing required field: department",
        },
        {
            "row": 7,
            "field": "email",
            "error": "Invalid email format",
        },
    ]

    mock_run_import.return_value = {
        "valid_records": [],
        "invalid_records": [
            {
                "roll_no": "CSE105",
                "name": "Karan Mehta",
                "email": "karan@example.com",
            }
        ],
        "errors": validation_errors,
        "duplicates": [],
    }

    db = create_db()

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["total_rows"] == 1
    assert result["valid_rows"] == 0
    assert result["invalid_rows"] == 1
    assert result["validation_errors"] == validation_errors

    db.commit.assert_called_once()


@patch("app.services.import_service.run_import")
def test_missing_batch_creates_reference_error(
    mock_run_import,
    tmp_path,
):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE110",
                "name": "Student",
                "email": "student@example.com",
                "department": "CSE",
                "batch": "2030",
                "group": "4A",
            }
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [],
    }

    db = create_db()

    department = create_department()

    db.scalar.side_effect = [
        department,
        None,
    ]

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["imported_students"] == []

    assert result["reference_errors"] == [
        {
            "roll_no": "CSE110",
            "field": "batch",
            "value": "2030",
            "error": "Batch not found",
        }
    ]


@patch("app.services.import_service.run_import")
def test_missing_group_creates_reference_error(
    mock_run_import,
    tmp_path,
):
    mock_run_import.return_value = {
        "valid_records": [
            {
                "roll_no": "CSE111",
                "name": "Student",
                "email": "student@example.com",
                "department": "CSE",
                "batch": "2026",
                "group": "9Z",
            }
        ],
        "invalid_records": [],
        "errors": [],
        "duplicates": [],
    }

    db = create_db()

    department = create_department()
    batch = create_batch()

    # Department → Batch → Group lookup → fallback Group lookup
    db.scalar.side_effect = [
        department,
        batch,
        None,
        None,
    ]

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    result = ImportService.process_student_file(
        db=db,
        file_path=str(file_path),
        filename="students.xlsx",
        created_by=2,
    )

    assert result["status"] == "completed"
    assert result["imported_students"] == []

    assert result["reference_errors"] == [
        {
            "roll_no": "CSE111",
            "field": "group",
            "value": "9Z",
            "error": "Group not found",
        }
    ]


@patch("app.services.import_service.run_import")
def test_import_failure_rolls_back(
    mock_run_import,
    tmp_path,
):
    mock_run_import.side_effect = RuntimeError(
        "Excel processing failed"
    )

    db = create_db()

    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    with pytest.raises(HTTPException) as exc_info:
        ImportService.process_student_file(
            db=db,
            file_path=str(file_path),
            filename="students.xlsx",
            created_by=2,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Student import failed"

    db.rollback.assert_called_once()

    assert not file_path.exists()