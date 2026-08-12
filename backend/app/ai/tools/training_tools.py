from typing import Dict, Any, Optional

mock_training = {
    "CSE101": {"status": "In Progress", "module": "Advanced Python", "completion_percentage": 60},
    "CSE102": {"status": "Completed", "module": "Data Structures", "completion_percentage": 100}
}

def get_training_status(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the training status for a given student ID.
    """
    return mock_training.get(student_id.upper())
