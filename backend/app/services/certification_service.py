from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.certification import Certification, CertificationAttempt
from app.models.student import Student
from app.schemas.certification import (
    CertificationAttemptResponse,
    CertificationSummary,
)


class CertificationService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Certifications
    # -------------------------

    def create_certification(
        self,
        name: str,
        issuing_organization: str | None,
    ) -> Certification:
        certification = Certification(
            name=name,
            issuing_organization=issuing_organization,
        )

        self.db.add(certification)
        self.db.commit()
        self.db.refresh(certification)

        return certification

    def get_certification(
        self,
        certification_id: int,
    ) -> Certification | None:
        return self.db.get(Certification, certification_id)

    def get_certifications(self) -> list[Certification]:
        return list(
            self.db.scalars(
                select(Certification)
            ).all()
        )

    # -------------------------
    # Certification Attempts
    # -------------------------

    def record_attempt(
        self,
        student_id: int,
        certification_id: int,
        status: str,
        score: float | None,
    ) -> CertificationAttempt:
        student = self.db.get(Student, student_id)

        if student is None:
            raise ValueError("Student not found")

        if self.db.get(Certification, certification_id) is None:
            raise ValueError("Certification not found")

        attempt = CertificationAttempt(
            student_id=student_id,
            certification_id=certification_id,
            status=status,
            score=score,
        )

        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def get_attempts(
        self,
        student_id: int | None = None,
        certification_id: int | None = None,
    ) -> list[CertificationAttemptResponse]:
        query = select(CertificationAttempt)

        if student_id is not None:
            query = query.where(CertificationAttempt.student_id == student_id)

        if certification_id is not None:
            query = query.where(
                CertificationAttempt.certification_id == certification_id
            )

        attempts = list(self.db.scalars(query).all())
        return [
            self._to_response(attempt)
            for attempt in attempts
        ]

    def update_attempt(
        self,
        attempt: CertificationAttempt,
        status: str | None,
        score: float | None,
    ) -> CertificationAttempt:
        if status is not None:
            attempt.status = status

        if score is not None:
            attempt.score = score

        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def get_summary(self) -> CertificationSummary:
        total_attempts = self.db.scalar(
            select(func.count(CertificationAttempt.id))
        ) or 0

        completed = self.db.scalar(
            select(func.count(CertificationAttempt.id)).where(
                CertificationAttempt.status == "completed"
            )
        ) or 0

        in_progress = self.db.scalar(
            select(func.count(CertificationAttempt.id)).where(
                CertificationAttempt.status == "in_progress"
            )
        ) or 0

        pending = self.db.scalar(
            select(func.count(CertificationAttempt.id)).where(
                CertificationAttempt.status == "pending"
            )
        ) or 0

        recent = list(
            self.db.scalars(
                select(CertificationAttempt)
                .order_by(CertificationAttempt.id.desc())
                .limit(10)
            ).all()
        )

        return CertificationSummary(
            total_certifications=self.db.scalar(
                select(func.count(Certification.id))
            ) or 0,
            total_attempts=total_attempts,
            completed=completed,
            in_progress=in_progress,
            pending=pending,
            recent_attempts=[
                self._to_response(attempt)
                for attempt in recent
            ],
        )

    def _to_response(
        self,
        attempt: CertificationAttempt,
    ) -> CertificationAttemptResponse:
        student = self.db.get(Student, attempt.student_id)
        certification = self.db.get(Certification, attempt.certification_id)

        return CertificationAttemptResponse(
            id=attempt.id,
            student_id=attempt.student_id,
            certification_id=attempt.certification_id,
            status=attempt.status,
            score=attempt.score,
            student_name=student.name if student else None,
            certification_name=certification.name if certification else None,
        )
