"""
Attendance import service — DB mediation layer for the attendance calculator.

Responsibilities:
- Validate: parse the sheet (both formats), resolve students/subjects against the
  master tables (never auto-create), classify every event, and build a preview
  payload that the frontend can show before commit.
- Commit: idempotently upsert per-event attendance rows, log overlapping-date
  overwrites, recompute student aggregate totals, and flag below-threshold
  students.
- Export: generate a downloadable .xlsx of the updated attendance summary with
  below-threshold rows highlighted.

Never auto-creates students or subjects for references that do not exist in the
master tables — such references are flagged for manual review instead.
"""
from __future__ import annotations

import io
import json
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.excel.attendance_parser import parse_attendance_sheet
from app.excel.reader import read_sheet
from app.models.attendance import Attendance
from app.models.department import Department
from app.models.group import Group
from app.models.batch import Batch
from app.models.import_job import ImportJob
from app.models.student import Student
from app.models.subject import Subject

VALID_STATUSES = {"PRESENT", "ABSENT", "LEAVE", "HOLIDAY"}
BASE_HELD_STATUSES = {"PRESENT", "ABSENT"}


def held_statuses() -> set[str]:
    """Statuses that count towards 'Total Classes Held' (the denominator)."""
    statuses = set(BASE_HELD_STATUSES)
    if settings.ATTENDANCE_LEAVE_COUNTS_AS_HELD:
        statuses.add("LEAVE")
    return statuses


class AttendanceValidationError(Exception):
    """Raised when the file is fundamentally not an attendance sheet."""


def _iso_or_none(v) -> str | None:
    return v.isoformat() if isinstance(v, date) else v


def _student_key(row: dict) -> str:
    return str(row.get("roll_no") or row.get("admission_id") or "").strip()


def _format_date(value) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _resolve_students(db: Session) -> tuple[dict, dict]:
    students = db.scalars(select(Student)).all()
    by_roll = {s.roll_no: s for s in students if s.roll_no}
    by_admission = {
        s.admission_id: s for s in students if s.admission_id
    }
    return by_roll, by_admission


def _resolve_subjects(db: Session) -> tuple[dict, dict, dict]:
    subjects = db.scalars(select(Subject)).all()
    by_code = {s.code.upper(): s for s in subjects if s.code}
    by_name = {s.name.upper(): s for s in subjects if s.name}
    by_id = {s.id: s for s in subjects}
    return by_code, by_name, by_id


