from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.student import Student
from typing import Any, List, Dict

class AttendanceService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        student_id: int,
        subject_id: int,
        session_date,
        status: str,
    ) -> Attendance:
        existing = self.db.scalar(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id,
                Attendance.session_date == session_date,
            )
        )

        if existing is not None:
            raise ValueError(
                "Attendance already recorded for this student, "
                "subject and session"
            )

        attendance = Attendance(
            student_id=student_id,
            subject_id=subject_id,
            session_date=session_date,
            status=status,
        )

        self.db.add(attendance)
        self.db.commit()
        self.db.refresh(attendance)

        return attendance

    def bulk_record(
        self,
        subject_id: int,
        session_date,
        records: list[dict],
    ) -> list[Attendance]:
        if not records:
            raise ValueError("Attendance records cannot be empty")

        student_ids = [record["student_id"] for record in records]

        if len(student_ids) != len(set(student_ids)):
            raise ValueError(
                "Duplicate student IDs found in attendance records"
            )

        existing_records = self.db.scalars(
            select(Attendance).where(
                Attendance.subject_id == subject_id,
                Attendance.session_date == session_date,
                Attendance.student_id.in_(student_ids),
            )
        ).all()

        if existing_records:
            existing_student_ids = {
                record.student_id
                for record in existing_records
            }

            raise ValueError(
                "Attendance already exists for student IDs: "
                + ", ".join(
                    str(student_id)
                    for student_id in sorted(existing_student_ids)
                )
            )

        attendance_records = [
            Attendance(
                student_id=record["student_id"],
                subject_id=subject_id,
                session_date=session_date,
                status=record["status"],
            )
            for record in records
        ]

        try:
            self.db.add_all(attendance_records)
            self.db.commit()

            for attendance in attendance_records:
                self.db.refresh(attendance)

            return attendance_records

        except Exception:
            self.db.rollback()
            raise

    def calculate_percentage(
        self,
        student_id: int,
        subject_id: int,
    ) -> float:
        records = self.db.scalars(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id,
            )
        ).all()

        eligible_records = [
            record
            for record in records
            if record.status in {"PRESENT", "ABSENT"}
        ]

        if not eligible_records:
            return 0.0

        attended = sum(
            1
            for record in eligible_records
            if record.status == "PRESENT"
        )

        return round(
            (attended / len(eligible_records)) * 100,
            2,
        )

    def get_low_attendance_students(
        self,
        threshold: float = 75.0,
    ) -> list[dict]:
        students = self.db.scalars(
            select(Student)
        ).all()

        results = []

        for student in students:
            subjects = self.db.scalars(
                select(Attendance.subject_id)
                .where(Attendance.student_id == student.id)
                .distinct()
            ).all()

            for subject_id in subjects:
                percentage = self.calculate_percentage(
                    student_id=student.id,
                    subject_id=subject_id,
                )

                if percentage < threshold:
                    results.append(
                        {
                            "student_id": student.id,
                            "roll_no": student.roll_no,
                            "name": student.name,
                            "subject_id": subject_id,
                            "attendance_percentage": percentage,
                        }
                    )

        return results
    
    def get_summary(
        self,
        student_id: int,
        subject_id: int,
    ) -> dict:
        records = self.db.scalars(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id,
            )
        ).all()

        eligible_sessions = sum(
            1
            for record in records
            if record.status in {"PRESENT", "ABSENT"}
        )

        attended_sessions = sum(
            1
            for record in records
            if record.status == "PRESENT"
        )
        percentage = self.calculate_percentage(
            student_id=student_id,
            subject_id=subject_id,
        )
        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "attended_sessions": attended_sessions,
            "eligible_sessions": eligible_sessions,
            "attendance_percentage": percentage,
        }

    def get_student_attendance(
        self,
        student_identifier: str,
    ) -> dict:
        stmt = select(Student).where(Student.roll_no == student_identifier)
        if student_identifier.isdigit():
            stmt = select(Student).where(
                (Student.roll_no == student_identifier) | (Student.id == int(student_identifier))
            )
        student = self.db.scalar(stmt)
        if not student:
            raise ValueError(f"Student with identifier '{student_identifier}' not found.")

        subjects = self.db.scalars(
            select(Attendance.subject_id)
            .where(Attendance.student_id == student.id)
            .distinct()
        ).all()

        subject_summaries = []
        total_attended = 0
        total_eligible = 0

        for subj_id in subjects:
            summary = self.get_summary(student_id=student.id, subject_id=subj_id)
            subject_summaries.append(summary)
            total_attended += summary["attended_sessions"]
            total_eligible += summary["eligible_sessions"]

        overall_percentage = (
            round((total_attended / total_eligible) * 100, 2)
            if total_eligible > 0
            else 0.0
        )

        return {
            "student_id": student.id,
            "roll_no": student.roll_no,
            "name": student.name,
            "overall_attendance_percentage": overall_percentage,
            "total_attended_sessions": total_attended,
            "total_eligible_sessions": total_eligible,
            "subjects": subject_summaries,
        }


def get_low_attendance_students_mock() -> list[dict[str, Any]]:
    """
    Backward-compatible mock interface used by the existing AI tool.

    This remains unchanged until the AI module is migrated to the
    production attendance service by its owner.
    """
    return [
        {
            "roll_no": "CSE101",
            "name": "Rahul",
            "attendance_percentage": 68,
        },
        {
            "roll_no": "CSE102",
            "name": "Aman",
            "attendance_percentage": 72,
        },
    ]
