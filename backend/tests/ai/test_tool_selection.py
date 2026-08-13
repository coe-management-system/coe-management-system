from app.ai.assistant import run_assistant_query

def test_tool_selection_student(monkeypatch):
    import app.ai.tools.student_tools
    from app.models.student import Student
    
    # Mock the DB call with a fully valid Student to pass Pydantic validation
    monkeypatch.setattr(app.ai.tools.student_tools, "get_student_by_roll_no", lambda db, roll_no: Student(id=1, roll_no=roll_no, name="Rahul", email="rahul@example.com", department_id=1, batch_id=1, group_id=1))

    response = run_assistant_query("Tell me about CSE101")
    assert response["result"]["metadata"]["tool"] == "get_student"
    assert response["result"]["success"] is True

def test_tool_selection_attendance():
    response = run_assistant_query("Who has attendance below 75%?")
    assert response["result"]["metadata"]["tool"] == "get_low_attendance_students"

def test_tool_selection_workload():
    response = run_assistant_query("What is faculty 12's workload?")
    assert response["result"]["metadata"]["tool"] == "get_faculty_workload"

def test_tool_selection_conflicts():
    response = run_assistant_query("Are there timetable conflicts?")
    assert response["result"]["metadata"]["tool"] == "get_timetable_conflicts"
