from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import re

class PlanStep(BaseModel):
    step_id: int
    tool_name: str
    kwargs: Dict[str, Any] = {}
    depends_on: List[int] = []

class ExecutionPlan(BaseModel):
    steps: List[PlanStep] = []
    intent: str = ""
    is_ambiguous: bool = False
    ambiguity_reason: Optional[str] = None
    requires_clarification: bool = False

def parse_query_to_plan(query_lower: str, context: Dict[str, Any]) -> ExecutionPlan:
    plan = ExecutionPlan()
    
    # 1. Ambiguity Check
    is_context_referential = any(ref in query_lower for ref in ["his", "her", "their", "this student", "the student"])
    student_match = re.search(r"cse\d+", query_lower)
    explicit_student_id = student_match.group(0).upper() if student_match else None
    
    # Check if context has multiple students but query is singular
    if is_context_referential and not explicit_student_id:
        last_students = context.get("last_student_ids", [])
        if len(last_students) > 1:
            plan.is_ambiguous = True
            plan.requires_clarification = True
            plan.ambiguity_reason = f"Which student do you mean, {' or '.join(last_students)}?"
            return plan
        elif len(last_students) == 1:
            explicit_student_id = last_students[0]
        elif "last_student_id" in context:
            explicit_student_id = context["last_student_id"]
    
    # 2. Intent and Tool Planning
    if ("below 75%" in query_lower or "low attendance" in query_lower) and ("training" in query_lower or "incomplete" in query_lower):
        plan.intent = "low_attendance_incomplete_training"
        plan.steps.append(PlanStep(step_id=1, tool_name="get_low_attendance_students", kwargs={"threshold": 75.0}))
        # Training status will be fetched for each student (handled in execution or loop)
        plan.steps.append(PlanStep(step_id=2, tool_name="get_training_status", kwargs={"batch": True}, depends_on=[1]))
        return plan

    if "which students" in query_lower or "who has attendance" in query_lower or "low attendance" in query_lower:
        plan.intent = "low_attendance_students"
        plan.steps.append(PlanStep(step_id=1, tool_name="get_low_attendance_students", kwargs={}))
        return plan
        
    if "unavailable" in query_lower or "what happens if" in query_lower:
        plan.intent = "what_if_simulation"
        fac_match = re.search(r"faculty\s*(\d+)", query_lower)
        fac_id = int(fac_match.group(1)) if fac_match else 12
        plan.steps.append(PlanStep(step_id=1, tool_name="run_what_if", kwargs={"parameters": {"unavailable_faculty": fac_id}}))
        return plan

    if "workload" in query_lower or "faculty" in query_lower or "overload" in query_lower:
        plan.intent = "faculty_workload"
        fac_match = re.search(r"faculty\s*(\d+)", query_lower)
        fac_id = int(fac_match.group(1)) if fac_match else 12
        plan.steps.append(PlanStep(step_id=1, tool_name="get_faculty_workload", kwargs={"faculty_id": fac_id}))
        return plan
        
    if "conflicts" in query_lower or "timetable" in query_lower:
        plan.intent = "timetable_conflicts"
        plan.steps.append(PlanStep(step_id=1, tool_name="get_timetable_conflicts", kwargs={}))
        return plan

    if explicit_student_id:
        if "attendance" in query_lower and "training" in query_lower and "certification" in query_lower:
            plan.intent = "student_360"
            plan.steps.append(PlanStep(step_id=1, tool_name="get_student", kwargs={"student_id": explicit_student_id}))
            plan.steps.append(PlanStep(step_id=2, tool_name="get_student_attendance", kwargs={"student_id": explicit_student_id}))
            plan.steps.append(PlanStep(step_id=3, tool_name="get_training_status", kwargs={"student_id": explicit_student_id}))
            plan.steps.append(PlanStep(step_id=4, tool_name="get_certification_status", kwargs={"student_id": explicit_student_id}))
            return plan

        if "attendance" in query_lower or "attend" in query_lower:
            plan.intent = "student_attendance"
            plan.steps.append(PlanStep(step_id=1, tool_name="get_student_attendance", kwargs={"student_id": explicit_student_id}))
            return plan
            
        if "training" in query_lower or "complete" in query_lower:
            plan.intent = "student_training"
            plan.steps.append(PlanStep(step_id=1, tool_name="get_training_status", kwargs={"student_id": explicit_student_id}))
            return plan

        plan.intent = "student_info"
        plan.steps.append(PlanStep(step_id=1, tool_name="get_student", kwargs={"student_id": explicit_student_id}))
        return plan
        
    return plan
