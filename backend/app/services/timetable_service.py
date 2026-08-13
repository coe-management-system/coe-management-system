from typing import List, Dict, Any

def get_timetable_conflicts_mock() -> List[Dict[str, Any]]:
    """
    Status: Interface Available
    Implementation: Pending Backend Service (Member 3)
    MOCK implementation for timetable conflicts.
    """
    return [
        {"conflict_type": "room_double_booked", "details": "Room 301 at 10 AM"}
    ]

def run_what_if_mock(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Status: Interface Available
    Implementation: Pending Backend Service (Member 3)
    MOCK implementation for what-if scheduling scenario.
    """
    return {
        "scenario": parameters,
        "feasibility": "Low",
        "new_conflicts": 3
    }
