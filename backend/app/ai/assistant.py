"""
AI Assistant Module - Prototype
Architecture:
User -> AI Assistant -> Controlled AI Tool -> Service Layer -> Database
The AI must NOT connect to PostgreSQL directly.
"""
from typing import Dict, Any

from app.ai.tools.registry import registry
# We need to import the tool modules to ensure the tools get registered
import app.ai.tools.student_tools
import app.ai.tools.attendance_tools
import app.ai.tools.training_tools
import app.ai.tools.certification_tools
import app.ai.tools.workload_tools
import app.ai.tools.scheduling_tools

def run_assistant_query(user_query: str) -> Dict[str, Any]:
    """
    Simulates the AI mapping a natural language query to the Tool Registry.
    In a real system, the LLM decides which tool to call based on `registry._tools` descriptions.
    """
    tool_name = None
    kwargs = {}

    # Demonstration routing - simulating LLM tool selection
    query_lower = user_query.lower()
    
    if "cse101" in query_lower:
        tool_name = "get_student"
        kwargs = {"student_id": "CSE101"}
    elif "cse999" in query_lower:
        tool_name = "get_student"
        kwargs = {"student_id": "CSE999"}
    elif "which students" in query_lower or "who has attendance" in query_lower:
        tool_name = "get_low_attendance_students"
    elif "workload of faculty" in query_lower or "faculty 12's workload" in query_lower:
        tool_name = "get_faculty_workload"
        kwargs = {"faculty_id": 12}
    elif "conflicts" in query_lower:
        tool_name = "get_timetable_conflicts"
    else:
        # Default behavior or unknown query
        return {"response": "I didn't understand that query or no tool is available.", "data": None}

    # Execute via registry
    result = registry.execute(tool_name, **kwargs)
    
    # Simulate LLM grounding the response based on the structured tool result
    if result.success:
        if result.data:
            # Fake LLM processing the returned data
            if isinstance(result.data, list):
                response_text = f"Found {len(result.data)} record(s) matching your request."
            else:
                response_text = "Here is the information you requested."
        else:
            response_text = "No matching records found."
    else:
        response_text = f"Unable to retrieve requested information. Reason: {result.error}"

    return {
        "response": response_text,
        "result": result.model_dump(mode="json")
    }
