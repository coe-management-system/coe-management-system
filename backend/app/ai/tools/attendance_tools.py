from typing import List, Dict, Any
from .student_tools import get_students

def get_low_attendance_students(threshold: int = 75) -> List[Dict[str, Any]]:
    """
    Returns a list of students with attendance below the given threshold.
    """
    all_students = get_students()
    return [s for s in all_students if s.get("attendance", 100) < threshold]
