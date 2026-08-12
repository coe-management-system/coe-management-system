def get_students():
    """
    Returns a list of all students.
    """
    # Mock data for prototype.
    # In production, this will call the FastAPI/service layer connected to PostgreSQL.
    return [
        {
            "roll_no": "CSE101",
            "name": "Rahul",
            "attendance": 68
        },
        {
            "roll_no": "CSE102",
            "name": "Aman",
            "attendance": 72
        },
        {
            "roll_no": "CSE103",
            "name": "Priya",
            "attendance": 90
        }
    ]

def get_student(student_id: str):
    """
    Returns detailed information about a specific student.
    """
    # Mock data for prototype.
    students = get_students()
    for student in students:
        if student["roll_no"] == student_id:
            return student
    return {"error": f"Student with ID {student_id} not found."}
