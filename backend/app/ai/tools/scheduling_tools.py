from typing import List, Dict, Any

def get_timetable_conflicts() -> List[Dict]:
    """
    Returns a list of current timetable conflicts.
    """
    return [
        {
            "faculty": "Faculty A",
            "time": "10:00-11:00",
            "subject_1": "Python",
            "subject_2": "DBMS",
            "conflict_type": "faculty_conflict"
        }
    ]

def run_what_if(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a what-if scheduling scenario based on parameters.
    """
    return {
        "status": "success",
        "message": "What-if scenario executed successfully with mock data.",
        "simulated_conflicts": 0,
        "parameters_used": parameters
    }
