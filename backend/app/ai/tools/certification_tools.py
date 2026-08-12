from typing import Dict, Any, Optional

mock_certifications = {
    "CSE101": {"certification": "AWS Cloud Practitioner", "status": "Not Started"},
    "CSE102": {"certification": "AWS Cloud Practitioner", "status": "Certified"}
}

def get_certification_status(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the certification status for a given student ID.
    """
    return mock_certifications.get(student_id.upper())
