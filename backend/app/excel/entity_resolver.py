"""
Resolves Excel text values (e.g. "CSE", "2026", "4A") to real database entity IDs.
This is the ONLY place Excel-layer code is allowed to query the database,
and it never writes — only reads for resolution purposes.
"""

from sqlalchemy.orm import Session
from app.models.department import Department
from app.models.batch import Batch
from app.models.group import Group
from app.models.student import Student


def resolve_department(db: Session, department_code: str):
    """Matches Excel department value against Department.code."""
    if not department_code:
        return None, "Missing department value"
    dept = db.query(Department).filter(Department.code == department_code.strip()).first()
    if not dept:
        return None, f"Unknown department code: {department_code}"
    return dept, None


def resolve_batch(db: Session, department_id: int, year_value: str):
    """Matches Excel batch/year value against Batch.year scoped to the resolved department."""
    if not year_value:
        return None, "Missing batch/year value"
    try:
        year_int = int(str(year_value).strip())
    except ValueError:
        return None, f"Invalid batch/year value: {year_value}"

    batch = db.query(Batch).filter(
        Batch.department_id == department_id,
        Batch.year == year_int
    ).first()
    if not batch:
        return None, f"No batch found for year {year_value} in this department"
    return batch, None


def resolve_group(db: Session, batch_id: int, group_name: str):
    """Matches Excel group/section value against Group.name scoped to the resolved batch."""
    if not group_name:
        return None, "Missing group/section value"
    group = db.query(Group).filter(
        Group.batch_id == batch_id,
        Group.name == group_name.strip()
    ).first()
    if not group:
        return None, f"No group '{group_name}' found in this batch"
    return group, None


def find_existing_student(db: Session, roll_no: str):
    """Checks if a student with this roll_no already exists in the database."""
    if not roll_no:
        return None
    return db.query(Student).filter(Student.roll_no == roll_no.strip()).first()