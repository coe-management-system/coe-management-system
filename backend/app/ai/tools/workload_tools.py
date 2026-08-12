from typing import Dict, Optional

def get_faculty_workload(faculty_id: int) -> Optional[Dict]:
    """
    Returns the workload for a specific faculty member.
    """
    return {
        "faculty_id": faculty_id,
        "allocated_hours": 32,
        "completed_hours": 24,
        "remaining_hours": 8
    }
