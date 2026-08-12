from typing import Dict, Optional

def get_certification_status(student_id: str) -> Optional[Dict]:
    """
    Returns the certification status for a specific student.
    """
    return {
        "student_id": student_id,
        "certification_name": "AWS Cloud Practitioner",
        "status": "Not Started"
    }
