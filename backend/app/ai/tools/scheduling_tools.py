from typing import Any, Dict
from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.timetable_service import get_timetable_conflicts_mock, run_what_if_mock


def execute_get_timetable_conflicts(**kwargs) -> ToolResult:
    """Retrieves current timetable conflicts."""
    try:
        data = get_timetable_conflicts_mock()
        return ToolResult(
            success=True, 
            data=data, 
            metadata={"service": "timetable_service_mock", "source": "mock_data"}
        )
    except Exception as e:
        return ToolResult(
            success=False, 
            error="Scheduling service unavailable", 
            data=None, 
            metadata={"service": "timetable_service_mock"}
        )

def execute_run_what_if(parameters: Dict[str, Any], **kwargs) -> ToolResult:
    """Runs a what-if scheduling scenario simulation."""
    try:
        data = run_what_if_mock(parameters)
        return ToolResult(
            success=True, 
            data=data, 
            metadata={"service": "timetable_service_mock", "source": "simulation"}
        )
    except Exception as e:
        return ToolResult(
            success=False, 
            error="Scheduling service unavailable for simulation", 
            data=None, 
            metadata={"service": "timetable_service_mock"}
        )


registry.register_tool(Tool(
    name="get_timetable_conflicts",
    description="Check for any scheduling or room booking conflicts in the current timetable.",
    parameters={},
    required_parameters=[],
    permission="READ",
    executor=execute_get_timetable_conflicts
))

registry.register_tool(Tool(
    name="run_what_if",
    description="Simulate a timetable change to see its impact and potential conflicts without saving the changes.",
    parameters={"parameters": "A dictionary of the scenario changes (e.g., moving a class to a different room or time)"},
    required_parameters=["parameters"],
    permission="SIMULATION",
    executor=execute_run_what_if
))
