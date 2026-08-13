"""
ImportService — orchestrates the full Excel import workflow.
This is the ONLY layer allowed to combine Excel processing with database access.
app/excel/ (reader, normalizer, validator, etc.) remains pure — no DB calls there.
"""

from sqlalchemy.orm import Session

from app.excel.reader import read_excel
from app.excel.detector import detect_columns
from app.excel.column_mapper import map_columns
from app.excel.normalizer import normalize_record
from app.excel.validator import validate_record
from app.excel.duplicate_detector import detect_duplicates
from app.excel.file_hash import compute_file_hash
from app.excel.entity_resolver import (
    resolve_department, resolve_batch, resolve_group, find_existing_student
)

from app.models.import_job import ImportJob, ImportError as ImportErrorModel
from app.models.import_status import ImportStatus


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def create_import(self, file_path: str, file_name: str, created_by: int = None) -> ImportJob:
        """Creates an ImportJob row with computed file hash. Status = CREATED."""
        file_hash = compute_file_hash(file_path)

        import_job = ImportJob(
            file_name=file_name,
            file_hash=file_hash,
            status=ImportStatus.CREATED,
            created_by=created_by,
        )
        self.db.add(import_job)
        self.db.commit()
        self.db.refresh(import_job)
        return import_job

    def inspect_workbook(self, file_path: str) -> dict:
        df = read_excel(file_path)
        columns = detect_columns(df)
        return {"columns": columns, "row_count": len(df)}

    def validate_import(self, import_job: ImportJob, file_path: str) -> dict:
        """
        Runs: read -> map -> normalize -> validate -> duplicate detection
              -> entity resolution -> existing-student check.
        Does NOT write students to the database. Only reads for resolution.
        Persists import_errors and moves status CREATED -> PROCESSING -> VALIDATED (or FAILED).
        """
        import_job.status = ImportStatus.PROCESSING
        self.db.commit()

        try:
            df = read_excel(file_path)
            excel_columns = detect_columns(df)
            mapping = map_columns(excel_columns)

            unmapped_columns = [c for c in excel_columns if c not in mapping]

            resolved_records = []

            for idx, row in df.iterrows():
                row_number = idx + 2
                raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
                normalized = normalize_record(raw_record)
                normalized["_row"] = row_number

                row_errors = validate_record(normalized, row_number)

                status = "ACCEPTED"
                resolution_notes = []

                if row_errors:
                    status = "REJECTED"
                    for err in row_errors:
                        self._log_error(import_job.id, "Students", row_number,
                                         err["field"], "FIELD_INVALID", err["error"])

                if status == "ACCEPTED":
                    dept, dept_err = resolve_department(self.db, normalized.get("department"))
                    if dept_err:
                        status = "REJECTED"
                        self._log_error(import_job.id, "Students", row_number,
                                         "department", "UNKNOWN_DEPARTMENT", dept_err)

                if status == "ACCEPTED":
                    batch, batch_err = resolve_batch(self.db, dept.id, normalized.get("batch"))
                    if batch_err:
                        status = "REJECTED"
                        self._log_error(import_job.id, "Students", row_number,
                                         "batch", "UNKNOWN_BATCH", batch_err)

                if status == "ACCEPTED":
                    group, group_err = resolve_group(self.db, batch.id, normalized.get("group"))
                    if group_err:
                        status = "REJECTED"
                        self._log_error(import_job.id, "Students", row_number,
                                         "group", "UNKNOWN_GROUP", group_err)

                if status == "ACCEPTED":
                    existing = find_existing_student(self.db, normalized.get("roll_no"))
                    if existing:
                        status = "EXISTING"
                        resolution_notes.append(f"Existing student id={existing.id}")

                resolved_records.append({**normalized, "_status": status, "_notes": resolution_notes})

            duplicates = detect_duplicates(resolved_records)
            duplicate_rows = set()
            for dup in duplicates:
                duplicate_rows.update(dup["rows"][1:])

            for record in resolved_records:
                if record["_row"] in duplicate_rows:
                    record["_status"] = "DUPLICATE"
                    self._log_error(import_job.id, "Students", record["_row"],
                                     "roll_no", "DUPLICATE_IN_FILE",
                                     f"Duplicate roll_no within uploaded file")

            import_job.status = ImportStatus.VALIDATED
            self.db.commit()

            return {
                "mapping": mapping,
                "unmapped_columns": unmapped_columns,
                "records": resolved_records,
                "duplicates": duplicates,
            }

        except Exception as e:
            import_job.status = ImportStatus.FAILED
            self.db.commit()
            raise

    def preview(self, import_job: ImportJob, validation_result: dict) -> dict:
        """Summarizes validation_result into accepted/rejected/duplicate/warning/existing counts."""
        records = validation_result["records"]
        counts = {"ACCEPTED": 0, "REJECTED": 0, "DUPLICATE": 0, "EXISTING": 0}
        for r in records:
            counts[r["_status"]] = counts.get(r["_status"], 0) + 1

        import_job.status = ImportStatus.PREVIEW_READY
        self.db.commit()

        return {
            "import_id": import_job.id,
            "file_name": import_job.file_name,
            "total_rows": len(records),
            "accepted": counts["ACCEPTED"],
            "rejected": counts["REJECTED"],
            "duplicates": counts["DUPLICATE"],
            "existing": counts["EXISTING"],
            "unmapped_columns": validation_result["unmapped_columns"],
            "row_details": [
                {"row": r["_row"], "status": r["_status"]} for r in records
            ],
        }

    def _log_error(self, import_id: int, sheet: str, row_number: int,
                    column_name: str, error_code: str, message: str):
        error = ImportErrorModel(
            import_id=import_id,
            sheet=sheet,
            row_number=row_number,
            column_name=column_name,
            error_code=error_code,
            message=message,
        )
        self.db.add(error)
        self.db.commit()