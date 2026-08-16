"""
Syllabus Conflicts Detection Module (M3-04)

Detects conflicts between syllabus requirements and the timetable,
including insufficient teaching capacity, deadline violations, and
topic sequencing conflicts.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.syllabus import SyllabusTopic
from app.models.subject import Subject
from app.models.timetable import TimetableEvent
from app.models.batch import Batch
from app.models.student import Student


class SyllabusConflictDetector:
    """
    Detects conflicts between syllabus requirements and scheduled classes.
    
    Conflict types:
    - Insufficient teaching capacity (not enough scheduled sessions for planned classes)
    - Deadline violations (target dates at risk)
    - Topic sequencing conflicts (prerequisites not met)
    - Batch timetable overload (too many classes for syllabus completion)
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_insufficient_capacity(
        self,
        subject_id: int,
        batch_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Detect if scheduled classes are insufficient for planned syllabus classes.
        
        Args:
            subject_id: ID of the subject
            batch_id: Optional filter by batch
            start_date: Optional start date for analysis period
            end_date: Optional end date for analysis period
            
        Returns:
            Dictionary with capacity conflict details
        """
        # Get syllabus topics for the subject
        topics_query = select(SyllabusTopic).where(SyllabusTopic.subject_id == subject_id)
        topics = self.db.execute(topics_query).scalars().all()

        if not topics:
            return {
                "subject_id": subject_id,
                "batch_id": batch_id,
                "conflict": False,
                "message": "No syllabus topics found for subject",
                "details": [],
            }

        total_planned = sum(t.planned_classes for t in topics)

        # Count scheduled timetable events for this subject/batch
        events_query = select(func.count(TimetableEvent.id)).where(
            TimetableEvent.subject_id == subject_id
        )

        if batch_id:
            events_query = events_query.where(TimetableEvent.batch_id == batch_id)
        if start_date:
            events_query = events_query.where(TimetableEvent.date >= start_date)
        if end_date:
            events_query = events_query.where(TimetableEvent.date <= end_date)

        scheduled_count = self.db.execute(events_query).scalar() or 0

        deficit = total_planned - scheduled_count
        conflict = deficit > 0

        return {
            "subject_id": subject_id,
            "batch_id": batch_id,
            "conflict": conflict,
            "conflict_type": "insufficient_capacity",
            "total_planned_classes": total_planned,
            "scheduled_classes": scheduled_count,
            "deficit": deficit,
            "details": [
                {
                    "topic_id": t.id,
                    "topic": t.topic,
                    "planned": t.planned_classes,
                }
                for t in topics
            ],
        }

    def detect_deadline_violations(
        self,
        subject_id: int,
        days_ahead: int = 14,
    ) -> dict:
        """
        Detect syllabus topics at risk of missing target dates.
        
        Args:
            subject_id: ID of the subject
            days_ahead: Number of days ahead to check
            
        Returns:
            Dictionary with deadline violation conflicts
        """
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        topics = self.db.execute(
            select(SyllabusTopic)
            .where(
                and_(
                    SyllabusTopic.subject_id == subject_id,
                    SyllabusTopic.target_date.isnot(None),
                    SyllabusTopic.target_date <= cutoff,
                )
            )
        ).scalars().all()

        violations = []
        for topic in topics:
            days_remaining = (topic.target_date - today).days
            planned = topic.planned_classes
            completed = topic.completed_classes
            pending = max(0, planned - completed)

            # Check if there are enough scheduled classes before target date
            scheduled_before_deadline = self.db.execute(
                select(func.count(TimetableEvent.id)).where(
                    and_(
                        TimetableEvent.subject_id == subject_id,
                        TimetableEvent.date <= topic.target_date,
                    )
                )
            ).scalar() or 0

            if completed + scheduled_before_deadline < planned:
                violations.append({
                    "topic_id": topic.id,
                    "topic": topic.topic,
                    "target_date": topic.target_date.isoformat(),
                    "days_remaining": days_remaining,
                    "planned_classes": planned,
                    "completed_classes": completed,
                    "pending_classes": pending,
                    "scheduled_before_deadline": scheduled_before_deadline,
                    "shortfall": planned - completed - scheduled_before_deadline,
                })

        return {
            "subject_id": subject_id,
            "conflict": len(violations) > 0,
            "conflict_type": "deadline_violation",
            "analysis_period_days": days_ahead,
            "violations": violations,
        }

    def detect_topic_sequencing_conflicts(
        self,
        subject_id: int,
    ) -> dict:
        """
        Detect conflicts in topic sequencing (e.g., topics scheduled before prerequisites).
        
        Note: This is a basic implementation. A full implementation would need
        a prerequisite mapping in the syllabus model.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            Dictionary with sequencing conflicts
        """
        # Get topics ordered by unit (assuming unit ordering represents sequence)
        topics = self.db.execute(
            select(SyllabusTopic)
            .where(SyllabusTopic.subject_id == subject_id)
            .order_by(SyllabusTopic.unit)
        ).scalars().all()

        if len(topics) < 2:
            return {
                "subject_id": subject_id,
                "conflict": False,
                "conflict_type": "topic_sequencing",
                "message": "Insufficient topics for sequencing analysis",
                "details": [],
            }

        # Get scheduled events for this subject
        events = self.db.execute(
            select(TimetableEvent)
            .where(TimetableEvent.subject_id == subject_id)
            .order_by(TimetableEvent.date, TimetableEvent.start_time)
        ).scalars().all()

        # Map events to topics (simplified - by order)
        # In a full implementation, you'd have explicit topic-to-event mapping
        conflicts = []
        
        # Check if events are scheduled in a way that respects unit order
        # This is a heuristic - assumes topics should be taught in unit order
        for i, topic in enumerate(topics):
            if topic.target_date and topic.actual_date:
                if topic.actual_date > topic.target_date:
                    conflicts.append({
                        "topic_id": topic.id,
                        "topic": topic.topic,
                        "unit": topic.unit,
                        "target_date": topic.target_date.isoformat(),
                        "actual_date": topic.actual_date.isoformat(),
                        "issue": "completed_after_deadline",
                    })

        return {
            "subject_id": subject_id,
            "conflict": len(conflicts) > 0,
            "conflict_type": "topic_sequencing",
            "details": conflicts,
        }

    def detect_batch_timetable_overload(
        self,
        batch_id: int,
        max_classes_per_week: int = 30,
    ) -> dict:
        """
        Detect if batch timetable is overloaded relative to syllabus requirements.
        
        Args:
            batch_id: ID of the batch
            max_classes_per_week: Maximum recommended classes per week
            
        Returns:
            Dictionary with overload conflicts
        """
        # Get all subjects for this batch
        subjects = self.db.execute(
            select(Subject.id)
            .join(Student, Student.batch_id == Batch.id)
            .join(Batch, Batch.id == Student.batch_id)
            .where(Batch.id == batch_id)
            .distinct()
        ).scalars().all()

        if not subjects:
            return {
                "batch_id": batch_id,
                "conflict": False,
                "conflict_type": "batch_overload",
                "message": "No subjects found for batch",
            }

        # Calculate total planned classes across all subjects
        total_planned = 0
        subject_details = []

        for subject_id in subjects:
            topics = self.db.execute(
                select(SyllabusTopic).where(SyllabusTopic.subject_id == subject_id)
            ).scalars().all()
            
            subject_planned = sum(t.planned_classes for t in topics)
            total_planned += subject_planned
            
            # Count scheduled classes for this subject/batch
            scheduled = self.db.execute(
                select(func.count(TimetableEvent.id)).where(
                    and_(
                        TimetableEvent.subject_id == subject_id,
                        TimetableEvent.batch_id == batch_id,
                    )
                )
            ).scalar() or 0

            subject_details.append({
                "subject_id": subject_id,
                "planned_classes": subject_planned,
                "scheduled_classes": scheduled,
                "deficit": subject_planned - scheduled,
            })

        # Get current weekly class count for batch
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        weekly_classes = self.db.execute(
            select(func.count(TimetableEvent.id)).where(
                and_(
                    TimetableEvent.batch_id == batch_id,
                    TimetableEvent.date >= week_start,
                    TimetableEvent.date <= week_end,
                )
            )
        ).scalar() or 0

        overload = weekly_classes > max_classes_per_week

        return {
            "batch_id": batch_id,
            "conflict": overload or any(d["deficit"] > 0 for d in subject_details),
            "conflict_type": "batch_overload",
            "max_classes_per_week": max_classes_per_week,
            "current_weekly_classes": weekly_classes,
            "overload": overload,
            "total_planned_classes": total_planned,
            "subjects": subject_details,
        }

    def detect_all_syllabus_conflicts(
        self,
        subject_id: Optional[int] = None,
        batch_id: Optional[int] = None,
    ) -> dict:
        """
        Run all syllabus conflict detectors.
        
        Args:
            subject_id: Optional filter by subject
            batch_id: Optional filter by batch
            
        Returns:
            Dictionary with all detected conflicts
        """
        all_conflicts = []
        
        # Get subjects to analyze
        if subject_id:
            subjects = [subject_id]
        else:
            if batch_id:
                subjects = self.db.execute(
                    select(Subject.id)
                    .join(Student, Student.batch_id == Batch.id)
                    .join(Batch, Batch.id == Student.batch_id)
                    .where(Batch.id == batch_id)
                    .distinct()
                ).scalars().all()
            else:
                subjects = self.db.execute(select(Subject.id)).scalars().all()

        for subj_id in subjects:
            # Insufficient capacity
            cap_result = self.detect_insufficient_capacity(subj_id, batch_id)
            if cap_result["conflict"]:
                all_conflicts.append(cap_result)

            # Deadline violations
            deadline_result = self.detect_deadline_violations(subj_id)
            if deadline_result["conflict"]:
                all_conflicts.append(deadline_result)

            # Topic sequencing
            seq_result = self.detect_topic_sequencing_conflicts(subj_id)
            if seq_result["conflict"]:
                all_conflicts.append(seq_result)

        # Batch overload
        if batch_id:
            overload_result = self.detect_batch_timetable_overload(batch_id)
            if overload_result["conflict"]:
                all_conflicts.append(overload_result)

        return {
            "subject_id": subject_id,
            "batch_id": batch_id,
            "total_conflicts": len(all_conflicts),
            "conflicts": all_conflicts,
        }


def detect_syllabus_capacity_conflict(
    total_planned: int,
    scheduled_count: int,
) -> dict:
    """Utility to detect capacity conflict."""
    deficit = total_planned - scheduled_count
    return {
        "conflict": deficit > 0,
        "total_planned": total_planned,
        "scheduled": scheduled_count,
        "deficit": max(0, deficit),
    }


def detect_deadline_risk(
    target_date: date,
    planned: int,
    completed: int,
    scheduled_before_deadline: int,
) -> dict:
    """Utility to assess deadline risk."""
    today = date.today()
    days_remaining = (target_date - today).days
    pending = max(0, planned - completed)
    
    will_meet = completed + scheduled_before_deadline >= planned
    
    if days_remaining < 0:
        risk = "overdue"
    elif not will_meet:
        risk = "high"
    elif days_remaining <= 7:
        risk = "moderate"
    else:
        risk = "low"

    return {
        "conflict": not will_meet,
        "risk_level": risk,
        "days_remaining": days_remaining,
        "shortfall": max(0, pending - scheduled_before_deadline),
    }