from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.workload_service import get_faculty_workload_mock


def execute_get_faculty_workload(faculty_id: int, **kwargs) -> ToolResult:
    """Retrieves the workload of a specific faculty member."""
    try:
        # Cast faculty_id to int if it comes as a string from the LLM
        if isinstance(faculty_id, str) and faculty_id.isdigit():
            faculty_id = int(faculty_id)
            
        data = get_faculty_workload_mock(faculty_id)
        return ToolResult(
            success=True, 
            data=data, 
            metadata={"service": "workload_service_mock", "source": "mock_data"}
        )
    except ValueError as e:
        return ToolResult(
            success=False, 
            error=str(e), 
            data=None, 
            metadata={"service": "workload_service_mock"}
        )
    except Exception as e:
        return ToolResult(
            success=False, 
            error="Workload service unavailable", 
            data=None, 
            metadata={"service": "workload_service_mock"}
        )


registry.register_tool(Tool(
    name="get_faculty_workload",
    description="Retrieve the current workload and assigned hours for a specific faculty member.",
    parameters={"faculty_id": "The numerical ID of the faculty member (e.g., 12)"},
    required_parameters=["faculty_id"],
    permission="FACULTY",
    executor=execute_get_faculty_workload
))
