from datetime import datetime
from pydantic import BaseModel


class ImportCreateResponse(BaseModel):
    import_id: int
    filename: str
    status: str
    file_hash: str


class ImportSummary(BaseModel):
    total_rows: int
    valid: int
    invalid: int
    reference_errors: int
    existing: int
    duplicates: int
    ready_to_commit: int


class ImportDetailResponse(BaseModel):
    import_id: int
    filename: str
    status: str
    created_by: int | None
    created_at: datetime
    completed_at: datetime | None
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    error_message: str | None


class ValidateImportResponse(BaseModel):
    import_id: int
    status: str
    mapping: dict
    unmapped_columns: list[str]
    summary: ImportSummary
    records: list[dict]


class CommitImportResponse(BaseModel):
    import_id: int
    status: str
    imported_count: int
    imported_students: list[str]