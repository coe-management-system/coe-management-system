from app.ai.assistant import run_assistant_query

def test_grounding_tool_returns_data():
    # Uses mock attendance
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "Found 2 record(s)" in response["response"]

def test_grounding_tool_returns_empty(monkeypatch):
    # We patch the mock to return empty list
    import app.ai.tools.attendance_tools
    monkeypatch.setattr(app.ai.tools.attendance_tools, "get_low_attendance_students_mock", lambda: [])
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "No matching records found" in response["response"]

def test_grounding_tool_failure(monkeypatch):
    def raise_error():
        raise Exception("DB Failure")
    
    import app.ai.tools.attendance_tools
    monkeypatch.setattr(app.ai.tools.attendance_tools, "get_low_attendance_students_mock", raise_error)
    response = run_assistant_query("Which students are below 75% attendance?")
    assert "Unable to retrieve requested information" in response["response"]
    assert "Attendance service unavailable" in response["response"]
