from .resolution_plan import (
    PlannedBatch,
    PlannedDepartment,
    PlannedGroup,
    PlannedStudent,
    PlannedSubject,
    WorkbookResolutionPlan,
)


def deserialize_resolution_plan(data: dict) -> WorkbookResolutionPlan:
    return WorkbookResolutionPlan(
        departments=[PlannedDepartment(**item) for item in data.get("departments", [])],
        batches=[PlannedBatch(**item) for item in data.get("batches", [])],
        groups=[PlannedGroup(**item) for item in data.get("groups", [])],
        students=[PlannedStudent(**item) for item in data.get("students", [])],
        subjects=[PlannedSubject(**item) for item in data.get("subjects", [])],
        errors=data.get("errors", []),
    )
