from unittest.mock import MagicMock, patch
import json
import pandas as pd
import pytest

from app.services.import_service import ImportService, ImportStatus


def make_df(rows, columns):
    return pd.DataFrame(rows, columns=columns)


def create_db():
    db = MagicMock()

    def add_side_effect(obj):
        if obj.__class__.__name__ == "ImportJob":
            obj.id = 1

    db.add.side_effect = add_side_effect
    return db


def make_import_job(status=ImportStatus.CREATED, file_path="dummy.xlsx", validation_result=None, import_type="department"):
    job = MagicMock()
    job.id = 1
    job.status = status
    job.file_path = file_path
    job.validation_result = validation_result
    job.import_type = import_type
    return job


@patch("app.services.import_service.read_excel")
def test_validate_department_import_marks_valid(mock_read_excel):
    db = create_db()
    db.scalar.return_value = None  # no existing department

    df = make_df([["MECH", "Mechanical Engineering"]], ["Code", "Name"])
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)

    assert job.status == ImportStatus.PREVIEW_READY
    assert result["summary"]["valid"] == 1
    assert result["records"][0]["category"] == "VALID"


@patch("app.services.import_service.read_excel")
def test_validate_department_import_flags_missing_code(mock_read_excel):
    db = create_db()

    df = make_df([["", "No Code Dept"]], ["Code", "Name"])
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)

    assert result["summary"]["invalid"] == 1
    assert result["records"][0]["category"] == "INVALID"


@patch("app.services.import_service.read_excel")
def test_validate_department_import_flags_existing(mock_read_excel):
    db = create_db()
    existing = MagicMock()
    existing.id = 5
    db.scalar.return_value = existing

    df = make_df([["CSE", "Computer Science"]], ["Code", "Name"])
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)

    assert result["summary"]["existing"] == 1
    assert result["records"][0]["category"] == "EXISTING"


@patch("app.services.import_service.read_excel")
def test_validate_department_import_flags_duplicate_in_file(mock_read_excel):
    db = create_db()
    db.scalar.return_value = None

    df = make_df(
        [["MECH", "Mechanical"], ["MECH", "Mech Duplicate"]],
        ["Code", "Name"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)

    assert result["summary"]["duplicates"] == 1


@patch("app.services.import_service.read_excel")
def test_validate_department_import_classifies_unknown_column(mock_read_excel):
    db = create_db()
    db.scalar.return_value = None

    df = make_df([["MECH", "Mechanical", "555-1234"]], ["Code", "Name", "Phone"])
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)

    assert "Phone" in result["unmapped_columns"]


def test_commit_department_import_inserts_only_valid():
    db = create_db()
    validation_payload = {
        "records": [
            {"row": 2, "category": "VALID", "code": "MECH", "name": "Mechanical Engineering"},
            {"row": 3, "category": "INVALID", "code": "", "name": "Bad"},
            {"row": 4, "category": "EXISTING", "code": "CSE", "name": "Existing"},
        ]
    }
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=json.dumps(validation_payload))

    result = ImportService.commit_department_import(db, job)

    assert job.status == ImportStatus.COMMITTED
    assert result["imported_count"] == 1
    assert result["imported_students"] == ["MECH"]
    db.add.assert_called_once()


def test_commit_department_import_rejects_wrong_status():
    db = create_db()
    job = make_import_job(status=ImportStatus.CREATED)

    with pytest.raises(ValueError):
        ImportService.commit_department_import(db, job)


def test_commit_department_import_rolls_back_on_failure():
    db = create_db()

    def add_side_effect(obj):
        if obj.__class__.__name__ == "Department":
            raise RuntimeError("unique constraint violation")

    db.add.side_effect = add_side_effect

    validation_payload = {
        "records": [
            {"row": 2, "category": "VALID", "code": "MECH", "name": "Mechanical Engineering"},
        ]
    }
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=json.dumps(validation_payload))

    with pytest.raises(RuntimeError):
        ImportService.commit_department_import(db, job)

    db.rollback.assert_called_once()
    assert job.status == ImportStatus.FAILED


def test_dispatch_routes_to_department_validate():
    db = create_db()
    job = make_import_job(import_type="department")

    with patch("app.services.import_service.ImportService.validate_department_import") as mock_val:
        mock_val.return_value = {"summary": {}}
        ImportService.validate_import_dispatch(db, job)
        mock_val.assert_called_once_with(db, job)


def test_dispatch_routes_to_student_validate():
    db = create_db()
    job = make_import_job(import_type="student")

    with patch("app.services.import_service.ImportService.validate_import") as mock_val:
        mock_val.return_value = {"summary": {}}
        ImportService.validate_import_dispatch(db, job)
        mock_val.assert_called_once_with(db, job)