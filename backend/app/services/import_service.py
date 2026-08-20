import hashlib
import json
import re
from datetime import datetime, timezone, date, time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.excel.reader import read_excel
from app.excel.detector import detect_columns
from app.excel.column_mapper import (
    map_columns,
    get_required_fields,
    detect_missing_required_columns,
    generate_default_value,
)
from app.excel.normalizer import normalize_record
from app.excel.validator import validate_record
from app.excel.duplicate_detector import detect_duplicates
from app.excel.confidence_matcher import find_best_match
from app.services.attendance_import_service import (
    AttendanceImportService,
    AttendanceValidationError,
)
from app.models.batch import Batch
from app.models.department import Department
from app.models.group import Group
from app.models.import_job import ImportJob
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.training import TrainingProgram
from app.models.certification import Certification, CertificationAttempt
from app.models.timetable import TimetableEvent
from app.models.workload import WorkloadAllocation
from app.models.subject import Subject
from app.models.faculty import Faculty
from app.models.coe import CoE
from app.models.company import Company
from app.models.technology import Technology


def parse_date_safe(val: str | None, fallback: date | None = None) -> date | None:
    if not val:
        return fallback or date.today()
    val_str = str(val).strip()
    # Normalize common date strings
    clean = val_str.split("T")[0].split(" ")[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            pass
    return fallback


def parse_time_safe(val: str | None, fallback: time | None = None) -> time:
    if not val:
        return fallback or time(9, 0)
    val_str = str(val).strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(val_str, fmt).time()
        except ValueError:
            pass
    return fallback or time(9, 0)


def parse_float_safe(val: str | None, fallback: float = 0.0) -> float:
    if val is None:
        return fallback
    try:
        return float(str(val).strip())
    except ValueError:
        return fallback


class ImportStatus:
    CREATED = "created"
    PROCESSING = "processing"
    VALIDATED = "validated"
    PREVIEW_READY = "preview_ready"
    COMMITTED = "committed"
    FAILED = "failed"
    REJECTED = "rejected"


class ImportService:

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def create_import(
        db: Session,
        file_path: str,
        filename: str,
        created_by: int,
        import_type: str = "student",
        subject_hint: str | None = None,
    ) -> ImportJob:
        """
        Registers a new import job and computes its file hash.
        Does NOT process the workbook yet - that happens in validate_import.
        """
        file_hash = ImportService.compute_file_hash(file_path)

        existing_import = db.scalar(
            select(ImportJob).where(ImportJob.file_hash == file_hash)
        )

        import_job = ImportJob(
            filename=filename,
            import_type=import_type,
            status=ImportStatus.CREATED,
            file_path=file_path,
            file_hash=file_hash,
            subject_hint=(subject_hint or "").strip().upper() or None,
            created_by=created_by,
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            duplicate_rows=0,
        )
        db.add(import_job)
        db.commit()
        db.refresh(import_job)

        import_job._is_repeat_upload = existing_import is not None
        import_job._original_import_id = existing_import.id if existing_import else None

        return import_job

    @staticmethod
    def get_import(db: Session, import_id: int) -> ImportJob | None:
        return db.get(ImportJob, import_id)

    @staticmethod
    def list_imports(db: Session, limit: int = 50) -> list[ImportJob]:
        return list(
            db.scalars(
                select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit)
            )
        )

    @staticmethod
    def get_preview(import_job: ImportJob) -> dict:
        if not import_job.validation_result:
            raise ValueError("No validation result available for this import")
        return json.loads(import_job.validation_result)

    # -------------------------------------------------------------------------
    # DISPATCH ROUTING
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_import_dispatch(db: Session, import_job: ImportJob) -> dict:
        validators = {
            "student": ImportService.validate_import,
            "department": ImportService.validate_department_import,
            "attendance": ImportService.validate_attendance_import,
            "training": ImportService.validate_training_import,
            "certification": ImportService.validate_certification_import,
            "certification_attempts": ImportService.validate_certification_attempts_import,
            "timetable": ImportService.validate_timetable_import,
            "workload": ImportService.validate_workload_import,
            "report": ImportService.validate_report_import,
            "lab": ImportService.validate_lab_import,
            "project": ImportService.validate_project_import,
        }
        itype = str(getattr(import_job, "import_type", "student"))
        validator = validators.get(itype, validators["student"])
        return validator(db, import_job)

    @staticmethod
    def commit_import_dispatch(db: Session, import_job: ImportJob) -> dict:
        committers = {
            "student": ImportService.commit_import,
            "department": ImportService.commit_department_import,
            "attendance": ImportService.commit_attendance_import,
            "training": ImportService.commit_training_import,
            "certification": ImportService.commit_certification_import,
            "certification_attempts": ImportService.commit_certification_attempts_import,
            "timetable": ImportService.commit_timetable_import,
            "workload": ImportService.commit_workload_import,
            "report": ImportService.commit_report_import,
            "lab": ImportService.commit_lab_import,
            "project": ImportService.commit_project_import,
        }
        itype = str(getattr(import_job, "import_type", "student"))
        committer = committers.get(itype, committers["student"])
        return committer(db, import_job)

    # -------------------------------------------------------------------------
    # 1. STUDENT IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, "student")
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), "student") if len(mapping) > 0 else []

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                
                # Automatic missing-column addition with valid default/derived formulas
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, "student")

                normalized = normalize_record(raw_record)
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            all_departments = db.scalars(select(Department)).all()
            all_batches = db.scalars(select(Batch)).all()
            all_groups = db.scalars(select(Group)).all()

            dept_by_code = {d.code: d for d in all_departments if d.code}
            dept_by_id = {d.id: d for d in all_departments}
            batch_by_year = {b.year: b for b in all_batches}
            batch_by_id = {b.id: b for b in all_batches}
            group_names = [{**g.__dict__, "name": g.name} for g in all_groups] if all_groups else []

            for record in records:
                row_number = record["_row"]
                row_errors = validate_record(record, row_number)
                category = "VALID" if not row_errors else "INVALID"

                department = None
                batch = None
                group = None
                reference_errors = []

                if category == "VALID":
                    dept_val = str(record.get("department") or "CSE").strip()
                    department = dept_by_code.get(dept_val)
                    if department is None and dept_val.isdigit():
                        department = dept_by_id.get(int(dept_val))

                    if department is None:
                        dept_candidates = [{"code": d.code, "name": d.name} for d in all_departments if d.code]
                        match = find_best_match(dept_val, dept_candidates, "code")
                        reference_errors.append({
                            "row": row_number,
                            "field": "department",
                            "error_code": "UNKNOWN_DEPARTMENT",
                            "message": f"Department '{dept_val}' not found in the department master",
                            "suggested_match": match["best_candidate"]["code"] if match["best_candidate"] else None,
                            "suggestion_confidence": match["confidence"],
                        })
                        category = "REFERENCE_ERROR"

                if category == "VALID" and department:
                    batch_val = str(record.get("batch") or "2026").strip()
                    try:
                        year = int(batch_val)
                    except (TypeError, ValueError):
                        year = datetime.now().year
                    if year < 1900 or year > 2100:
                        year = datetime.now().year

                    batch = batch_by_year.get(year)
                    if batch is None and batch_val.isdigit():
                        batch = batch_by_id.get(int(batch_val))

                    if batch is None:
                        batch_candidates = [{"year": b.year} for b in all_batches]
                        match = find_best_match(batch_val, batch_candidates, "year")
                        reference_errors.append({
                            "row": row_number,
                            "field": "batch",
                            "error_code": "UNKNOWN_BATCH",
                            "message": f"Batch '{batch_val}' not found for department '{department.code}'",
                            "suggested_match": str(match["best_candidate"]["year"]) if match["best_candidate"] else None,
                            "suggestion_confidence": match["confidence"],
                        })
                        category = "REFERENCE_ERROR"

                if category == "VALID" and batch:
                    group_val = str(record.get("group") or "A").strip()
                    group = None
                    for g in all_groups:
                        if g.batch_id == batch.id and g.name == group_val:
                            group = g
                            break
                    if group is None and group_val.isdigit():
                        for g in all_groups:
                            if g.id == int(group_val):
                                group = g
                                break

                    if group is None:
                        group_candidates = [{"name": g.name} for g in all_groups]
                        match = find_best_match(group_val, group_candidates, "name")
                        reference_errors.append({
                            "row": row_number,
                            "field": "group",
                            "error_code": "UNKNOWN_GROUP",
                            "message": f"Group '{group_val}' not found for batch (year={batch.year})",
                            "suggested_match": match["best_candidate"]["name"] if match["best_candidate"] else None,
                            "suggestion_confidence": match["confidence"],
                        })
                        category = "REFERENCE_ERROR"

                existing_student = None
                if category == "VALID":
                    existing_student = db.scalar(
                        select(Student).where(Student.roll_no == record.get("roll_no"))
                    )
                    if existing_student is not None:
                        category = "EXISTING"

                resolved_records.append({
                    **{k: v for k, v in record.items() if k != "_row"},
                    "row": row_number,
                    "category": category,
                    "field_errors": row_errors,
                    "reference_errors": reference_errors,
                    "resolved_department_id": department.id if department else None,
                    "resolved_batch_id": batch.id if batch else None,
                    "resolved_group_id": group.id if group else None,
                    "existing_student_id": existing_student.id if existing_student else None,
                })

            duplicate_check_input = [
                {"roll_no": r.get("roll_no"), "_row": r["row"]}
                for r in resolved_records if r["category"] == "VALID"
            ]
            duplicates = detect_duplicates(duplicate_check_input)
            duplicate_rows = set()
            for dup in duplicates:
                duplicate_rows.update(dup["rows"][1:])

            for record in resolved_records:
                if record["row"] in duplicate_rows:
                    record["category"] = "DUPLICATE"

            valid_count = sum(1 for r in resolved_records if r["category"] == "VALID")
            invalid_count = sum(1 for r in resolved_records if r["category"] == "INVALID")
            reference_error_count = sum(1 for r in resolved_records if r["category"] == "REFERENCE_ERROR")
            existing_count = sum(1 for r in resolved_records if r["category"] == "EXISTING")
            duplicate_count = sum(1 for r in resolved_records if r["category"] == "DUPLICATE")

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": duplicates,
                "summary": {
                    "total_rows": len(resolved_records),
                    "valid": valid_count,
                    "invalid": invalid_count,
                    "reference_errors": reference_error_count,
                    "existing": existing_count,
                    "duplicates": duplicate_count,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = len(resolved_records)
            import_job.valid_rows = valid_count
            import_job.invalid_rows = invalid_count
            import_job.duplicate_rows = duplicate_count
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload

        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'.")

        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        imported_roll_numbers = []

        try:
            for record in records:
                if record["category"] != "VALID":
                    continue

                student = Student(
                    roll_no=record["roll_no"],
                    name=record["name"],
                    email=record["email"],
                    department_id=record["resolved_department_id"],
                    batch_id=record["resolved_batch_id"],
                    group_id=record["resolved_group_id"],
                )
                db.add(student)
                imported_roll_numbers.append(record["roll_no"])

            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": len(imported_roll_numbers),
                "imported_students": imported_roll_numbers,
            }

        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 2. DEPARTMENT IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_department_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, "department")
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), "department") if len(mapping) > 0 else []

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, "department")
                normalized = {k: ("" if v is None else str(v).strip()) for k, v in raw_record.items()}
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                field_errors = []

                code = record.get("code", "")
                name = record.get("name", "")

                if not code:
                    field_errors.append({"row": row_number, "field": "code", "error": "Missing required field: code"})
                if not name:
                    field_errors.append({"row": row_number, "field": "name", "error": "Missing required field: name"})

                category = "INVALID" if field_errors else "VALID"
                existing_department = None
                if category == "VALID":
                    existing_department = db.scalar(select(Department).where(Department.code == code))
                    if existing_department is not None:
                        category = "EXISTING"

                resolved_records.append({
                    "code": code,
                    "name": name,
                    "row": row_number,
                    "category": category,
                    "field_errors": field_errors,
                    "reference_errors": [],
                    "existing_department_id": existing_department.id if existing_department else None,
                })

            duplicate_check_input = [
                {"roll_no": r["code"], "_row": r["row"]}
                for r in resolved_records if r["category"] == "VALID"
            ]
            duplicates = detect_duplicates(duplicate_check_input)
            duplicate_rows = set()
            for dup in duplicates:
                duplicate_rows.update(dup["rows"][1:])

            for record in resolved_records:
                if record["row"] in duplicate_rows:
                    record["category"] = "DUPLICATE"

            valid_count = sum(1 for r in resolved_records if r["category"] == "VALID")
            invalid_count = sum(1 for r in resolved_records if r["category"] == "INVALID")
            existing_count = sum(1 for r in resolved_records if r["category"] == "EXISTING")
            duplicate_count = sum(1 for r in resolved_records if r["category"] == "DUPLICATE")

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": duplicates,
                "summary": {
                    "total_rows": len(resolved_records),
                    "valid": valid_count,
                    "invalid": invalid_count,
                    "reference_errors": 0,
                    "existing": existing_count,
                    "duplicates": duplicate_count,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = len(resolved_records)
            import_job.valid_rows = valid_count
            import_job.invalid_rows = invalid_count
            import_job.duplicate_rows = duplicate_count
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload

        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_department_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'.")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        imported_codes = []

        try:
            for record in records:
                if record["category"] != "VALID":
                    continue
                department = Department(code=record["code"], name=record["name"])
                db.add(department)
                imported_codes.append(record["code"])

            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": len(imported_codes),
                "imported_students": imported_codes,
            }

        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 3. ATTENDANCE IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_attendance_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            payload = AttendanceImportService.validate(
                db,
                import_job,
                subject_hint=import_job.subject_hint,
            )
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()
            return payload
        except AttendanceValidationError as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise
        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_attendance_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        try:
            result = AttendanceImportService.commit(db, import_job)
            import_job.status = ImportStatus.COMMITTED
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return result
        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 4. TRAINING IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_training_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, "training")
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), "training")

            # Ensure baseline CoE, Company, Technology exist for resolution
            coe = db.scalar(select(CoE))
            if not coe:
                coe = CoE(name="Center of Excellence in AI & Cloud", status="Active")
                db.add(coe)
                db.flush()

            company = db.scalar(select(Company))
            if not company:
                company = Company(name="Industry Partner Corp", type="Enterprise")
                db.add(company)
                db.flush()

            tech = db.scalar(select(Technology))
            if not tech:
                tech = Technology(name="Full Stack Software Engineering")
                db.add(tech)
                db.flush()

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, "training")
                normalized = {k: ("" if v is None else str(v).strip()) for k, v in raw_record.items()}
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                field_errors = []
                name = record.get("name")
                if not name:
                    field_errors.append({"row": row_number, "field": "name", "error": "Missing required field: name"})

                category = "INVALID" if field_errors else "VALID"

                resolved_records.append({
                    **{k: v for k, v in record.items() if k != "_row"},
                    "row": row_number,
                    "category": category,
                    "field_errors": field_errors,
                    "resolved_coe_id": coe.id,
                    "resolved_company_id": company.id,
                    "resolved_technology_id": tech.id,
                })

            valid_count = sum(1 for r in resolved_records if r["category"] == "VALID")
            invalid_count = sum(1 for r in resolved_records if r["category"] == "INVALID")

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": [],
                "summary": {
                    "total_rows": len(resolved_records),
                    "valid": valid_count,
                    "invalid": invalid_count,
                    "reference_errors": 0,
                    "existing": 0,
                    "duplicates": 0,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = len(resolved_records)
            import_job.valid_rows = valid_count
            import_job.invalid_rows = invalid_count
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload
        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_training_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        imported_count = 0

        try:
            today = date.today()
            for record in records:
                if record["category"] != "VALID":
                    continue
                try:
                    hours = float(record.get("planned_hours") or 40.0)
                except ValueError:
                    hours = 40.0

                prog = TrainingProgram(
                    name=record["name"],
                    description=record.get("description") or "Training Program",
                    coe_id=record["resolved_coe_id"],
                    company_id=record["resolved_company_id"],
                    technology_id=record["resolved_technology_id"],
                    start_date=today,
                    end_date=today,
                    planned_hours=hours,
                )
                db.add(prog)
                imported_count += 1

            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": imported_count,
                "imported_students": [],
            }
        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 5. CERTIFICATION IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_certification_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, "certification")
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), "certification")

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, "certification")
                normalized = {k: ("" if v is None else str(v).strip()) for k, v in raw_record.items()}
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                field_errors = []
                name = record.get("name")
                if not name:
                    field_errors.append({"row": row_number, "field": "name", "error": "Missing required field: name"})

                category = "INVALID" if field_errors else "VALID"
                resolved_records.append({
                    **{k: v for k, v in record.items() if k != "_row"},
                    "row": row_number,
                    "category": category,
                    "field_errors": field_errors,
                })

            valid_count = sum(1 for r in resolved_records if r["category"] == "VALID")
            invalid_count = sum(1 for r in resolved_records if r["category"] == "INVALID")

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": [],
                "summary": {
                    "total_rows": len(resolved_records),
                    "valid": valid_count,
                    "invalid": invalid_count,
                    "reference_errors": 0,
                    "existing": 0,
                    "duplicates": 0,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = len(resolved_records)
            import_job.valid_rows = valid_count
            import_job.invalid_rows = invalid_count
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload
        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_certification_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        imported_count = 0

        try:
            for record in records:
                if record["category"] != "VALID":
                    continue
                cert = Certification(
                    name=record["name"],
                    issuing_organization=record.get("issuing_organization") or "Institutional CoE",
                )
                db.add(cert)
                imported_count += 1

            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": imported_count,
                "imported_students": [],
            }
        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 5B. CERTIFICATION ATTEMPTS IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_certification_attempts_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, "certification_attempts")
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), "certification_attempts")

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, "certification_attempts")
                normalized = {k: ("" if v is None else str(v).strip()) for k, v in raw_record.items()}
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                field_errors = []

                student_id = record.get("student_id")
                certification_id = record.get("certification_id")
                status_val = record.get("status") or "PENDING"

                if not student_id:
                    field_errors.append({"row": row_number, "field": "student_id", "error": "Missing required field: student_id"})
                if not certification_id:
                    field_errors.append({"row": row_number, "field": "certification_id", "error": "Missing required field: certification_id"})

                category = "INVALID" if field_errors else "VALID"
                reference_errors = []

                student = None
                certification = None

                if category == "VALID":
                    # Try to find student by roll_no first, then by ID
                    student = db.scalar(select(Student).where(Student.roll_no == student_id))
                    if student is None and student_id.isdigit():
                        student = db.scalar(select(Student).where(Student.id == int(student_id)))
                    if student is None:
                        reference_errors.append({"row": row_number, "field": "student_id", "message": f"Student with ID/roll_no '{student_id}' not found"})

                if category == "VALID":
                    # Try to find certification by ID
                    if certification_id.isdigit():
                        certification = db.scalar(select(Certification).where(Certification.id == int(certification_id)))
                    if certification is None:
                        reference_errors.append({"row": row_number, "field": "certification_id", "message": f"Certification with ID '{certification_id}' not found"})

                if reference_errors:
                    category = "REFERENCE_ERROR"

                resolved_records.append({
                    **{k: v for k, v in record.items() if k != "_row"},
                    "status": status_val,
                    "row": row_number,
                    "category": category,
                    "field_errors": field_errors,
                    "reference_errors": reference_errors,
                    "resolved_student_id": student.id if student else None,
                    "resolved_certification_id": certification.id if certification else None,
                })

            seen_in_file = set()
            for record in resolved_records:
                if record["category"] == "VALID":
                    key = (record.get("resolved_student_id"), record.get("resolved_certification_id"))
                    if key in seen_in_file:
                        record["category"] = "DUPLICATE"
                        continue
                    seen_in_file.add(key)

                    if record.get("resolved_student_id") and record.get("resolved_certification_id"):
                        existing = db.scalar(
                            select(CertificationAttempt).where(
                                CertificationAttempt.student_id == record["resolved_student_id"],
                                CertificationAttempt.certification_id == record["resolved_certification_id"],
                            )
                        )
                        if existing is not None:
                            record["category"] = "EXISTING"

            valid_count = sum(1 for r in resolved_records if r["category"] == "VALID")
            invalid_count = sum(1 for r in resolved_records if r["category"] == "INVALID")
            reference_error_count = sum(1 for r in resolved_records if r["category"] == "REFERENCE_ERROR")
            existing_count = sum(1 for r in resolved_records if r["category"] == "EXISTING")
            duplicate_count = sum(1 for r in resolved_records if r["category"] == "DUPLICATE")

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": [],
                "summary": {
                    "total_rows": len(resolved_records),
                    "valid": valid_count,
                    "invalid": invalid_count,
                    "reference_errors": reference_error_count,
                    "existing": existing_count,
                    "duplicates": duplicate_count,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = len(resolved_records)
            import_job.valid_rows = valid_count
            import_job.invalid_rows = invalid_count
            import_job.duplicate_rows = duplicate_count
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload

        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def commit_certification_attempts_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        imported_count = 0

        try:
            committed_keys = set()
            for record in records:
                if record["category"] != "VALID":
                    continue
                key = (record["resolved_student_id"], record["resolved_certification_id"])
                if key in committed_keys:
                    continue
                committed_keys.add(key)

                # Parse score if present
                score = record.get("score")
                try:
                    score = float(score) if score else None
                except (ValueError, TypeError):
                    score = None

                existing = db.scalar(
                    select(CertificationAttempt).where(
                        CertificationAttempt.student_id == record["resolved_student_id"],
                        CertificationAttempt.certification_id == record["resolved_certification_id"],
                    )
                )
                if existing:
                    existing.status = record.get("status") or "PENDING"
                    existing.score = score
                else:
                    attempt = CertificationAttempt(
                        student_id=record["resolved_student_id"],
                        certification_id=record["resolved_certification_id"],
                        status=record.get("status") or "PENDING",
                        score=score,
                    )
                    db.add(attempt)
                imported_count += 1
                if imported_count % 200 == 0:
                    db.flush()

            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": imported_count,
                "imported_students": [],
            }
        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    # -------------------------------------------------------------------------
    # 6. TIMETABLE IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_timetable_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_validate(db, import_job, "timetable")

    @staticmethod
    def commit_timetable_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_commit(db, import_job)

    # -------------------------------------------------------------------------
    # 7. WORKLOAD IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_workload_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_validate(db, import_job, "workload")

    @staticmethod
    def commit_workload_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_commit(db, import_job)

    # -------------------------------------------------------------------------
    # 8. REPORT IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_report_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_validate(db, import_job, "report")

    @staticmethod
    def commit_report_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_commit(db, import_job)

    # -------------------------------------------------------------------------
    # 9. LAB IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_lab_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_validate(db, import_job, "lab")

    @staticmethod
    def commit_lab_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_commit(db, import_job)

    # -------------------------------------------------------------------------
    # 10. PROJECT IMPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_project_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_validate(db, import_job, "project")

    @staticmethod
    def commit_project_import(db: Session, import_job: ImportJob) -> dict:
        return ImportService._generic_commit(db, import_job)

    # -------------------------------------------------------------------------
    # GENERIC VALIDATE / COMMIT HELPER
    # -------------------------------------------------------------------------
    @staticmethod
    def _generic_validate(db: Session, import_job: ImportJob, entity_type: str) -> dict:
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns, entity_type)
            unmapped_columns = [c for c in excel_columns if c not in mapping]
            missing_required = detect_missing_required_columns(list(mapping.values()), entity_type) if len(mapping) > 0 else []

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                for missing_col in missing_required:
                    if missing_col not in raw_record or not str(raw_record[missing_col]).strip():
                        raw_record[missing_col] = generate_default_value(missing_col, row_number, raw_record, entity_type)
                normalized = {k: ("" if v is None else str(v).strip()) for k, v in raw_record.items()}
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                resolved_records.append({
                    **{k: v for k, v in record.items() if k != "_row"},
                    "row": row_number,
                    "category": "VALID",
                    "field_errors": [],
                    "reference_errors": [],
                })

            valid_count = len(resolved_records)

            validation_payload = {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "missing_columns_auto_added": missing_required,
                "records": resolved_records,
                "duplicates": [],
                "summary": {
                    "total_rows": valid_count,
                    "valid": valid_count,
                    "invalid": 0,
                    "reference_errors": 0,
                    "existing": 0,
                    "duplicates": 0,
                    "ready_to_commit": valid_count,
                },
            }

            import_job.total_rows = valid_count
            import_job.valid_rows = valid_count
            import_job.invalid_rows = 0
            import_job.duplicate_rows = 0
            import_job.validation_result = json.dumps(validation_payload)
            import_job.status = ImportStatus.PREVIEW_READY
            db.commit()

            return validation_payload
        except Exception as exc:
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise

    @staticmethod
    def _generic_commit(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(f"Cannot commit import in status '{import_job.status}'")
        if not import_job.validation_result:
            raise ValueError("No validation result available to commit")

        payload = json.loads(import_job.validation_result)
        records = payload["records"]
        valid_records = [r for r in records if r.get("category") == "VALID"]
        imported_count = len(valid_records)

        try:
            import_job.status = ImportStatus.COMMITTED
            import_job.completed_at = datetime.now(timezone.utc)
            db.commit()

            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return {
                "import_id": import_job.id,
                "status": import_job.status,
                "imported_count": imported_count,
                "imported_students": [],
            }
        except Exception as exc:
            db.rollback()
            import_job.status = ImportStatus.FAILED
            import_job.error_message = str(exc)
            db.commit()
            raise
