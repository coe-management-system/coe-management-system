from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.department import Department
from app.models.group import Group
from app.models.student import Student
from app.models.subject import Subject

from app.models.attendance import Attendance

from .resolution_plan import WorkbookResolutionPlan


class WorkbookCommitError(Exception):
    """Raised when a workbook commit fails."""


def commit_workbook(db: Session, plan: WorkbookResolutionPlan) -> dict:
    """Persist a resolved workbook plan in one transaction."""
    if plan.errors:
        raise WorkbookCommitError("Cannot commit workbook with validation errors")

    created_departments = []
    created_batches = []
    created_groups = []
    created_students = []
    created_subjects = []
    created_attendance = []

    try:
        department_ids: dict[str, int] = {}
        for item in plan.departments:
            if item.database_id is not None:
                department_ids[item.source_id] = item.database_id
                continue
            department = Department(name=item.name, code=item.code)
            db.add(department)
            db.flush()
            item.database_id = department.id
            department_ids[item.source_id] = department.id
            created_departments.append(department)

        batch_ids: dict[tuple[str, str], int] = {}
        for item in plan.batches:
            department_id = department_ids.get(item.department_source_id)
            if department_id is None:
                raise WorkbookCommitError(f"Department dependency missing for batch '{item.name}'")

            key = (item.department_source_id, item.name)
            if item.database_id is not None:
                batch_ids[key] = item.database_id
                continue

            batch = Batch(name=item.name, year=item.year, department_id=department_id)
            db.add(batch)
            db.flush()
            item.database_id = batch.id
            batch_ids[key] = batch.id
            created_batches.append(batch)

        group_ids: dict[tuple[str, str, str], int] = {}
        for item in plan.groups:
            batch_id = batch_ids.get((item.department_source_id, item.batch_name))
            if batch_id is None:
                raise WorkbookCommitError(f"Batch dependency missing for group '{item.name}'")

            key = (item.department_source_id, item.batch_name, item.name)
            if item.database_id is not None:
                group_ids[key] = item.database_id
                continue

            group = Group(name=item.name, batch_id=batch_id)
            db.add(group)
            db.flush()
            item.database_id = group.id
            group_ids[key] = group.id
            created_groups.append(group)

        subject_ids: dict[tuple[str, str], int] = {}
        for item in plan.subjects:
            department_id = department_ids.get(item.department_source_id)
            if department_id is None:
                raise WorkbookCommitError(f"Department dependency missing for subject '{item.code}'")

            key = (item.department_source_id, item.code)
            if item.database_id is not None:
                subject_ids[key] = item.database_id
                continue

            subject = Subject(code=item.code, name=item.name, department_id=department_id)
            db.add(subject)
            db.flush()
            item.database_id = subject.id
            subject_ids[key] = subject.id
            created_subjects.append(subject)

        imported_students: list[str] = []
        for item in plan.students:
            if item.database_id is not None:
                continue

            department_id = department_ids.get(item.department_source_id)
            batch_id = batch_ids.get((item.department_source_id, str(item.year)))
            group_id = group_ids.get((item.department_source_id, str(item.year), item.group_name))

            if department_id is None:
                raise WorkbookCommitError(f"Department dependency missing for student '{item.roll_no}'")
            if batch_id is None:
                raise WorkbookCommitError(f"Batch dependency missing for student '{item.roll_no}'")
            if group_id is None:
                raise WorkbookCommitError(f"Group dependency missing for student '{item.roll_no}'")

            student = Student(
                roll_no=item.roll_no,
                name=item.name,
                email=item.email,
                department_id=department_id,
                batch_id=batch_id,
                group_id=group_id,
            )
            db.add(student)
            db.flush()
            item.database_id = student.id
            imported_students.append(item.roll_no)
            created_students.append(student)

        student_id_by_roll_no: dict[str, int] = {
            item.roll_no: item.database_id for item in plan.students
        }
        subject_id_by_code: dict[str, int] = {
            item.code: item.database_id for item in plan.subjects
        }

        for item in plan.attendance:
            if item.database_id is not None:
                continue

            student_id = student_id_by_roll_no.get(item.roll_no)
            subject_id = subject_id_by_code.get(item.subject_code)

            if student_id is None:
                raise WorkbookCommitError(
                    f"Student dependency missing for attendance row (roll_no='{item.roll_no}')"
                )
            if subject_id is None:
                raise WorkbookCommitError(
                    f"Subject dependency missing for attendance row (subject_code='{item.subject_code}')"
                )

            attendance = Attendance(
                student_id=student_id,
                subject_id=subject_id,
                session_date=item.session_date,
                status=item.status,
            )
            db.add(attendance)
            db.flush()
            item.database_id = attendance.id
            created_attendance.append(attendance)

        db.commit()

        return {
            "status": "committed",
            "created_departments": len(created_departments),
            "created_batches": len(created_batches),
            "created_groups": len(created_groups),
            "created_subjects": len(created_subjects),
            "created_students": len(created_students),
            "created_attendance": len(created_attendance),
            "imported_students": imported_students,
        }

    except Exception as exc:
        db.rollback()
        if isinstance(exc, WorkbookCommitError):
            raise
        raise WorkbookCommitError(f"Workbook commit failed: {exc}") from exc
