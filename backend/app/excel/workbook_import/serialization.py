from .resolution_plan import WorkbookResolutionPlan


def serialize_resolution_plan(plan: WorkbookResolutionPlan) -> dict:
    return {
        "departments": [
            {
                "source_id": item.source_id,
                "name": item.name,
                "code": item.code,
                "database_id": item.database_id,
            }
            for item in plan.departments
        ],
        "batches": [
            {
                "source_id": item.source_id,
                "name": item.name,
                "year": item.year,
                "department_source_id": item.department_source_id,
                "database_id": item.database_id,
            }
            for item in plan.batches
        ],
        "groups": [
            {
                "source_id": item.source_id,
                "name": item.name,
                "department_source_id": item.department_source_id,
                "batch_name": item.batch_name,
                "database_id": item.database_id,
            }
            for item in plan.groups
        ],
        "students": [
            {
                "roll_no": item.roll_no,
                "name": item.name,
                "email": item.email,
                "department_source_id": item.department_source_id,
                "year": item.year,
                "group_name": item.group_name,
                "database_id": item.database_id,
            }
            for item in plan.students
        ],
        "subjects": [
            {
                "code": item.code,
                "name": item.name,
                "department_source_id": item.department_source_id,
                "database_id": item.database_id,
            }
            for item in plan.subjects
        ],
        "errors": plan.errors,
    }
