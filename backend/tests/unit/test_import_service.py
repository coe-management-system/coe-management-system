import json
from unittest.mock import MagicMock, patch

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


def make_import_job(status=ImportStatus.CREATED, file_path="dummy.xlsx", validation_result=None):
    job = MagicMock()
    job.id = 1
    job.status = status
    job.file_path = file_path
    job.validation_result = validation_result
    job.file_hash = "abc123"
    job.filename = "students.xlsx"
    return job


def create_department(dept_id=1, code="CSE"):
    d = MagicMock()
    d.id = dept_id
    d.code = code
    return d


def create_batch(batch_id=1, year=2026, department_id=1):
    b = MagicMock()
    b.id = batch_id
    b.year = year
    b.department_id = department_id
    return b


def create_group(group_id=1, name="4A", batch_id=1):
    g = MagicMock()
    g.id = group_id
    g.name = name
    g.batch_id = batch_id
    return g


# ---------- create_import ----------

@patch("app.services.import_service.ImportService.compute_file_hash", return_value="hash123")
def test_create_import_registers_job(mock_hash, tmp_path):
    db = create_db()
    file_path = tmp_path / "students.xlsx"
    file_path.write_bytes(b"test")

    job = ImportService.create_import(
        db=db, file_path=str(file_path), filename="students.xlsx", created_by=2
    )

    assert job.status == ImportStatus.CREATED
    assert job.file_hash == "hash123"
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ---------- validate_import ----------

@patch("app.services.import_service.read_excel")
def test_validate_import_marks_valid_record_accepted(mock_read_excel):
    db = create_db()
    db.scalar.side_effect = [
        create_department(), create_batch(), create_group(), None,  # no existing student
    ]

    df = make_df(
        [["CSE101", "Rahul Kumar", "rahul@example.com", "CSE", "2026", "4A"]],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)

    assert job.status == ImportStatus.PREVIEW_READY
    assert result["summary"]["valid"] == 1
    assert result["summary"]["ready_to_commit"] == 1
    assert result["records"][0]["category"] == "VALID"


@patch("app.services.import_service.read_excel")
def test_validate_import_flags_invalid_email(mock_read_excel):
    db = create_db()

    df = make_df(
        [["CSE102", "Priya", "not-an-email", "CSE", "2026", "4A"]],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)

    assert result["summary"]["invalid"] == 1
    assert result["records"][0]["category"] == "INVALID"
    assert any(e["field"] == "email" for e in result["records"][0]["field_errors"])


@patch("app.services.import_service.read_excel")
def test_validate_import_flags_unknown_department_as_reference_error(mock_read_excel):
    db = create_db()
    db.scalar.return_value = None  # department lookup fails

    df = make_df(
        [["CSE103", "Aman", "aman@example.com", "XYZ", "2026", "4A"]],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)

    assert result["summary"]["reference_errors"] == 1
    assert result["records"][0]["category"] == "REFERENCE_ERROR"
    assert result["records"][0]["reference_errors"][0]["error_code"] == "UNKNOWN_DEPARTMENT"


@patch("app.services.import_service.read_excel")
def test_validate_import_flags_existing_student(mock_read_excel):
    db = create_db()
    existing = MagicMock()
    existing.id = 99
    db.scalar.side_effect = [create_department(), create_batch(), create_group(), existing]

    df = make_df(
        [["CSE104", "Neha", "neha@example.com", "CSE", "2026", "4A"]],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)

    assert result["summary"]["existing"] == 1
    assert result["records"][0]["category"] == "EXISTING"


@patch("app.services.import_service.read_excel")
def test_validate_import_flags_duplicate_in_file(mock_read_excel):
    db = create_db()
    db.scalar.side_effect = [
        create_department(), create_batch(), create_group(), None,
        create_department(), create_batch(), create_group(), None,
    ]

    df = make_df(
        [
            ["CSE105", "Rahul", "rahul@example.com", "CSE", "2026", "4A"],
            ["CSE105", "Rahul K", "rahulk@example.com", "CSE", "2026", "4A"],
        ],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)

    assert result["summary"]["duplicates"] == 1
    categories = [r["category"] for r in result["records"]]
    assert "DUPLICATE" in categories


def test_validate_import_rejects_wrong_status():
    db = create_db()
    job = make_import_job(status=ImportStatus.COMMITTED)

    with pytest.raises(ValueError):
        ImportService.validate_import(db, job)


@patch("app.services.import_service.read_excel", side_effect=RuntimeError("corrupt file"))
def test_validate_import_marks_failed_on_exception(mock_read_excel):
    db = create_db()
    job = make_import_job()

    with pytest.raises(RuntimeError):
        ImportService.validate_import(db, job)

    assert job.status == ImportStatus.FAILED


# ---------- commit_import ----------

def test_commit_import_inserts_only_valid_records():
    db = create_db()
    validation_payload = {
        "records": [
            {"row": 2, "category": "VALID", "roll_no": "CSE101", "name": "Rahul", "email": "rahul@example.com",
             "resolved_department_id": 1, "resolved_batch_id": 1, "resolved_group_id": 1},
            {"row": 3, "category": "INVALID", "roll_no": "CSE102", "name": "Bad", "email": "bad"},
            {"row": 4, "category": "EXISTING", "roll_no": "CSE103", "name": "Existing", "email": "e@example.com"},
        ]
    }
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=json.dumps(validation_payload))

    result = ImportService.commit_import(db, job)

    assert job.status == ImportStatus.COMMITTED
    assert result["imported_count"] == 1
    assert result["imported_students"] == ["CSE101"]
    db.add.assert_called_once()
    db.commit.assert_called()


