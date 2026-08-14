from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.coe import CoE
from app.models.company import Company
from app.models.faculty import Faculty
from app.models.group import Group
from app.models.technology import Technology
from app.models.training import TrainingProgram, TrainingSession


class TrainingService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Training Programs
    # -------------------------

    def create_program(
        self,
        name: str,
        description: str | None,
        coe_id: int,
        company_id: int,
        technology_id: int,
        start_date,
        end_date,
        planned_hours: float,
    ) -> TrainingProgram:

        self._validate_coe(coe_id)
        self._validate_company(company_id)
        self._validate_technology(technology_id)

        if end_date < start_date:
            raise ValueError(
                "Training program end date cannot be earlier than start date"
            )

        if planned_hours <= 0:
            raise ValueError(
                "Planned training hours must be greater than zero"
            )

        program = TrainingProgram(
            name=name,
            description=description,
            coe_id=coe_id,
            company_id=company_id,
            technology_id=technology_id,
            start_date=start_date,
            end_date=end_date,
            planned_hours=planned_hours,
        )

        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)

        return program

    def get_program(
        self,
        program_id: int,
    ) -> TrainingProgram | None:
        return self.db.get(
            TrainingProgram,
            program_id,
        )

    def get_programs(
        self,
        coe_id: int | None = None,
        company_id: int | None = None,
        technology_id: int | None = None,
    ) -> list[TrainingProgram]:

        query = select(TrainingProgram)

        if coe_id is not None:
            query = query.where(
                TrainingProgram.coe_id == coe_id
            )

        if company_id is not None:
            query = query.where(
                TrainingProgram.company_id == company_id
            )

        if technology_id is not None:
            query = query.where(
                TrainingProgram.technology_id == technology_id
            )

        return list(
            self.db.scalars(query).all()
        )

    # -------------------------
    # Training Sessions
    # -------------------------

    def schedule_session(
        self,
        program_id: int,
        faculty_id: int,
        batch_id: int,
        group_id: int | None,
        title: str,
        start_at: datetime,
        end_at: datetime,
        hours: float,
    ) -> TrainingSession:

        program = self.db.get(
            TrainingProgram,
            program_id,
        )

        if program is None:
            raise ValueError(
                "Training program not found"
            )

        self._validate_faculty(faculty_id)
        self._validate_batch(batch_id)

        if group_id is not None:
            self._validate_group(group_id)

        if end_at <= start_at:
            raise ValueError(
                "Session end time must be later than start time"
            )

        if hours <= 0:
            raise ValueError(
                "Training session hours must be greater than zero"
            )

        session = TrainingSession(
            program_id=program_id,
            faculty_id=faculty_id,
            batch_id=batch_id,
            group_id=group_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            hours=hours,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(
        self,
        session_id: int,
    ) -> TrainingSession | None:
        return self.db.get(
            TrainingSession,
            session_id,
        )

    def get_sessions(
        self,
        program_id: int | None = None,
        batch_id: int | None = None,
        group_id: int | None = None,
    ) -> list[TrainingSession]:

        query = select(TrainingSession)

        if program_id is not None:
            query = query.where(
                TrainingSession.program_id == program_id
            )

        if batch_id is not None:
            query = query.where(
                TrainingSession.batch_id == batch_id
            )

        if group_id is not None:
            query = query.where(
                TrainingSession.group_id == group_id
            )

        return list(
            self.db.scalars(query).all()
        )

    # -------------------------
    # Cohort assignment
    # -------------------------

    def assign_cohort(
        self,
        session: TrainingSession,
        batch_id: int,
        group_id: int | None = None,
    ) -> TrainingSession:

        self._validate_batch(batch_id)

        if group_id is not None:
            self._validate_group(group_id)

        session.batch_id = batch_id
        session.group_id = group_id

        self.db.commit()
        self.db.refresh(session)

        return session

    # -------------------------
    # Completion calculation
    # -------------------------

    def calculate_completion(
        self,
        program_id: int,
    ) -> dict:

        program = self.db.get(
            TrainingProgram,
            program_id,
        )

        if program is None:
            raise ValueError(
                "Training program not found"
            )

        sessions = self.db.scalars(
            select(TrainingSession).where(
                TrainingSession.program_id == program_id
            )
        ).all()

        completed_hours = sum(
            session.hours
            for session in sessions
        )

        planned_hours = program.planned_hours

        if planned_hours <= 0:
            completion_percentage = 0.0
        else:
            completion_percentage = round(
                min(
                    (completed_hours / planned_hours) * 100,
                    100.0,
                ),
                2,
            )

        return {
            "program_id": program.id,
            "planned_hours": planned_hours,
            "completed_hours": completed_hours,
            "completion_percentage": completion_percentage,
            "session_count": len(sessions),
        }

    # -------------------------
    # Validation helpers
    # -------------------------

    def _validate_coe(
        self,
        coe_id: int,
    ) -> None:
        if self.db.get(CoE, coe_id) is None:
            raise ValueError("CoE not found")

    def _validate_company(
        self,
        company_id: int,
    ) -> None:
        if self.db.get(Company, company_id) is None:
            raise ValueError("Company not found")

    def _validate_technology(
        self,
        technology_id: int,
    ) -> None:
        if self.db.get(
            Technology,
            technology_id,
        ) is None:
            raise ValueError("Technology not found")

    def _validate_faculty(
        self,
        faculty_id: int,
    ) -> None:
        if self.db.get(
            Faculty,
            faculty_id,
        ) is None:
            raise ValueError("Faculty not found")

    def _validate_batch(
        self,
        batch_id: int,
    ) -> None:
        if self.db.get(
            Batch,
            batch_id,
        ) is None:
            raise ValueError("Batch not found")

    def _validate_group(
        self,
        group_id: int,
    ) -> None:
        if self.db.get(
            Group,
            group_id,
        ) is None:
            raise ValueError("Group not found")