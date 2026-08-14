import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.excel.reader import read_excel
from app.excel.detector import detect_columns
from app.excel.column_mapper import map_columns
from app.excel.normalizer import normalize_record
from app.excel.validator import validate_record
from app.excel.duplicate_detector import detect_duplicates
from app.excel.import_definitions import FieldMapping
from app.excel.mapping_engine import map_columns_for_definition
from app.models.batch import Batch
from app.models.department import Department
from app.models.group import Group
from app.models.import_job import ImportJob
from app.models.student import Student


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
    def create_import(db: Session, file_path: str, filename: str, created_by: int, import_type: str = "student") -> ImportJob:
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
    def validate_import_dispatch(db: Session, import_job: ImportJob) -> dict:
        if import_job.import_type == "department":
            return ImportService.validate_department_import(db, import_job)
        return ImportService.validate_import(db, import_job)

    @staticmethod
    def commit_import_dispatch(db: Session, import_job: ImportJob) -> dict:
        if import_job.import_type == "department":
            return ImportService.commit_department_import(db, import_job)
        return ImportService.commit_import(db, import_job)

    @staticmethod
    def validate_import(db: Session, import_job: ImportJob) -> dict:
        """
        Runs the full Excel pipeline: read -> detect -> map -> normalize
        -> validate -> resolve entities -> detect duplicates/existing.

        Writes ZERO student records. Stores the result on the ImportJob
        as JSON (validation_result) so commit_import can use it later
        without re-reading the file.
        """
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(
                f"Cannot validate import in status '{import_job.status}'"
            )

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns)
            unmapped_columns = [c for c in excel_columns if c not in mapping]

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                normalized = normalize_record(raw_record)
                normalized["_row"] = row_number
                records.append(normalized)

            resolved_records = []
            for record in records:
                row_number = record["_row"]
                row_errors = validate_record(record, row_number)

                category = "VALID"
                reference_errors = []

                if row_errors:
                    category = "INVALID"

                department = None
                batch = None
                group = None

                if category == "VALID":
                    department = db.scalar(
                        select(Department).where(Department.code == record.get("department"))
                    )
                    if department is None:
                        category = "REFERENCE_ERROR"
                        reference_errors.append({
                            "field": "department",
                            "value": record.get("department"),
                            "error_code": "UNKNOWN_DEPARTMENT",
                            "message": f"Department '{record.get('department')}' not found",
                        })

                if category == "VALID":
                    try:
                        year = int(record.get("batch"))
                    except (TypeError, ValueError):
                        year = None
                    batch = db.scalar(
                        select(Batch).where(
                            Batch.department_id == department.id,
                            Batch.year == year,
                        )
                    ) if year is not None else None
                    if batch is None:
                        category = "REFERENCE_ERROR"
                        reference_errors.append({
                            "field": "batch",
                            "value": record.get("batch"),
                            "error_code": "UNKNOWN_BATCH",
                            "message": f"Batch '{record.get('batch')}' not found for this department",
                        })

                if category == "VALID":
                    group = db.scalar(
                        select(Group).where(
                            Group.batch_id == batch.id,
                            Group.name == record.get("group"),
                        )
                    )
                    if group is None:
                        category = "REFERENCE_ERROR"
                        reference_errors.append({
                            "field": "group",
                            "value": record.get("group"),
                            "error_code": "UNKNOWN_GROUP",
                            "message": f"Group '{record.get('group')}' not found for this batch",
                        })

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
            import_job.invalid_rows = invalid_count + reference_error_count
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
    def validate_department_import(db: Session, import_job: ImportJob) -> dict:
        """
        Department-specific validation. Mirrors validate_import's structure
        but uses Department's own required fields (code, name) and identity
        field (code) for duplicate/existing detection. Writes ZERO records.
        """
        if import_job.status not in (ImportStatus.CREATED, ImportStatus.FAILED):
            raise ValueError(f"Cannot validate import in status '{import_job.status}'")

        import_job.status = ImportStatus.PROCESSING
        db.commit()

        try:
            df = read_excel(import_job.file_path)
            excel_columns = detect_columns(df)


            dept_field_mappings = [
                FieldMapping("code", ["code", "dept code", "department code", "dept_code"]),
                FieldMapping("name", ["name", "department name", "department_name", "dept name"]),
            ]

            mapping_result = map_columns_for_definition(excel_columns, dept_field_mappings)
            mapping = mapping_result["mapping"]
            unmapped_columns = mapping_result["unmapped_columns"]
            ambiguous_columns = mapping_result["ambiguous_columns"]
            column_status = mapping_result["column_status"]

            records = []
            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
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

    @staticmethod
    def commit_import(db: Session, import_job: ImportJob) -> dict:
        """
        Loads the stored validation result and inserts only VALID records
        as new students, inside a single transaction. Rolls back entirely
        on any failure. Never re-reads the Excel file.
        """
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(
                f"Cannot commit import in status '{import_job.status}'. "
                f"Import must be in 'preview_ready' status."
            )

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
                    Path(import_job.file_path).unlink()
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
            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink()
                except Exception:
                    pass
            raise

    @staticmethod
    def commit_department_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(
                f"Cannot commit import in status '{import_job.status}'. Import must be in 'preview_ready' status."
            )
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
                    Path(import_job.file_path).unlink()
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
            if import_job.file_path and Path(import_job.file_path).exists():
                try:
                    Path(import_job.file_path).unlink()
                except Exception:
                    pass
            raise

    @staticmethod
    def commit_department_import(db: Session, import_job: ImportJob) -> dict:
        if import_job.status != ImportStatus.PREVIEW_READY:
            raise ValueError(
                f"Cannot commit import in status '{import_job.status}'. Import must be in 'preview_ready' status."
            )
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
                    Path(import_job.file_path).unlink()
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
