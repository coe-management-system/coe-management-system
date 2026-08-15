from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.attendance_service import AttendanceService
from app.core.database import SessionLocal


def execute_get_low_attendance_students(threshold: float = 75.0, **kwargs) -> ToolResult:
    """Retrieves students with low attendance from PostgreSQL via AttendanceService."""
    try:
        with SessionLocal() as db:
            service = AttendanceService(db)
            data = service.get_low_attendance_students(threshold=threshold)
            return ToolResult(
                success=True, 
                data=data, 
                metadata={"service": "attendance_service", "source": "postgresql"}
            )
    except Exception as e:
        return ToolResult(
            success=False, 
            error=f"Attendance service error: {str(e)}", 
            data=None, 
            metadata={"service": "attendance_service", "source": "postgresql"}
        )


def execute_get_student_attendance(student_id: str, **kwargs) -> ToolResult:
    """Retrieves detailed attendance summary for a specific student from PostgreSQL."""
    try:
        with SessionLocal() as db:
            service = AttendanceService(db)
            data = service.get_student_attendance(student_identifier=student_id)
            return ToolResult(
                success=True,
                data=data,
                metadata={"service": "attendance_service", "source": "postgresql"}
            )
    except ValueError as e:
        return ToolResult(
            success=False,
            error=str(e),
            data=None,
            metadata={"service": "attendance_service", "source": "postgresql"}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Attendance service error: {str(e)}",
            data=None,
            metadata={"service": "attendance_service", "source": "postgresql"}
        )


registry.register_tool(Tool(
    name="get_low_attendance_students",
    description="Retrieve a list of students whose attendance is below the required threshold (default: 75%).",
    parameters={"threshold": "The attendance percentage threshold below which students are flagged (default 75.0)"},
    required_parameters=[],
    permission="READ",
    executor=execute_get_low_attendance_students
))

registry.register_tool(Tool(
    name="get_student_attendance",
    description="Retrieve attendance record and percentage for a specific student by roll number or ID.",
    parameters={"student_id": "The roll number (e.g. CSE101) or numerical ID of the student"},
    required_parameters=["student_id"],
    permission="READ",
    executor=execute_get_student_attendance
))
