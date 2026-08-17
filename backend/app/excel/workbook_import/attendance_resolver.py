from app.excel.workbook_import.planner import WorkbookPlan
from app.excel.workbook_import.resolution_plan import PlannedAttendance, WorkbookResolutionPlan

VALID_ATTENDANCE_STATUSES = {"PRESENT", "ABSENT", "EXCUSED", "CANCELLED"}


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
    seen_keys: set[tuple[str, str, str]] = set()

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

        dedup_key = (roll_no, subject_code, row.session_date.strip())
        if dedup_key in seen_keys:
            plan.errors.append(
                {
                    "entity": "attendance",
                    "roll_no": row.roll_no,
                    "subject_code": row.subject_code,
                    "error": (
                        "Duplicate attendance row in workbook for "
                        f"student '{row.roll_no}', subject "
                        f"'{row.subject_code}', date '{row.session_date}'"
                    ),
                }
            )
            continue

        status = row.status.upper()
        if status not in VALID_ATTENDANCE_STATUSES:
            plan.errors.append(
                {
                    "entity": "attendance",
                    "roll_no": row.roll_no,
                    "subject_code": row.subject_code,
                    "error": (
                        f"Invalid Status '{row.status}' - must be one of "
                        f"{sorted(VALID_ATTENDANCE_STATUSES)}"
                    ),
                }
            )
            continue

        seen_keys.add(dedup_key)

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