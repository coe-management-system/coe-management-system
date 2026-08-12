"""
AI Assistant Module - Prototype
Architecture:
User -> AI Assistant -> Controlled AI Tool -> Service Layer -> Database
The AI must NOT connect to PostgreSQL directly.

Currently, this uses mock tools in the `tools/` directory.
"""
from typing import Dict, Any

from app.ai.tools.student_tools import get_students, get_student
from app.ai.tools.attendance_tools import get_low_attendance_students
from app.ai.tools.training_tools import get_training_status
from app.ai.tools.certification_tools import get_certification_status
from app.ai.tools.workload_tools import get_faculty_workload
from app.ai.tools.scheduling_tools import get_timetable_conflicts, run_what_if

def run_assistant_query(user_query: str) -> Dict[str, Any]:
    """
    Mock function to simulate AI parsing the query, selecting a tool, and returning a result.
    Member 5 will integrate the actual LLM calls here to map natural language to the tools above.
    """
    # Demonstration routing
    if "attendance" in user_query.lower():
        data = get_low_attendance_students()
        return {"response": f"Found {len(data)} students with low attendance.", "data": data}
    elif "cse101" in user_query.lower():
        data = get_student("CSE101")
        return {"response": f"Student details for CSE101.", "data": data}
    elif "workload of faculty" in user_query.lower():
        # Parsing would happen via LLM, hardcoded for demonstration
        data = get_faculty_workload(12)
        return {"response": "Workload for faculty 12.", "data": data}
    elif "conflicts" in user_query.lower():
        data = get_timetable_conflicts()
        return {"response": f"Found {len(data)} timetable conflicts.", "data": data}
    
    return {"response": "I didn't understand that query.", "data": None}
