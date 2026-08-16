"""
Syllabus Analytics Module (M3-02)

Provides analytics for syllabus coverage including planned/completed/pending
classes, progress tracking, and deadline risk assessment.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.syllabus import SyllabusTopic
from app.models.subject import Subject
from app.models.batch import Batch
from app.models.student import Student


class SyllabusAnalytics:
    """
    Analytics engine for syllabus coverage data.
    
    Tracks planned vs completed classes, syllabus progress, and deadline risk.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_syllabus_progress(
        self,
        subject_id: int,
        batch_id: Optional[int] = None,
    ) -> dict:
        """
        Get overall syllabus progress for a subject.
        
        Args:
            subject_id: ID of the subject
            batch_id: Optional filter by batch
            
        Returns:
            Dictionary with syllabus progress statistics
        """
        query = select(SyllabusTopic).where(SyllabusTopic.subject_id == subject_id)
        
        topics = self.db.execute(query).scalars().all()
        
        if not topics:
            return {
                "subject_id": subject_id,
                "batch_id": batch_id,
                "topics": [],
                "summary": {
                    "total_topics": 0,
                    "total_planned_classes": 0,
                    "total_completed_classes": 0,
                    "total_pending_classes": 0,
                    "overall_progress_percentage": 0.0,
                    "topics_completed": 0,
                    "topics_in_progress": 0,
                    "topics_not_started": 0,
                },
            }

        topic_details = []
        total_planned = 0
        total_completed = 0
        topics_completed = 0
        topics_in_progress = 0
        topics_not_started = 0

        for topic in topics:
            planned = topic.planned_classes
            completed = topic.completed_classes
            pending = max(0, planned - completed)
            
            if planned > 0:
                progress = (completed / planned) * 100
            else:
                progress = 0.0

            if completed >= planned and planned > 0:
                status = "completed"
                topics_completed += 1
            elif completed > 0:
                status = "in_progress"
                topics_in_progress += 1
            else:
                status = "not_started"
                topics_not_started += 1

            total_planned += planned
            total_completed += completed

            topic_details.append({
                "topic_id": topic.id,
                "unit": topic.unit,
                "topic": topic.topic,
                "planned_classes": planned,
                "completed_classes": completed,
                "pending_classes": pending,
                "progress_percentage": round(progress, 2),
                "status": status,
                "target_date": topic.target_date.isoformat() if topic.target_date else None,
                "actual_date": topic.actual_date.isoformat() if topic.actual_date else None,
            })

        overall_progress = (total_completed / total_planned * 100) if total_planned > 0 else 0.0

        return {
            "subject_id": subject_id,
            "batch_id": batch_id,
            "topics": topic_details,
            "summary": {
                "total_topics": len(topics),
                "total_planned_classes": total_planned,
                "total_completed_classes": total_completed,
                "total_pending_classes": total_planned - total_completed,
                "overall_progress_percentage": round(overall_progress, 2),
                "topics_completed": topics_completed,
                "topics_in_progress": topics_in_progress,
                "topics_not_started": topics_not_started,
            },
        }

    def get_deadline_risk(
        self,
        subject_id: int,
        days_ahead: int = 14,
    ) -> dict:
        """
        Assess deadline risk for syllabus topics.
        
        Args:
            subject_id: ID of the subject
            days_ahead: Number of days ahead to check for upcoming deadlines
            
        Returns:
            Dictionary with deadline risk assessment
        """
        today = date.today()
        deadline_cutoff = today + timedelta(days=days_ahead)

        topics = self.db.execute(
            select(SyllabusTopic)
            .where(
                and_(
                    SyllabusTopic.subject_id == subject_id,
                    SyllabusTopic.target_date.isnot(None),
                    SyllabusTopic.target_date <= deadline_cutoff,
                )
            )
        ).scalars().all()

        risk_items = []
        for topic in topics:
            days_remaining = (topic.target_date - today).days
            planned = topic.planned_classes
            completed = topic.completed_classes
            pending = max(0, planned - completed)
            
            if planned > 0:
                progress = (completed / planned) * 100
            else:
                progress = 0.0

            # Risk assessment logic
            if days_remaining < 0:
                risk_level = "overdue"
            elif days_remaining == 0:
                risk_level = "due_today"
            elif days_remaining <= 3:
                risk_level = "critical"
            elif days_remaining <= 7:
                risk_level = "high"
            elif progress < 50:
                risk_level = "moderate"
            else:
                risk_level = "on_track"

            risk_items.append({
                "topic_id": topic.id,
                "unit": topic.unit,
                "topic": topic.topic,
                "target_date": topic.target_date.isoformat(),
                "days_remaining": days_remaining,
                "planned_classes": planned,
                "completed_classes": completed,
                "pending_classes": pending,
                "progress_percentage": round(progress, 2),
                "risk_level": risk_level,
            })

        # Sort by risk level severity and days remaining
        risk_order = {"overdue": 0, "due_today": 1, "critical": 2, "high": 3, "moderate": 4, "on_track": 5}
        risk_items.sort(key=lambda x: (risk_order.get(x["risk_level"], 99), x["days_remaining"]))

        return {
            "subject_id": subject_id,
            "analysis_period_days": days_ahead,
            "today": today.isoformat(),
            "risk_items": risk_items,
            "summary": {
                "total_at_risk": len([r for r in risk_items if r["risk_level"] in ("overdue", "due_today", "critical", "high")]),
                "overdue": len([r for r in risk_items if r["risk_level"] == "overdue"]),
                "due_today": len([r for r in risk_items if r["risk_level"] == "due_today"]),
                "critical": len([r for r in risk_items if r["risk_level"] == "critical"]),
                "high": len([r for r in risk_items if r["risk_level"] == "high"]),
                "moderate": len([r for r in risk_items if r["risk_level"] == "moderate"]),
                "on_track": len([r for r in risk_items if r["risk_level"] == "on_track"]),
            },
        }

    def get_batch_syllabus_status(
        self,
        batch_id: int,
    ) -> dict:
        """
        Get syllabus status for all subjects in a batch.
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            Dictionary with syllabus status per subject
        """
        # Get subjects for this batch via students
        subjects = self.db.execute(
            select(Subject.id, Subject.name, Subject.code)
            .join(Student, Student.batch_id == Batch.id)
            .join(Batch, Batch.id == Student.batch_id)
            .where(Batch.id == batch_id)
            .distinct()
        ).all()

        subject_reports = []
        for subject_id, subject_name, subject_code in subjects:
            progress = self.get_syllabus_progress(subject_id)
            risk = self.get_deadline_risk(subject_id)
            
            subject_reports.append({
                "subject_id": subject_id,
                "subject_name": subject_name,
                "subject_code": subject_code,
                "progress": progress["summary"],
                "deadline_risk": risk["summary"],
            })

        return {
            "batch_id": batch_id,
            "subjects": subject_reports,
            "overall": {
                "total_subjects": len(subject_reports),
                "subjects_on_track": len([s for s in subject_reports if s["deadline_risk"]["critical"] == 0 and s["deadline_risk"]["high"] == 0]),
                "subjects_at_risk": len([s for s in subject_reports if s["deadline_risk"]["critical"] > 0 or s["deadline_risk"]["high"] > 0]),
            },
        }

    def get_pending_classes_summary(
        self,
        subject_id: Optional[int] = None,
        batch_id: Optional[int] = None,
    ) -> dict:
        """
        Get summary of pending classes across topics.
        
        Args:
            subject_id: Optional filter by subject
            batch_id: Optional filter by batch
            
        Returns:
            Dictionary with pending classes summary
        """
        query = select(SyllabusTopic)
        
        if subject_id:
            query = query.where(SyllabusTopic.subject_id == subject_id)
        
        topics = self.db.execute(query).scalars().all()

        total_pending = 0
        topics_with_pending = 0
        topic_details = []

        for topic in topics:
            pending = max(0, topic.planned_classes - topic.completed_classes)
            if pending > 0:
                topics_with_pending += 1
                total_pending += pending
                topic_details.append({
                    "topic_id": topic.id,
                    "unit": topic.unit,
                    "topic": topic.topic,
                    "pending_classes": pending,
                    "target_date": topic.target_date.isoformat() if topic.target_date else None,
                })

        return {
            "subject_id": subject_id,
            "batch_id": batch_id,
            "total_pending_classes": total_pending,
            "topics_with_pending": topics_with_pending,
            "topics": topic_details,
        }


