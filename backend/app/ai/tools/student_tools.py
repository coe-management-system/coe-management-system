from typing import Any
from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.student_service import get_all_students, get_student_by_roll_no
from app.core.database import SessionLocal
from app.schemas.student import StudentResponse


def execute_get_students(**kwargs) -> ToolResult:
    """Retrieves all students from the database."""
    try:
        with SessionLocal() as db:
            students = get_all_students(db)
            data = [StudentResponse.model_validate(s).model_dump(mode="json") for s in students]
            return ToolResult(success=True, data=data, metadata={"service": "student_service", "source": "postgresql"})
    except Exception as e:
        return ToolResult(success=False, error="Student service unavailable", data=None, metadata={"service": "student_service", "source": "postgresql"})


def execute_get_student(student_id: str, **kwargs) -> ToolResult:
    """Retrieves information about a specific student by roll number."""
    try:
        with SessionLocal() as db:
            student = get_student_by_roll_no(db, student_id)
            if not student:
                return ToolResult(success=False, error="Student not found", data=None, metadata={"service": "student_service", "source": "postgresql"})
            
            data = StudentResponse.model_validate(student).model_dump(mode="json")
            return ToolResult(success=True, data=data, metadata={"service": "student_service", "source": "postgresql"})
    except ValueError as e:
        return ToolResult(success=False, error=str(e), data=None, metadata={"service": "student_service", "source": "postgresql"})
    except Exception as e:
        return ToolResult(success=False, error="Student service unavailable", data=None, metadata={"service": "student_service", "source": "postgresql"})


registry.register_tool(Tool(
    name="get_students",
    description="Retrieve a list of all students.",
    parameters={},
    required_parameters=[],
    permission="READ",
    executor=execute_get_students
))

registry.register_tool(Tool(
    name="get_student",
    description="Retrieve a student's academic identity information using the student's identifier.",
    parameters={"student_id": "The roll number of the student (e.g., CSE101)"},
    required_parameters=["student_id"],
    permission="READ",
    executor=execute_get_student
))
