import pytest
from app.ai.tools.registry import registry

def test_get_student_missing_parameter():
    result = registry.execute("get_student")
    assert result.success is False
    assert "Missing required parameter: student_id" in result.error

def test_get_faculty_workload_invalid_parameter():
    result = registry.execute("get_faculty_workload", faculty_id="invalid")
    assert result.success is False
    assert result.error is not None
    assert "invalid" in result.error.lower()

def test_get_training_status_pending():
    result = registry.execute("get_training_status", student_id="CSE101")
    assert result.success is False
    assert "pending implementation" in result.error
    assert result.metadata["service"] == "training_service_pending"

def test_get_low_attendance_students():
    result = registry.execute("get_low_attendance_students")
    assert result.success is True
    assert len(result.data) > 0
    assert result.data[0]["roll_no"] == "CSE101"
