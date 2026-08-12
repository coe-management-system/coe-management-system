from typing import List, Dict, Any, Optional

# Mock Data
mock_students = [
    {
        "roll_no": "CSE101",
        "name": "Rahul",
        "attendance": 68,
        "department": "Computer Science"
    },
    {
        "roll_no": "CSE102",
        "name": "Aman",
        "attendance": 72,
        "department": "Computer Science"
    }
]

def get_students() -> List[Dict[str, Any]]:
    """
    Returns a list of all students.
    """
    return mock_students

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns information about a specific student by their roll number/student ID.
    """
    for student in mock_students:
        if student["roll_no"].lower() == student_id.lower():
            return student
    return None
