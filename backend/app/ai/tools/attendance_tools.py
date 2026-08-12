def get_low_attendance_students():
    """
    Returns a list of students with attendance below 75%.
    """
    # Mock data as requested for the prototype.
    # In production, this will call the FastAPI/service layer connected to PostgreSQL.
    mock_students = [
        {
            "roll_no": "CSE101",
            "name": "Rahul",
            "attendance": 68
        },
        {
            "roll_no": "CSE102",
            "name": "Aman",
            "attendance": 72
        }
    ]
    return mock_students
