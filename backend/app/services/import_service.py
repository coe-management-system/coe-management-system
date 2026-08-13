import json
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.excel.importer import run_import
from app.models.batch import Batch
from app.models.department import Department
from app.models.group import Group
from app.models.import_job import ImportJob
from app.models.student import Student


class ImportService:
    @staticmethod
    def process_student_file(
        db: Session,
        file_path: str,
        filename: str,
        created_by: int,
    ) -> dict:
        """
        Process a student Excel file and import valid records.

        The existing Excel pipeline is responsible for:
        - reading
        - column detection
        - column mapping
        - normalization
        - validation
        - duplicate detection

        This service is responsible for:
        - resolving database entities
        - checking existing students
        - creating Student records
        - recording the import job
        """

        import_job = ImportJob(
            filename=filename,
            status="processing",
            created_by=created_by,
        )

        db.add(import_job)
        db.flush()

        try:
            result = run_import(file_path)

            valid_records = result["valid_records"]
            invalid_records = result["invalid_records"]
            errors = result["errors"]
            duplicates = result["duplicates"]

            import_job.total_rows = (
                len(valid_records) + len(invalid_records)
            )
            import_job.valid_rows = len(valid_records)
            import_job.invalid_rows = len(invalid_records)
            import_job.duplicate_rows = len(duplicates)

            duplicate_roll_numbers = {
                duplicate["roll_no"]
                for duplicate in duplicates
            }

            imported_students = []
            skipped_existing = []
            reference_errors = []

            for record in valid_records:
                roll_no = record["roll_no"]

                if roll_no in duplicate_roll_numbers:
                    continue

                department = db.scalar(
                    select(Department).where(
                        Department.code == record["department"]
                    )
                )

                if department is None:
                    reference_errors.append(
                        {
                            "roll_no": roll_no,
                            "field": "department",
                            "value": record["department"],
                            "error": "Department not found",
                        }
                    )
                    continue

                batch = db.scalar(
                    select(Batch).where(
                        Batch.year == int(record["batch"]),
                        Batch.department_id == department.id,
                    )
                )

                if batch is None:
                    reference_errors.append(
                        {
                            "roll_no": roll_no,
                            "field": "batch",
                            "value": record["batch"],
                            "error": "Batch not found",
                        }
                    )
                    continue

                section = record["group"]

                group = db.scalar(
                    select(Group).where(
                        Group.batch_id == batch.id,
                        Group.name == section,
                    )
                )

                if group is None:
                    group = db.scalar(
                        select(Group).where(
                            Group.batch_id == batch.id,
                            Group.name == (
                                f"{department.code}-{section}"
                            ),
                        )
                    )

                if group is None:
                    reference_errors.append(
                        {
                            "roll_no": roll_no,
                            "field": "group",
                            "value": section,
                            "error": "Group not found",
                        }
                    )
                    continue

                existing_student = db.scalar(
                    select(Student).where(
                        Student.roll_no == roll_no
                    )
                )

                if existing_student is not None:
                    skipped_existing.append(roll_no)
                    continue

                student = Student(
                    roll_no=roll_no,
                    name=record["name"],
                    email=record["email"],
                    department_id=department.id,
                    batch_id=batch.id,
                    group_id=group.id,
                )

                db.add(student)
                imported_students.append(roll_no)

            import_job.status = "completed"

            error_summary = {
                "validation_errors": errors,
                "reference_errors": reference_errors,
                "existing_students": skipped_existing,
            }

            if errors or reference_errors:
                import_job.error_message = json.dumps(
                    error_summary
                )

            db.commit()

            return {
                "import_job_id": import_job.id,
                "filename": filename,
                "status": import_job.status,
                "total_rows": import_job.total_rows,
                "valid_rows": import_job.valid_rows,
                "invalid_rows": import_job.invalid_rows,
                "duplicate_rows": import_job.duplicate_rows,
                "imported_students": imported_students,
                "skipped_existing": skipped_existing,
                "reference_errors": reference_errors,
                "validation_errors": errors,
            }

        except Exception as exc:
            db.rollback()

            import_job = db.get(
                ImportJob,
                import_job.id,
            )

            if import_job is not None:
                import_job.status = "failed"
                import_job.error_message = str(exc)
                db.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Student import failed",
            ) from exc

        finally:
            Path(file_path).unlink(
                missing_ok=True
            )