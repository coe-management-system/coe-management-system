"""
Attendance Analytics Module (M3-01)

Provides analytics for student attendance including percentages, trends,
and warning/critical case identification.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.student import Student
from app.models.subject import Subject
from app.models.batch import Batch
from app.models.group import Group


class AttendanceAnalytics:
    """
    Analytics engine for attendance data.
    
    Computes attendance percentages, trends, and identifies warning/critical cases.
    """

    # Thresholds for warning and critical classifications
    WARNING_THRESHOLD = 75.0  # Below 75% = warning
    CRITICAL_THRESHOLD = 60.0  # Below 60% = critical

    def __init__(self, db: Session):
        self.db = db

    def get_student_attendance_percentage(
        self,
        student_id: int,
        subject_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Calculate attendance percentage for a student.
        
        Args:
            student_id: ID of the student
            subject_id: Optional filter by subject
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with attendance statistics
        """
        query = select(
            func.count(Attendance.id).label("total_sessions"),
            func.sum(
                (Attendance.status == "present").cast(func.Integer())
            ).label("present_count"),
        ).where(Attendance.student_id == student_id)

        if subject_id:
            query = query.where(Attendance.subject_id == subject_id)
        if start_date:
            query = query.where(Attendance.session_date >= start_date)
        if end_date:
            query = query.where(Attendance.session_date <= end_date)

        result = self.db.execute(query).first()
        total = result.total_sessions or 0
        present = result.present_count or 0

        percentage = (present / total * 100) if total > 0 else 0.0

        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "total_sessions": total,
            "present_sessions": present,
            "absent_sessions": total - present,
            "attendance_percentage": round(percentage, 2),
            "classification": self._classify_attendance(percentage),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def get_batch_attendance_summary(
        self,
        batch_id: int,
        subject_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Get attendance summary for an entire batch.
        
        Args:
            batch_id: ID of the batch
            subject_id: Optional filter by subject
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with batch attendance statistics
        """
        # Get all students in the batch
        students = self.db.execute(
            select(Student.id).where(Student.batch_id == batch_id)
        ).scalars().all()

        if not students:
            return {
                "batch_id": batch_id,
                "subject_id": subject_id,
                "students": [],
                "summary": {
                    "total_students": 0,
                    "avg_attendance": 0.0,
                    "warning_count": 0,
                    "critical_count": 0,
                },
            }

        student_stats = []
        warning_count = 0
        critical_count = 0
        total_percentage = 0.0

        for student_id in students:
            stats = self.get_student_attendance_percentage(
                student_id, subject_id, start_date, end_date
            )
            student_stats.append({
                "student_id": student_id,
                "attendance_percentage": stats["attendance_percentage"],
                "classification": stats["classification"],
            })
            total_percentage += stats["attendance_percentage"]
            if stats["classification"] == "warning":
                warning_count += 1
            elif stats["classification"] == "critical":
                critical_count += 1

        avg_attendance = total_percentage / len(students) if students else 0.0

        return {
            "batch_id": batch_id,
            "subject_id": subject_id,
            "students": student_stats,
            "summary": {
                "total_students": len(students),
                "avg_attendance": round(avg_attendance, 2),
                "warning_count": warning_count,
                "critical_count": critical_count,
            },
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def get_attendance_trends(
        self,
        student_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        weeks: int = 8,
    ) -> dict:
        """
        Calculate attendance trends over time.
        
        Args:
            student_id: Optional filter by student
            batch_id: Optional filter by batch
            subject_id: Optional filter by subject
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with weekly attendance trends
        """
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)

        query = select(
            Attendance.session_date,
            func.count(Attendance.id).label("total"),
            func.sum(
                (Attendance.status == "present").cast(func.Integer())
            ).label("present"),
        ).where(
            and_(
                Attendance.session_date >= start_date,
                Attendance.session_date <= end_date,
            )
        )

        if student_id:
            query = query.where(Attendance.student_id == student_id)
        elif batch_id:
            # Join with students to filter by batch
            query = query.join(Student, Attendance.student_id == Student.id).where(
                Student.batch_id == batch_id
            )

        if subject_id:
            query = query.where(Attendance.subject_id == subject_id)

        query = query.group_by(Attendance.session_date).order_by(Attendance.session_date)

        results = self.db.execute(query).all()

        trends = []
        for row in results:
            total = row.total or 0
            present = row.present or 0
            pct = (present / total * 100) if total > 0 else 0.0
            trends.append({
                "date": row.session_date.isoformat(),
                "total_sessions": total,
                "present": present,
                "attendance_percentage": round(pct, 2),
            })

        # Calculate trend direction
        if len(trends) >= 2:
            first_week_avg = sum(t["attendance_percentage"] for t in trends[:len(trends)//2]) / (len(trends)//2)
            last_week_avg = sum(t["attendance_percentage"] for t in trends[len(trends)//2:]) / (len(trends) - len(trends)//2)
            trend_direction = "improving" if last_week_avg > first_week_avg else "declining" if last_week_avg < first_week_avg else "stable"
        else:
            trend_direction = "insufficient_data"

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "weeks_analyzed": weeks,
            "trends": trends,
            "trend_direction": trend_direction,
        }

    def get_warning_critical_cases(
        self,
        batch_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Identify students in warning or critical attendance categories.
        
        Args:
            batch_id: Optional filter by batch
            subject_id: Optional filter by subject
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with warning and critical cases
        """
        if batch_id:
            students = self.db.execute(
                select(Student.id).where(Student.batch_id == batch_id)
            ).scalars().all()
        else:
            students = self.db.execute(select(Student.id)).scalars().all()

        warning_cases = []
        critical_cases = []

        for student_id in students:
            stats = self.get_student_attendance_percentage(
                student_id, subject_id, start_date, end_date
            )
            if stats["total_sessions"] == 0:
                continue
            if stats["classification"] == "warning":
                warning_cases.append({
                    "student_id": student_id,
                    "attendance_percentage": stats["attendance_percentage"],
                    "total_sessions": stats["total_sessions"],
                    "present_sessions": stats["present_sessions"],
                })
            elif stats["classification"] == "critical":
                critical_cases.append({
                    "student_id": student_id,
                    "attendance_percentage": stats["attendance_percentage"],
                    "total_sessions": stats["total_sessions"],
                    "present_sessions": stats["present_sessions"],
                })

        return {
            "warning_cases": warning_cases,
            "critical_cases": critical_cases,
            "total_warning": len(warning_cases),
            "total_critical": len(critical_cases),
            "thresholds": {
                "warning": self.WARNING_THRESHOLD,
                "critical": self.CRITICAL_THRESHOLD,
            },
        }

    def get_subject_attendance_report(
        self,
        subject_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Get attendance report for a specific subject across all batches.
        
        Args:
            subject_id: ID of the subject
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with subject attendance report
        """
        # Get all batches that have this subject (via students)
        batches = self.db.execute(
            select(Batch.id, Batch.name)
            .join(Student, Student.batch_id == Batch.id)
            .join(Attendance, Attendance.student_id == Student.id)
            .where(Attendance.subject_id == subject_id)
            .distinct()
        ).all()

        batch_reports = []
        for batch_id, batch_name in batches:
            report = self.get_batch_attendance_summary(
                batch_id, subject_id, start_date, end_date
            )
            report["batch_name"] = batch_name
            batch_reports.append(report)

        # Overall stats
        all_students = []
        for batch in batch_reports:
            all_students.extend(batch["students"])

        total_students = len(all_students)
        avg_attendance = sum(s["attendance_percentage"] for s in all_students) / total_students if total_students > 0 else 0.0

        return {
            "subject_id": subject_id,
            "batches": batch_reports,
            "overall": {
                "total_students": total_students,
                "average_attendance": round(avg_attendance, 2),
            },
        }

    def _classify_attendance(self, percentage: float) -> str:
        """Classify attendance percentage into categories."""
        if percentage < self.CRITICAL_THRESHOLD:
            return "critical"
        elif percentage < self.WARNING_THRESHOLD:
            return "warning"
        elif percentage < 90.0:
            return "normal"
        else:
            return "excellent"


def calculate_attendance_percentage(
    present_count: int,
    total_count: int,
) -> float:
    """Utility function to calculate attendance percentage."""
    if total_count == 0:
        return 0.0
    return round((present_count / total_count) * 100, 2)


def classify_attendance_status(percentage: float) -> str:
    """Classify attendance percentage into status categories."""
    if percentage < 60.0:
        return "critical"
    elif percentage < 75.0:
        return "warning"
    elif percentage < 90.0:
        return "normal"
    else:
        return "excellent"