def test_commit_import_rejects_wrong_status():
    db = create_db()
    job = make_import_job(status=ImportStatus.CREATED)

    with pytest.raises(ValueError):
        ImportService.commit_import(db, job)


def test_commit_import_rejects_missing_validation_result():
    db = create_db()
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=None)

    with pytest.raises(ValueError):
        ImportService.commit_import(db, job)


def test_commit_import_rolls_back_on_failure():
    db = create_db()

    def add_side_effect(obj):
        if obj.__class__.__name__ == "Student":
            raise RuntimeError("constraint violation")

    db.add.side_effect = add_side_effect

    validation_payload = {
        "records": [
            {"row": 2, "category": "VALID", "roll_no": "CSE101", "name": "Rahul", "email": "rahul@example.com",
             "resolved_department_id": 1, "resolved_batch_id": 1, "resolved_group_id": 1},
        ]
    }
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=json.dumps(validation_payload))

    with pytest.raises(RuntimeError):
        ImportService.commit_import(db, job)

    db.rollback.assert_called_once()
    assert job.status == ImportStatus.FAILED


@patch("app.services.import_service.read_excel")
def test_validate_import_summary_counts_are_internally_consistent(mock_read_excel):
    db = create_db()
    db.scalar.side_effect = [
        create_department(), create_batch(), create_group(), None,  # row 1: VALID
        None,  # row 2: unknown department -> REFERENCE_ERROR
    ]

    df = make_df(
        [
            ["CSE101", "Rahul Kumar", "rahul@example.com", "CSE", "2026", "4A"],
            ["CSE102", "Priya Singh", "not-an-email", "XX", "2026", "4A"],
        ],
        ["roll_no", "name", "email", "department", "batch", "group"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_import(db, job)
    summary = result["summary"]

    total_from_categories = (
        summary["valid"] + summary["invalid"] + summary["reference_errors"]
        + summary["existing"] + summary["duplicates"]
    )
    assert total_from_categories == summary["total_rows"]
    assert summary["ready_to_commit"] == summary["valid"]


@patch("app.services.import_service.read_excel")
def test_validate_department_import_summary_counts_are_internally_consistent(mock_read_excel):
    db = create_db()
    db.scalar.side_effect = [None]  # no existing department for the one valid row

    df = make_df(
        [["CSE", "Computer Science"]],
        ["code", "name"],
    )
    mock_read_excel.return_value = df

    job = make_import_job()
    result = ImportService.validate_department_import(db, job)
    summary = result["summary"]

    total_from_categories = (
        summary["valid"] + summary["invalid"] + summary["reference_errors"]
        + summary["existing"] + summary["duplicates"]
    )
    assert total_from_categories == summary["total_rows"]
    assert summary["ready_to_commit"] == summary["valid"]


@patch("app.services.import_service.read_excel")
def test_repeated_commit_on_committed_job_is_rejected(mock_read_excel):
    validation_payload = {
        "records": [
            {"roll_no": "CSE101", "name": "Rahul", "email": "rahul@example.com",
             "category": "VALID", "resolved_department_id": 1, "resolved_batch_id": 1, "resolved_group_id": 1},
        ],
    }
    db = create_db()
    job = make_import_job(status=ImportStatus.COMMITTED, validation_result=json.dumps(validation_payload))

    with pytest.raises(ValueError, match="Cannot commit import in status .committed."):
        ImportService.commit_import(db, job)


def test_concurrent_commit_second_caller_rejected_after_first_succeeds():
    """
    Simulates two callers holding references to the same PREVIEW_READY job.
    The first commit succeeds and flips status to COMMITTED; the second
    commit attempt on the same (now-committed) job object must be rejected
    by the status guard rather than double-inserting records.

    Note: this proves the in-process status-guard protection. It does not
    exercise true multi-connection/multi-process database-level concurrency
    (e.g. a race via separate sessions with no row lock), which would need
    a live Postgres instance and is a documented follow-up, not covered here.
    """
    validation_payload = {
        "records": [
            {"roll_no": "CSE101", "name": "Rahul", "email": "rahul@example.com",
             "category": "VALID", "resolved_department_id": 1, "resolved_batch_id": 1, "resolved_group_id": 1},
        ],
    }
    db = create_db()
    job = make_import_job(status=ImportStatus.PREVIEW_READY, validation_result=json.dumps(validation_payload))

    result_a = ImportService.commit_import(db, job)
    assert result_a["status"] == ImportStatus.COMMITTED
    assert job.status == ImportStatus.COMMITTED

    with pytest.raises(ValueError, match="Cannot commit import in status .committed."):
        ImportService.commit_import(db, job)


def test_no_response_schema_exposes_file_path():
    """
    Security regression guard: ensure no import response schema ever
    exposes the server-side file_path, only the safe file_hash digest.
    """
    from app.schemas import import_schema
    import inspect

    source = inspect.getsource(import_schema)
    assert "file_path" not in source
