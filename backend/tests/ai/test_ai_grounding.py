from app.ai.assistant import run_assistant_query
from app.ai.tools.registry import registry, ToolResult

def test_grounding_tool_returns_data(monkeypatch):
    dummy_data = [{"roll_no": "CSE101", "name": "Rahul", "attendance_percentage": 68.0}]
    tool = registry.get_tool("get_low_attendance_students")
    monkeypatch.setattr(
        tool, 
        "executor", 
        lambda **kwargs: ToolResult(success=True, data=dummy_data, metadata={"source": "postgresql"})
    )
    
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "Found 1 record(s)" in response["response"]

def test_grounding_tool_returns_empty(monkeypatch):
    tool = registry.get_tool("get_low_attendance_students")
    monkeypatch.setattr(
        tool, 
        "executor", 
        lambda **kwargs: ToolResult(success=True, data=[], metadata={"source": "postgresql"})
    )
    
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "No matching records found" in response["response"]

def test_grounding_tool_failure(monkeypatch):
    tool = registry.get_tool("get_low_attendance_students")
    monkeypatch.setattr(
        tool, 
        "executor", 
        lambda **kwargs: ToolResult(success=False, error="Attendance service unavailable", data=None, metadata={"source": "postgresql"})
    )
    
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "Unable to retrieve requested information" in response["response"]
    assert "Attendance service unavailable" in response["response"]
