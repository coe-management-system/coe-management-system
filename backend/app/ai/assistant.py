"""
AI Assistant Module - Production Orchestrator (Day 4)
Architecture:
User Query -> Prompt Injection Defense -> Planner (Intent & Context) -> RBAC Tool Registry -> Service Layer -> Database
"""
import re
from typing import Dict, Any, Optional

from app.ai.tools.registry import registry, ToolResult
from app.ai.planner import parse_query_to_plan
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

def check_result_for_prompt_injection(result_data: Any) -> bool:
    """Check if database contents contain prompt injection commands."""
    if isinstance(result_data, str):
        return detect_prompt_injection(result_data)
    if isinstance(result_data, dict):
        return any(check_result_for_prompt_injection(v) for v in result_data.values())
    if isinstance(result_data, list):
        return any(check_result_for_prompt_injection(i) for i in result_data)
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
    
    # 2. Plan generation (Context & Ambiguity & Tool selection)
    plan = parse_query_to_plan(query_lower, ctx)
    
    if plan.is_ambiguous:
        return {
            "response": plan.ambiguity_reason,
            "result": ToolResult(success=False, error="Ambiguous context", data=None).model_dump(mode="json")
        }
        
    if not plan.steps:
        return {
            "response": "I didn't understand that query or no appropriate tool is available.",
            "result": ToolResult(success=False, error="Unknown query or tool unavailable.", data=None).model_dump(mode="json")
        }

    # 3. Execution of the Plan
    results = {}
    aggregated_data = None
    tools_aggregated = []
    
    # Simple dependency executor
    for step in plan.steps:
        # Dependency logic for multi-tool
        if step.tool_name == "get_training_status" and step.kwargs.get("batch"):
            # This is a specific dependent tool step
            dep_res = results.get(1) # Depends on step 1
            if not dep_res or not dep_res.success:
                results[step.step_id] = ToolResult(success=False, error="Dependency failed", data=None)
                continue
            
            low_att_students = dep_res.data or []
            combined_data = []
            partial_failure = False
            for student_info in low_att_students:
                roll_no = student_info.get("roll_no") or str(student_info.get("student_id"))
                tr_res = registry.execute("get_training_status", user_role=user_role, student_id=roll_no)
                
                if tr_res.success and tr_res.data:
                    tr_status = tr_res.data.get("status", "").upper()
                    if tr_status in ("INCOMPLETE", "PENDING") or not tr_res.data.get("training_completed", False):
                        combined_item = {**student_info, "training_status": tr_status}
                        combined_data.append(combined_item)
                else:
                    partial_failure = True
                    
            aggregated_data = combined_data
            tools_aggregated = ["get_low_attendance_students", "get_training_status"]
            
            meta = {"tools_aggregated": tools_aggregated, "source": "postgresql", "count": len(combined_data)}
            if partial_failure:
                meta["partial_failure"] = True
                
            results[step.step_id] = ToolResult(success=True, data=combined_data, metadata=meta)
            continue
            
        # Normal execution
        # Check if student context is explicitly set in step or from context
        kwargs = dict(step.kwargs)
        if "student_id" in kwargs:
            ctx["last_student_id"] = kwargs["student_id"]
        
        try:
            # Fake timeout handling could be done here
            result = registry.execute(step.tool_name, user_role=user_role, **kwargs)
        except TimeoutError:
            result = ToolResult(success=False, error=f"The {step.tool_name} service did not respond in time.", data=None)

        results[step.step_id] = result
        
        # Check Tool-Output Injection
        if result.success and check_result_for_prompt_injection(result.data):
             result = ToolResult(
                success=False,
                data=None,
                error="Prompt injection detected in database output.",
                metadata={"security_event": "prompt_injection_blocked", "status": "DENIED"}
            )
             results[step.step_id] = result
             return {
                "response": "Security Alert: Malicious content found in database. Response blocked.",
                "result": result.model_dump(mode="json")
             }
        
        if result.success and result.data and isinstance(result.data, dict) and "roll_no" in result.data:
            ctx["last_student_id"] = result.data["roll_no"]

    # 4. Result Formulation
    final_step = plan.steps[-1]
    final_result = results[final_step.step_id]

    if not final_result.success:
        
        if "Permission Denied" in final_result.error:
             return {
                "response": "You do not have permission to perform this action.",
                "result": final_result.model_dump(mode="json")
             }
             
        response_text = f"Unable to retrieve requested information. Reason: {final_result.error}"
        return {
            "response": response_text,
            "result": final_result.model_dump(mode="json")
        }
        
    if plan.intent == "low_attendance_incomplete_training":
        data = final_result.data or []
        response_text = f"Found {len(data)} student(s) with attendance below 75% and incomplete training." if data else "No students found matching both low attendance (<75%) and incomplete training."
        if final_result.metadata.get("partial_failure"):
            response_text += " Attendance information was retrieved successfully. Training information is currently unavailable for some students."
    else:
        # Fallback formatting
        data = final_result.data
        if data is not None:
            if isinstance(data, list):
                response_text = f"Found {len(data)} record(s) matching your request." if len(data) > 0 else "No matching records found."
            else:
                response_text = f"Here is the requested information for {final_step.kwargs.get('student_id', 'the entity')}."
        else:
            response_text = "No matching records found."

    # Hack to keep old tests passing which expected tool in metadata
    if not final_result.metadata.get("tools_aggregated"):
        final_result.metadata["tool"] = final_step.tool_name

    return {
        "response": response_text,
        "result": final_result.model_dump(mode="json")
    }
