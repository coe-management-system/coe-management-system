from typing import Dict, Any, Optional

mock_workload = {
    "12": {
        "faculty_id": 12,
        "allocated_hours": 32,
        "completed_hours": 24,
        "remaining_hours": 8
    }
}

def get_faculty_workload(faculty_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the workload details for a given faculty member ID.
    """
    return mock_workload.get(str(faculty_id))
