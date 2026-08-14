"""
AI Assistant Module - Production Orchestrator
Architecture:
User Query -> Prompt Injection Defense -> Context Resolution -> RBAC Tool Registry -> Service Layer -> Database
The AI must NOT connect to PostgreSQL directly.
"""
import re
from typing import Dict, Any, Optional

from app.ai.tools.registry import registry, ToolResult
# Import tool modules to ensure registration
import app.ai.tools.student_tools
import app.ai.tools.attendance_tools
import app.ai.tools.training_tools
import app.ai.tools.certification_tools
import app.ai.tools.workload_tools
import app.ai.tools.scheduling_tools

# Module-level active conversation context storage (resets or updates per session)
_conversation_context: Dict[str, Any] = {}

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?permissions",
    r"bypass\s+rbac",
    r"ignore\s+(system\s+)?instructions",
    r"override\s+security",
    r"system\s+prompt",
    r"as\s+admin",
    r"disable\s+safety",
    r"forget\s+rules",
]


def detect_prompt_injection(user_query: str) -> bool:
    """Detects adversarial prompt injection attempts designed to bypass security controls."""
    query_lower = user_query.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    return False


def run_assistant_query(
    user_query: str,
    user_role: str = "FACULTY",
    session_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestrates natural language query mapping, prompt injection defense,
    context resolution, multi-tool aggregation, and RBAC-controlled tool execution.
    """
    global _conversation_context
    ctx = session_context if session_context is not None else _conversation_context

    # 1. Security Check: Prompt Injection Defense
    if detect_prompt_injection(user_query):
        result = ToolResult(
            success=False,
            data=None,
            error="Prompt injection detected. Request denied by Security Guard.",
            metadata={"security_event": "prompt_injection_blocked", "status": "DENIED"}
        )
        return {
            "response": "Security Alert: Prompt injection attempt detected. System permissions and RBAC remain strictly enforced.",
            "result": result.model_dump(mode="json")
        }

    query_lower = user_query.lower()

    # 2. Multi-Tool Aggregation Routing (Scenario 3)
    if ("below 75%" in query_lower or "low attendance" in query_lower) and ("training" in query_lower or "incomplete" in query_lower):
        # Step A: Execute Attendance Tool
        att_res = registry.execute("get_low_attendance_students", user_role=user_role, threshold=75.0)
        if not att_res.success:
            return {
                "response": f"Unable to complete request. Attendance tool failed: {att_res.error}",
                "result": att_res.model_dump(mode="json")
            }

        low_att_students = att_res.data or []
        combined_data = []

        # Step B: Execute Training Tool for low attendance students
        for student_info in low_att_students:
            roll_no = student_info.get("roll_no") or str(student_info.get("student_id"))
            tr_res = registry.execute("get_training_status", user_role=user_role, student_id=roll_no)
            
            if tr_res.success and tr_res.data:
                tr_status = tr_res.data.get("status", "").upper()
                if tr_status in ("INCOMPLETE", "PENDING") or not tr_res.data.get("training_completed", False):
                    combined_item = {**student_info, "training_status": tr_status}
                    combined_data.append(combined_item)

        aggregated_result = ToolResult(
            success=True,
            data=combined_data,
            metadata={
                "tools_aggregated": ["get_low_attendance_students", "get_training_status"],
                "source": "postgresql",
                "count": len(combined_data)
            }
        )

        response_text = (
            f"Found {len(combined_data)} student(s) with attendance below 75% and incomplete training."
            if combined_data else "No students found matching both low attendance (<75%) and incomplete training."
        )

        return {
            "response": response_text,
            "result": aggregated_result.model_dump(mode="json")
        }

    # 3. Tool Selection & Context Resolution
    tool_name = None
    kwargs = {}

    # Extract explicit student ID if present
    student_match = re.search(r"cse\d+", query_lower)
    explicit_student_id = student_match.group(0).upper() if student_match else None

    if explicit_student_id:
        ctx["last_student_id"] = explicit_student_id

    # Check for pronominal context resolution ("his", "their", "the student", "this student")
    is_context_referential = any(ref in query_lower for ref in ["his", "her", "their", "this student", "the student"])
    
    if is_context_referential and "attendance" in query_lower and "last_student_id" in ctx:
        tool_name = "get_student_attendance"
        kwargs = {"student_id": ctx["last_student_id"]}
    elif "attendance" in query_lower and explicit_student_id:
        tool_name = "get_student_attendance"
        kwargs = {"student_id": explicit_student_id}
    elif explicit_student_id or "tell me about" in query_lower or "student info" in query_lower:
        tool_name = "get_student"
        kwargs = {"student_id": explicit_student_id or "CSE101"}
    elif "which students" in query_lower or "who has attendance" in query_lower:
        tool_name = "get_low_attendance_students"
    elif "workload" in query_lower or "faculty" in query_lower:
        tool_name = "get_faculty_workload"
        # Extract faculty ID if given, else default to 12
        fac_match = re.search(r"faculty\s*(\d+)", query_lower)
        kwargs = {"faculty_id": int(fac_match.group(1)) if fac_match else 12}
    elif "conflicts" in query_lower or "timetable" in query_lower:
        tool_name = "get_timetable_conflicts"
    else:
        return {
            "response": "I didn't understand that query or no appropriate tool is available.",
            "result": ToolResult(success=False, error="Unknown query or tool unavailable.", data=None).model_dump(mode="json")
        }

    # 4. Execute tool via Registry with RBAC enforcement
    result = registry.execute(tool_name, user_role=user_role, **kwargs)

    # Update context if student queried successfully
    if result.success and result.data and isinstance(result.data, dict) and "roll_no" in result.data:
        ctx["last_student_id"] = result.data["roll_no"]

    # 5. Format Grounded Response based on ToolResult
    if result.success:
        if result.data is not None:
            if isinstance(result.data, list):
                if len(result.data) == 0:
                    response_text = "No matching records found."
                else:
                    response_text = f"Found {len(result.data)} record(s) matching your request."
            else:
                response_text = f"Here is the requested information for {kwargs.get('student_id', 'the entity')}."
        else:
            response_text = "No matching records found."
    else:
        response_text = f"Unable to retrieve requested information. Reason: {result.error}"


    return {
        "response": response_text,
        "result": result.model_dump(mode="json")
    }