class AttendanceImportService:

    # ------------------------------------------------------------------
    # Parsing + resolution (no writes)
    # ------------------------------------------------------------------
    @staticmethod
    def parse_and_resolve(
        db: Session,
        file_path: str,
        filename: str,
        subject_hint: str | None = None,
    ) -> dict:
        df, _sheets = read_sheet(file_path)
        parsed = parse_attendance_sheet(
            df,
            filename=filename,
            subject_hint=subject_hint,
            sentinel_roll_threshold=settings.ATTENDANCE_SENTINEL_ROLL_THRESHOLD,
            sentinel_subject_threshold=settings.ATTENDANCE_SENTINEL_SUBJECT_THRESHOLD,
        )

        if parsed["format"] is None:
            raise AttendanceValidationError(
                parsed["reason"]
            )

        by_roll, by_admission = _resolve_students(db)
        by_code, by_name, by_id = _resolve_subjects(db)

        issues = list(parsed["issues"])
        records: list[dict] = []
        seen_keys: set[tuple] = set()

        for event in parsed["events"]:
            row_number = event["row"]
            ref = _student_key(event)
            field_errors = []
            reference_errors = []
            category = "VALID"

            student = None
            subject_obj = None

            # --- resolve student (no auto-create) -----------------------------
            if event.get("sentinel"):
                reference_errors.append({
                    "row": row_number,
                    "field": "student_id",
                    "message": f"Out-of-range student reference '{ref}' flagged for review",
                })
                category = "REFERENCE_ERROR"
            elif ref:
                student = by_roll.get(ref) or by_admission.get(ref)
                if student is None:
                    reference_errors.append({
                        "row": row_number,
                        "field": "student_id",
                        "message": f"Student '{ref}' not found in the student master — "
                                   f"flagged for manual review, no record created",
                    })
                    category = "REFERENCE_ERROR"

            # --- resolve subject (no auto-create) -----------------------------
            subj_code = str(event.get("subject") or "").strip().upper()
            if event.get("subject") is None:
                issues.append({
                    "row": row_number,
                    "column": None,
                    "type": "subject_required",
                    "message": f"Row {row_number}: no subject code available",
                })
                category = "EXCLUDED"
            elif subject_obj is None:
                if event.get("sentinel_subject"):
                    reference_errors.append({
                        "row": row_number,
                        "field": "subject",
                        "message": f"Out-of-range subject code '{subj_code}' flagged for review",
                    })
                    category = "REFERENCE_ERROR"
                else:
                    subject_obj = by_code.get(subj_code) or by_name.get(subj_code)
                    if subject_obj is None and subj_code.isdigit() and int(subj_code) in by_id:
                        subject_obj = by_id[int(subj_code)]
                    if subject_obj is None:
                        reference_errors.append({
                            "row": row_number,
                            "field": "subject",
                            "message": f"Subject '{subj_code}' not found in the subjects "
                                       f"master — flagged for manual review",
                        })
                        category = "REFERENCE_ERROR"

            event_status = event.get("status")
            if event_status is None:
                category = "EXCLUDED"
                if not (event.get("raw_status") or "").strip():
                    field_errors.append({
                        "row": row_number,
                        "field": "status",
                        "error": f"Blank mark on {event.get('date')} — excluded from classes "
                                 "held (not counted as absent)",
                    })
                else:
                    field_errors.append({
                        "row": row_number,
                        "field": "status",
                        "error": f"Attendance mark on {event.get('date')} could not be mapped "
                                 f"(raw: {event.get('raw_status')})",
                    })
            if event.get("date") is None:
                category = "EXCLUDED"
                field_errors.append({
                    "row": row_number,
                    "field": "date",
                    "error": f"Date on row {row_number} could not be parsed",
                })

            d = _format_date(event.get("date"))
            if (
                d is not None
                and student is not None
                and subject_obj is not None
                and event_status is not None
            ):
                key = (student.id, subject_obj.id, d)
                if key in seen_keys:
                    category = "DUPLICATE"
                else:
                    seen_keys.add(key)
                    existing = db.scalar(
                        select(Attendance).where(
                            Attendance.student_id == student.id,
                            Attendance.subject_id == subject_obj.id,
                            Attendance.session_date == d,
                        )
                    )
                    if existing is not None:
                        category = "EXISTING"

            if category == "VALID":
                for issue in event["issues"]:
                    if issue["type"] == "not_marked":
                        # blank cell -> this event is intentionally excluded
                        category = "EXCLUDED"
                        issues.append({
                            "row": row_number,
                            "column": None,
                            "type": "not_marked",
                            "message": f"Blank mark on {event.get('date')} excluded from "
                                       "classes held",
                        })
                        break

            records.append({
                "row": row_number,
                "roll_no": event.get("roll_no") or "",
                "admission_id": event.get("admission_id") or "",
                "student_name": event.get("student_name") or "",
                "branch": event.get("branch") or "",
                "section": event.get("section") or "",
                "subject": subj_code,
                "date": event.get("date"),
                "status": event_status,
                "raw_status": event.get("raw_status") or "",
                "external_id": event.get("external_id"),
                "category": category,
                "field_errors": field_errors,
                "reference_errors": reference_errors,
                "resolved_student_id": student.id if student else None,
                "resolved_subject_id": subject_obj.id if subject_obj else None,
            })

        return {
            "format": parsed["format"],
            "detected_type": parsed["detected_type"],
            "reason": parsed["reason"],
            "subject": parsed["subject"],
            "subject_source": parsed["subject_source"],
            "issues": issues,
            "duplicates": parsed["duplicates"],
            "records": records,
            "summary": AttendanceImportService._summarize(records),
            "mapping": {},
            "unmapped_columns": [],
            "ambiguous_columns": [],
            "column_status": [],
        }

    @staticmethod
    def validate(db: Session, import_job: ImportJob, subject_hint: str | None = None) -> dict:
        payload = AttendanceImportService.parse_and_resolve(
            db,
            import_job.file_path,
            import_job.filename,
            subject_hint=subject_hint,
        )
        import_job.total_rows = payload["summary"]["total"]
        import_job.valid_rows = payload["summary"]["valid"]
        import_job.invalid_rows = payload["summary"]["invalid"]
        import_job.duplicate_rows = payload["summary"]["duplicates"]
        import_job.validation_result = json.dumps(payload)
        return payload

    @staticmethod
    def _summarize(records: list[dict]) -> dict:
        valid = sum(1 for r in records if r["category"] == "VALID")
        existing = sum(1 for r in records if r["category"] == "EXISTING")
        duplicates = sum(1 for r in records if r["category"] == "DUPLICATE")
        reference_errors = sum(1 for r in records if r["category"] == "REFERENCE_ERROR")
        excluded = sum(1 for r in records if r["category"] == "EXCLUDED")
        return {
            "total": len(records),
            "total_rows": len(records),
            "valid": valid,
            "invalid": reference_errors + excluded,
            "reference_errors": reference_errors,
            "existing": existing,
            "duplicates": duplicates,
            "excluded": excluded,
            "ready_to_commit": valid,
        }

    # ------------------------------------------------------------------
    # Commit (writes)
    # ------------------------------------------------------------------
    @staticmethod
    def commit(db: Session, import_job: ImportJob) -> dict:
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload.get("records", [])

        try:
            inserted = 0
            updated = 0
            overwritten: list[dict] = []
            affected_student_ids: set[int] = set()
            subject_cache: dict[int, str] = {}

            for record in records:
                if record["category"] not in ("VALID", "EXISTING"):
                    continue
                sid = record.get("resolved_student_id")
                subj_id = record.get("resolved_subject_id")
                d = _format_date(record.get("date"))
                status = record.get("status")
                if sid is None or subj_id is None or d is None or status not in VALID_STATUSES:
                    continue

                affected_student_ids.add(sid)
                subject_cache.setdefault(subj_id, record.get("subject") or "")

                existing = db.scalar(
                    select(Attendance).where(
                        Attendance.student_id == sid,
                        Attendance.subject_id == subj_id,
                        Attendance.session_date == d,
                    )
                )
                if existing is not None:
                    if existing.status != status:
                        overwritten.append({
                            "student_id": sid,
                            "roll_no": record.get("roll_no") or record.get("admission_id"),
                            "subject_code": record.get("subject") or "",
                            "date": d.isoformat(),
                            "old_status": existing.status,
                            "new_status": status,
                        })
                        existing.status = status
                        existing.external_id = record.get("external_id") or existing.external_id
                        existing.source_import_id = import_job.id
                        existing.source_file = import_job.filename
                        updated += 1
                else:
                    db.add(Attendance(
                        student_id=sid,
                        subject_id=subj_id,
                        session_date=d,
                        status=status,
                        external_id=record.get("external_id"),
                        source_import_id=import_job.id,
                        source_file=import_job.filename,
                    ))
                    inserted += 1

            db.flush()

            now = datetime.now(timezone.utc)
            for sid in affected_student_ids:
                student = db.get(Student, sid)
                if student is None:
                    continue
                AttendanceImportService.recompute_student(
                    db, student, source_file=import_job.filename, updated_at=now,
                )

            import_job.status = "committed"
            import_job.completed_at = now
            db.commit()

            summary = AttendanceImportService._summarize(records)
            threshold = settings.ATTENDANCE_THRESHOLD_PERCENT
            low_students = AttendanceImportService.low_attendance_students(db, threshold)

            result = {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": inserted + updated,
                "inserted": inserted,
                "updated": updated,
                "overwritten": overwritten,
                "valid_events": summary["valid"],
                "existing_events": summary["existing"],
                "excluded_events": summary["invalid"],
                "below_threshold_count": len(low_students),
                "below_threshold_threshold": threshold,
                "below_threshold": low_students,
                "imported_students": sorted(
                    {str(r.get("roll_no") or r.get("admission_id")) for r in records
                     if r["category"] in ("VALID", "EXISTING")}
                ),
            }
            return result

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def recompute_student(
        db: Session,
        student: Student,
        source_file: str | None,
        updated_at: datetime,
    ) -> None:
        """Recompute a student's aggregate totals from the attendance table.

        Derived from the per-event rows, so totals are always consistent and
        re-importing the same file is idempotent by construction.
        """
        rows = db.scalars(
            select(Attendance).where(Attendance.student_id == student.id)
        ).all()

        HELD = held_statuses()
        held = [r for r in rows if r.status in HELD]
        present = sum(1 for r in held if r.status == "PRESENT")
        absent = sum(1 for r in held if r.status == "ABSENT")
        total = len(held)
        percentage = round((present / total) * 100, 2) if total else 0.0

        student.total_classes_held = total
        student.total_present = present
        student.total_absent = absent
        student.attendance_percentage = percentage
        student.attendance_updated_at = updated_at
        student.attendance_source_file = source_file

    @staticmethod
    def low_attendance_students(db: Session, threshold: float = 75.0) -> list[dict]:
        students = db.scalars(select(Student)).all()
        results = []
        for s in students:
            if s.total_classes_held and s.attendance_percentage < threshold:
                department = db.get(Department, s.department_id)
                batch = db.get(Batch, s.batch_id)
                group = db.get(Group, s.group_id)
                results.append({
                    "student_id": s.id,
                    "roll_no": s.roll_no,
                    "admission_id": s.admission_id,
                    "name": s.name,
                    "department": department.name if department else "",
                    "batch": batch.name if batch else "",
                    "section": group.name if group else "",
                    "total_classes": s.total_classes_held,
                    "present": s.total_present,
                    "absent": s.total_absent,
                    "attendance_percentage": s.attendance_percentage,
                })
        results.sort(key=lambda r: r["attendance_percentage"])
        return results

    # ------------------------------------------------------------------
    # Reports / export
    # ------------------------------------------------------------------
    @staticmethod
    def list_flagged(db: Session, import_job: ImportJob) -> dict:
        payload = json.loads(import_job.validation_result or "{}")
        records = payload.get("records", [])
        flagged = []
        for r in records:
            if r["category"] == "VALID":
                continue
            reasons = [e.get("error", e.get("message")) for e in r.get("field_errors", [])]
            reasons += [e.get("message") for e in r.get("reference_errors", [])]
            flagged.append({
                "row": r["row"],
                "category": r["category"],
                "roll_no": r.get("roll_no"),
                "admission_id": r.get("admission_id"),
                "date": r.get("date"),
                "status": r.get("status"),
                "subject": r.get("subject"),
                "reasons": reasons,
            })
        return {
            "import_id": import_job.id,
            "flagged_rows": flagged,
            "issues": payload.get("issues", []),
        }

    @staticmethod
    def build_export(db: Session, import_job: ImportJob) -> bytes:
        """Build an updated attendance summary workbook (xlsx bytes).

        One row per (student, subject). Rows below the configured threshold are
        highlighted red. Uses aggregate columns on the student master so the
        export reflects the state after this import.
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter

        threshold = settings.ATTENDANCE_THRESHOLD_PERCENT
        subject_names = {
            s.id: s.name for s in db.scalars(select(Subject)).all()
        }
        students = db.scalars(select(Student)).all()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Updated Attendance"

        headers = [
            "Roll No", "Admission ID", "Student Name", "Department", "Section",
            "Subject Code", "Subject Name", "Total Classes Held", "Present",
            "Absent", "Attendance %", "Status",
        ]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        red_font = Font(color="9C0006", bold=True)

        for s in students:
            if not s.total_classes_held and not s.attendance_percentage:
                continue
            department = db.get(Department, s.department_id)
            batch = db.get(Batch, s.batch_id)
            group = db.get(Group, s.group_id)
            subject_ids = db.scalars(
                select(Attendance.subject_id)
                .where(Attendance.student_id == s.id)
                .distinct()
            ).all()
            if not subject_ids:
                subject_ids = [None]
            for subj_id in subject_ids:
                if subj_id is None:
                    code, name = "", "Overall"
                    total = s.total_classes_held
                    present = s.total_present
                    absent = s.total_absent
                    pct = s.attendance_percentage
                else:
                    rows = db.scalars(
                        select(Attendance).where(
                            Attendance.student_id == s.id,
                            Attendance.subject_id == subj_id,
                        )
                    ).all()
                    HELD = held_statuses()
                    held = [r for r in rows if r.status in HELD]
                    present = sum(1 for r in held if r.status == "PRESENT")
                    absent = sum(1 for r in held if r.status == "ABSENT")
                    total = len(held)
                    pct = round((present / total) * 100, 2) if total else 0.0
                    subj = db.get(Subject, subj_id)
                    code = subj.code if subj else ""
                    name = subject_names.get(subj_id, "") if subj else ""

                row = [
                    s.roll_no, s.admission_id or "", s.name,
                    department.name if department else "", group.name if group else "",
                    code, name, total, present, absent, pct,
                    "Below threshold" if pct < threshold else "OK",
                ]
                ws.append(row)
                if pct < threshold:
                    last = ws.max_row
                    for cell in ws[last]:
                        cell.fill = red_fill
                        cell.font = red_font

        for idx, width in enumerate([12, 14, 24, 18, 12, 14, 26, 16, 10, 10, 12, 16], start=1):
            ws.column_dimensions[get_column_letter(idx)].width = width

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()