from typing import List, Dict, Any

def get_low_attendance_students_mock() -> List[Dict[str, Any]]:
    """
    Status: Interface Available
    Implementation: Pending Backend Service
    MOCK implementation for retrieving low attendance students.
    """
    return [
        {"roll_no": "CSE101", "name": "Rahul", "attendance_percentage": 68},
        {"roll_no": "CSE102", "name": "Aman", "attendance_percentage": 72}
    ]
