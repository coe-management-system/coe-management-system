import pytest
from app.ai.tools.registry import registry, ToolResult

def test_get_student_missing_parameter():
    result = registry.execute("get_student")
    assert result.success is False
    assert "Missing required parameter: student_id" in result.error

def test_get_faculty_workload_invalid_parameter():
    result = registry.execute("get_faculty_workload", faculty_id="invalid")
    assert result.success is False
    assert result.error is not None

def test_get_training_status_execution(monkeypatch):
    tool = registry.get_tool("get_training_status")
    monkeypatch.setattr(
        tool,
        "executor",
        lambda student_id, **kwargs: ToolResult(
            success=True,
            data={"roll_no": student_id, "status": "INCOMPLETE", "training_completed": False},
            metadata={"service": "training_service", "source": "postgresql"}
        )
    )
    result = registry.execute("get_training_status", student_id="CSE101")
    assert result.success is True
    assert result.data["roll_no"] == "CSE101"
    assert result.metadata["service"] == "training_service"

def test_get_low_attendance_students_execution(monkeypatch):
    dummy_data = [{"roll_no": "CSE101", "name": "Rahul", "attendance_percentage": 68.0}]
    tool = registry.get_tool("get_low_attendance_students")
    monkeypatch.setattr(
        tool,
        "executor",
        lambda **kwargs: ToolResult(success=True, data=dummy_data, metadata={"service": "attendance_service", "source": "postgresql"})
    )
    result = registry.execute("get_low_attendance_students")
    assert result.success is True
    assert len(result.data) > 0
    assert result.data[0]["roll_no"] == "CSE101"
