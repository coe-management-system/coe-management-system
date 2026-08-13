from pydantic import BaseModel


class ImportResponse(BaseModel):
    import_job_id: int
    filename: str
    status: str

    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int

    imported_students: list[str]
    skipped_existing: list[str]
    reference_errors: list[dict]
    validation_errors: list[dict]