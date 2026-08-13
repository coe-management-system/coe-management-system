from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.attendance_service import get_low_attendance_students_mock


def execute_get_low_attendance_students(**kwargs) -> ToolResult:
    """Retrieves students with low attendance."""
    try:
        data = get_low_attendance_students_mock()
        return ToolResult(
            success=True, 
            data=data, 
            metadata={"service": "attendance_service_mock", "source": "mock_data"}
        )
    except Exception as e:
        return ToolResult(
            success=False, 
            error="Attendance service unavailable", 
            data=None, 
            metadata={"service": "attendance_service_mock"}
        )


registry.register_tool(Tool(
    name="get_low_attendance_students",
    description="Retrieve a list of students whose attendance is below the required threshold (e.g., 75%).",
    parameters={},
    required_parameters=[],
    permission="READ",
    executor=execute_get_low_attendance_students
))
