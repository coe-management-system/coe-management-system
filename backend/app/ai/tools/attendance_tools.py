from typing import List, Dict

def get_low_attendance_students() -> List[Dict]:
    """
    Returns a list of students with attendance below 75%.
    """
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
        }
    ]
