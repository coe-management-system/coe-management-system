from app.ai.tools.registry import registry, Tool, ToolResult
from app.services.training_service import TrainingService
from app.core.database import SessionLocal


def execute_get_training_status(student_id: str, **kwargs) -> ToolResult:
    """Retrieves training and internship status of a specific student."""
    try:
        with SessionLocal() as db:
            service = TrainingService(db)
            data = service.get_student_training_status(student_identifier=student_id)
            return ToolResult(
                success=True,
                data=data,
                metadata={"service": "training_service", "source": "postgresql"}
            )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Training service error: {str(e)}",
            data=None,
            metadata={"service": "training_service", "source": "postgresql"}
        )


def execute_get_all_training_statuses(**kwargs) -> ToolResult:
    """Retrieves training statuses for all students."""
    try:
        with SessionLocal() as db:
            service = TrainingService(db)
            data = service.get_all_training_statuses()
            return ToolResult(
                success=True,
                data=data,
                metadata={"service": "training_service", "source": "postgresql"}
            )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Training service error: {str(e)}",
            data=None,
            metadata={"service": "training_service", "source": "postgresql"}
        )


registry.register_tool(Tool(
    name="get_training_status",
    description="Retrieve the training and internship status of a specific student by roll number or ID.",
    parameters={"student_id": "The roll number of the student (e.g., CSE101)"},
    required_parameters=["student_id"],
    permission="READ",
    executor=execute_get_training_status
))

registry.register_tool(Tool(
    name="get_all_training_statuses",
    description="Retrieve training progress and statuses for all students.",
    parameters={},
    required_parameters=[],
    permission="READ",
    executor=execute_get_all_training_statuses
))
