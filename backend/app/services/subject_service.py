from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.subject import Subject


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_subject(
        self,
        code: str,
        name: str,
        department_id: int,
    ) -> Subject:
        department = self.db.get(
            Department,
            department_id,
        )

        if department is None:
            raise ValueError("Department not found")

        existing = self.db.scalar(
            select(Subject).where(
                Subject.code == code
            )
        )

        if existing is not None:
            raise ValueError(
                "Subject code already exists"
            )

        subject = Subject(
            code=code,
            name=name,
            department_id=department_id,
        )

        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)

        return subject

    def get_subject(
        self,
        subject_id: int,
    ) -> Subject | None:
        return self.db.get(
            Subject,
            subject_id,
        )

    def get_subjects(
        self,
        department_id: int | None = None,
    ) -> list[Subject]:
        query = select(Subject)

        if department_id is not None:
            query = query.where(
                Subject.department_id == department_id
            )

        return list(
            self.db.scalars(query).all()
        )

    def update_subject(
        self,
        subject: Subject,
        code: str | None = None,
        name: str | None = None,
        department_id: int | None = None,
    ) -> Subject:
        if code is not None and code != subject.code:
            existing = self.db.scalar(
                select(Subject).where(
                    Subject.code == code,
                    Subject.id != subject.id,
                )
            )

            if existing is not None:
                raise ValueError(
                    "Subject code already exists"
                )

            subject.code = code

        if name is not None:
            subject.name = name

        if department_id is not None:
            department = self.db.get(
                Department,
                department_id,
            )

            if department is None:
                raise ValueError(
                    "Department not found"
                )

            subject.department_id = department_id

        self.db.commit()
        self.db.refresh(subject)

        return subject