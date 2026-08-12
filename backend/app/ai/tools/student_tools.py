from typing import List, Dict, Optional

def get_students() -> List[Dict]:
    """
    Returns a list of all students (mock data for prototype).
    """
    return [
        {"roll_no": "CSE101", "name": "Rahul", "department": "CSE"},
        {"roll_no": "CSE102", "name": "Aman", "department": "CSE"}
    ]

def get_student(student_id: str) -> Optional[Dict]:
    """
    Returns information about a specific student.
    """
    students = get_students()
    for student in students:
        if student["roll_no"] == student_id:
            return student
    return None
