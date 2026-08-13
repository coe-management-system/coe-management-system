from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student


def get_all_students(db: Session) -> List[Student]:
    """Retrieve all students from the database."""
    return list(db.scalars(select(Student)).all())


def get_student_by_roll_no(db: Session, roll_no: str) -> Optional[Student]:
    """Retrieve a single student by their roll number."""
    if not roll_no:
        raise ValueError("Invalid student identifier")
    
    return db.scalar(
        select(Student).where(Student.roll_no == roll_no)
    )
