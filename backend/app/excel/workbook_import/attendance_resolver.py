from app.excel.workbook_import.planner import WorkbookPlan
from app.excel.workbook_import.resolution_plan import PlannedAttendance, WorkbookResolutionPlan


def resolve_attendance(
    workbook_plan: WorkbookPlan,
    plan: WorkbookResolutionPlan,
) -> None:
    """
    Resolve Attendance rows against already-resolved students and
    subjects on the given WorkbookResolutionPlan.

    Student and subject lookup only - never creates either. If a
    row's roll_no or subject_code cannot be matched against
    plan.students / plan.subjects, a hard error is appended to
    plan.errors and the row is skipped.

    Mutates plan.attendance and plan.errors in place.
    """
    student_by_roll_no = {
        item.roll_no.upper(): item for item in plan.students
    }
    subject_by_code = {
        item.code.upper(): item for item in plan.subjects
    }

    for row in workbook_plan.attendance:
        roll_no = row.roll_no.upper()
        subject_code = row.subject_code.upper()

        student = student_by_roll_no.get(roll_no)
        subject = subject_by_code.get(subject_code)

        if student is None:
            plan.errors.append(
                {
                    "entity": "attendance",
                    "roll_no": row.roll_no,
                    "subject_code": row.subject_code,
                    "error": (
                        f"Unknown student (Admission ID): {row.roll_no}"
                    ),
                }
            )
            continue

        if subject is None:
            plan.errors.append(
                {
                    "entity": "attendance",
                    "roll_no": row.roll_no,
                    "subject_code": row.subject_code,
                    "error": (
                        f"Unknown subject (Subject Code): {row.subject_code}"
                    ),
                }
            )
            continue

        plan.attendance.append(
            PlannedAttendance(
                roll_no=row.roll_no,
                subject_code=row.subject_code,
                session_date=row.session_date,
                status=row.status,
                student_id=student.database_id,
                subject_id=subject.database_id,
                database_id=None,
            )
        )