def calculate_syllabus_progress(
    planned_classes: int,
    completed_classes: int,
) -> dict:
    """
    Calculate syllabus progress metrics.
    
    Args:
        planned_classes: Total planned classes
        completed_classes: Classes already completed
        
    Returns:
        Dictionary with progress metrics
    """
    if planned_classes == 0:
        return {
            "planned_classes": 0,
            "completed_classes": 0,
            "pending_classes": 0,
            "progress_percentage": 0.0,
            "status": "not_started",
        }

    pending = max(0, planned_classes - completed_classes)
    progress = (completed_classes / planned_classes) * 100

    if completed_classes >= planned_classes:
        status = "completed"
    elif completed_classes > 0:
        status = "in_progress"
    else:
        status = "not_started"

    return {
        "planned_classes": planned_classes,
        "completed_classes": completed_classes,
        "pending_classes": pending,
        "progress_percentage": round(progress, 2),
        "status": status,
    }


def assess_deadline_risk(
    target_date: Optional[date],
    planned_classes: int,
    completed_classes: int,
    today: Optional[date] = None,
) -> dict:
    """
    Assess deadline risk for a syllabus topic.
    
    Args:
        target_date: Target completion date
        planned_classes: Total planned classes
        completed_classes: Classes completed
        today: Current date (defaults to today)
        
    Returns:
        Dictionary with risk assessment
    """
    if today is None:
        today = date.today()

    if target_date is None:
        return {
            "risk_level": "no_deadline",
            "days_remaining": None,
        }

    days_remaining = (target_date - today).days
    progress_data = calculate_syllabus_progress(planned_classes, completed_classes)
    progress = progress_data["progress_percentage"]

    if days_remaining < 0:
        risk_level = "overdue"
    elif days_remaining == 0:
        risk_level = "due_today"
    elif days_remaining <= 3:
        risk_level = "critical"
    elif days_remaining <= 7:
        risk_level = "high"
    elif progress < 50:
        risk_level = "moderate"
    else:
        risk_level = "on_track"

    return {
        "risk_level": risk_level,
        "days_remaining": days_remaining,
        "progress_percentage": progress,
    }