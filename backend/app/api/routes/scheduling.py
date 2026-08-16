from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.scheduling import (
    AttendanceAnalyticsRequest,
    CandidateRequest,
    OptimizeRequest,
    RecommendationRequest,
    RescheduleRequest,
    SyllabusAnalyticsRequest,
    SyllabusConflictRequest,
    VersionActionRequest,
    VersionChangesRequest,
    VersionCompareRequest,
    VersionCreateRequest,
    WhatIfRequest,
)
from app.scheduling.optimizer import OptimizationConfig
from app.scheduling.service import SchedulingService
from app.scheduling.attendance import AttendanceAnalytics
from app.scheduling.syllabus import SyllabusAnalytics
from app.scheduling.syllabus_conflicts import SyllabusConflictDetector
from app.scheduling.version_manager import TimetableVersionManager
from app.scheduling.candidate_generator import generate_slots, evaluate_candidates, generate_candidates
from app.scheduling.recommendation import recommend_reschedule

router = APIRouter(
    prefix="/scheduling",
    tags=["Scheduling"],
)

faculty_required = require_role("faculty")


@router.get("/conflicts")
def get_scheduling_conflicts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return structured, explainable scheduling conflicts.

    Read-only business operation.
    """
    service = SchedulingService.from_db(db)

    return service.analyze_conflicts_structured()


# =============================================================================
# Analytics Endpoints (M3-01, M3-02)
# =============================================================================

@router.get("/analytics/attendance")
def get_attendance_analytics(
    request: AttendanceAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get attendance analytics including percentages, trends, and warning/critical cases.
    
    Supports filtering by student, batch, subject, and date range.
    """
    analytics = AttendanceAnalytics(db)
    
    if request.student_id:
        return analytics.get_student_attendance_percentage(
            request.student_id,
            request.subject_id,
            request.start_date,
            request.end_date,
        )
    elif request.batch_id:
        return analytics.get_batch_attendance_summary(
            request.batch_id,
            request.subject_id,
            request.start_date,
            request.end_date,
        )
    else:
        # Return trends by default
        return analytics.get_attendance_trends(
            student_id=request.student_id,
            batch_id=request.batch_id,
            subject_id=request.subject_id,
        )


@router.get("/analytics/attendance/warning-cases")
def get_attendance_warning_cases(
    request: AttendanceAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get students in warning or critical attendance categories.
    """
    analytics = AttendanceAnalytics(db)
    return analytics.get_warning_critical_cases(
        request.batch_id,
        request.subject_id,
        request.start_date,
        request.end_date,
    )


@router.get("/analytics/syllabus")
def get_syllabus_analytics(
    request: SyllabusAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get syllabus analytics including progress, pending classes, and deadline risk.
    """
    analytics = SyllabusAnalytics(db)
    
    progress = analytics.get_syllabus_progress(request.subject_id, request.batch_id)
    risk = analytics.get_deadline_risk(request.subject_id, request.days_ahead)
    
    return {
        "progress": progress,
        "deadline_risk": risk,
    }


@router.get("/analytics/syllabus/batch/{batch_id}")
def get_batch_syllabus_status(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get syllabus status for all subjects in a batch.
    """
    analytics = SyllabusAnalytics(db)
    return analytics.get_batch_syllabus_status(batch_id)


@router.get("/analytics/syllabus/pending")
def get_pending_classes(
    request: SyllabusAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary of pending syllabus classes.
    """
    analytics = SyllabusAnalytics(db)
    return analytics.get_pending_classes_summary(request.subject_id, request.batch_id)


# =============================================================================
# Syllabus Conflicts (M3-04)
# =============================================================================

@router.get("/conflicts/syllabus")
def get_syllabus_conflicts(
    request: SyllabusConflictRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect all syllabus-related conflicts.
    """
    detector = SyllabusConflictDetector(db)
    return detector.detect_all_syllabus_conflicts(
        request.subject_id,
        request.batch_id,
    )


# =============================================================================
# Faculty Workload (M3-03)
# =============================================================================

@router.get("/faculty/{faculty_id}/workload")
def get_faculty_workload(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed workload report for a faculty member.
    """
    service = SchedulingService.from_db(db)

    return service.get_faculty_workload(faculty_id)


# =============================================================================
# Timetable Endpoints
# =============================================================================

@router.get("/timetable")
def get_timetable(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current official timetable.
    """
    service = SchedulingService.from_db(db)
    return service.get_timetable()


@router.get("/timetable/conflicts")
def get_timetable_conflicts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all conflicts in the current timetable.
    """
    service = SchedulingService.from_db(db)
    return service.analyze_conflicts_structured()


# =============================================================================
# Candidate Generation (M3-06)
# =============================================================================

@router.post("/candidates")
def post_candidates(
    payload: CandidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Generate feasible candidate slots for an event.
    """
    service = SchedulingService.from_db(db)
    events = [e.to_dict() for e in service.events]

    event = next((e for e in events if e["id"] == payload.event_id), None)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {payload.event_id} not found",
        )

    dates = None
    if payload.date_range:
        start = payload.date_range.get("start")
        end = payload.date_range.get("end")
        if start and end:
            from datetime import date, timedelta
            s = date.fromisoformat(start)
            e = date.fromisoformat(end)
            dates = []
            d = s
            while d <= e:
                dates.append(d)
                d += timedelta(days=1)

    evaluations = generate_candidates(
        events=events,
        event=event,
        dates=dates,
        capacities=payload.capacities,
        hard_capacities=payload.hard_capacities,
    )

    return {
        "event_id": payload.event_id,
        "evaluations": evaluations,
        "feasible_count": sum(1 for e in evaluations if e["status"] == "FEASIBLE"),
    }


# =============================================================================
# Reschedule Recommendation (M3-09)
# =============================================================================

@router.post("/reschedule-recommendation")
def post_reschedule_recommendation(
    payload: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Generate a rescheduling recommendation for a conflicting event.

    The recommendation never modifies the official timetable.
    """
    service = SchedulingService.from_db(db)

    try:
        recommendation = service.recommend_reschedule(
            payload.event_id,
            candidates=[c.model_dump() for c in payload.candidates]
            if payload.candidates
            else None,
            preferred_time=payload.preferred_time,
            capacities=payload.capacities,
            hard_capacities=payload.hard_capacities,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return recommendation


@router.post("/recommendations")
def post_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Generate ranked rescheduling recommendations for an event.
    """
    service = SchedulingService.from_db(db)
    events = [e.to_dict() for e in service.events]
    
    recommendation = recommend_reschedule(
        events,
        payload.event_id,
        capacities=payload.capacities,
        hard_capacities=payload.hard_capacities,
    )
    
    return recommendation


# =============================================================================
# What-If Simulation (M3-10)
# =============================================================================

@router.post("/what-if")
def post_what_if(
    payload: WhatIfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Evaluate a what-if scenario against a copy of the timetable.

    The official timetable is never modified.
    """
    service = SchedulingService.from_db(db)

    scenario = {
        "type": payload.type,
        "resource": payload.resource,
        "date": payload.date,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "event_id": payload.event_id,
        "changes": payload.changes,
    }

    return service.run_what_if(
        scenario,
        capacities=payload.capacities,
        hard_capacities=payload.hard_capacities,
    )


# =============================================================================
# Optimization (M3-07, M3-08)
# =============================================================================

@router.post("/optimize")
def post_optimize(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Optimize the official timetable on an isolated scenario.

    Produces a proposed schedule only. It never modifies or publishes
    the official timetable. The response contains the optimization
    status, the proposed schedule, the before/after comparison, and the
    objective breakdown.
    """
    service = SchedulingService.from_db(db)

    config = OptimizationConfig(
        dates=payload.dates,
        day_start=payload.day_start,
        day_end=payload.day_end,
        slot_minutes=payload.slot_minutes,
        mode=payload.mode,
        max_moves=payload.max_moves,
    )

    return service.optimize(
        capacities=payload.capacities,
        hard_capacities=payload.hard_capacities,
        config=config,
    )


# =============================================================================
# Timetable Versioning (M3-11)
# =============================================================================

@router.get("/versions")
def list_versions(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all timetable versions.
    """
    manager = TimetableVersionManager(db)
    
    version_status = None
    if status:
        try:
            from app.models.timetable_version import VersionStatus
            version_status = VersionStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )
    
    versions = manager.list_versions(status=version_status, limit=limit, offset=offset)
    
    return {
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "name": v.name,
                "description": v.description,
                "status": v.status.value,
                "events_added": v.events_added,
                "events_modified": v.events_modified,
                "events_removed": v.events_removed,
                "created_by": v.created_by,
                "approved_by": v.approved_by,
                "approved_at": v.approved_at.isoformat() if v.approved_at else None,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
        "total": len(versions),
        "limit": limit,
        "offset": offset,
    }


@router.get("/versions/latest")
def get_latest_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent version."""
    manager = TimetableVersionManager(db)
    version = manager.get_latest_version()
    
    if not version:
        raise HTTPException(status_code=404, detail="No versions found")
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "description": version.description,
        "status": version.status.value,
        "events_added": version.events_added,
        "events_modified": version.events_modified,
        "events_removed": version.events_removed,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat(),
    }


@router.get("/versions/published")
def get_published_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the currently published version."""
    manager = TimetableVersionManager(db)
    version = manager.get_published_version()
    
    if not version:
        raise HTTPException(status_code=404, detail="No published version")
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "description": version.description,
        "status": version.status.value,
        "created_at": version.created_at.isoformat(),
        "approved_at": version.approved_at.isoformat() if version.approved_at else None,
    }


@router.get("/versions/{version_id}")
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific version by ID."""
    manager = TimetableVersionManager(db)
    version = manager.get_version(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    events = manager.get_version_events(version_id)
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "description": version.description,
        "status": version.status.value,
        "events_added": version.events_added,
        "events_modified": version.events_modified,
        "events_removed": version.events_removed,
        "snapshot": events,
        "changes_summary": version.changes_summary,
        "created_by": version.created_by,
        "approved_by": version.approved_by,
        "approved_at": version.approved_at.isoformat() if version.approved_at else None,
        "created_at": version.created_at.isoformat(),
    }


@router.post("/versions")
def create_version(
    payload: VersionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Create a new version from the current timetable."""
    manager = TimetableVersionManager(db)
    service = SchedulingService.from_db(db)
    
    events = service.events
    
    from app.models.timetable_version import VersionStatus
    
    version = manager.create_version(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
        status=VersionStatus(payload.status),
        events=events,
    )
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "status": version.status.value,
        "created_at": version.created_at.isoformat(),
    }


@router.post("/versions/changes")
def create_version_from_changes(
    payload: VersionChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Create a version from specific changes (added/modified/removed events)."""
    manager = TimetableVersionManager(db)
    service = SchedulingService.from_db(db)
    events = [e.to_dict() for e in service.events]
    
    # Convert payload events to TimetableEvent objects
    from app.models.timetable import TimetableEvent
    from datetime import datetime
    
    def dict_to_event(d):
        return TimetableEvent(
            id=d.get("id", 0),
            subject_id=d["subject_id"],
            faculty_id=d["faculty_id"],
            batch_id=d["batch_id"],
            room_id=d.get("room_id"),
            event_date=datetime.fromisoformat(d["event_date"]).date() if d.get("event_date") else None,
            start_time=datetime.strptime(d["start_time"], "%H:%M:%S").time() if d.get("start_time") else None,
            end_time=datetime.strptime(d["end_time"], "%H:%M:%S").time() if d.get("end_time") else None,
            priority=d.get("priority", 1),
        )
    
    added = [dict_to_event(e) for e in payload.added_events]
    modified = [(dict_to_event(m["old"]), dict_to_event(m["new"])) for m in payload.modified_events]
    removed = payload.removed_event_ids
    
    from app.models.timetable_version import VersionStatus
    
    version = manager.create_version_from_changes(
        name=payload.name,
        description=payload.description,
        added_events=added,
        modified_events=modified,
        removed_event_ids=removed,
        created_by=current_user.id,
        status=VersionStatus.PROPOSED,
    )
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "status": version.status.value,
        "events_added": version.events_added,
        "events_modified": version.events_modified,
        "events_removed": version.events_removed,
        "created_at": version.created_at.isoformat(),
    }


@router.post("/versions/{version_id}/approve")
def approve_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Approve a version (move from draft/proposed to approved)."""
    manager = TimetableVersionManager(db)
    
    try:
        version = manager.approve_version(version_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": version.id,
        "status": version.status.value,
        "approved_by": version.approved_by,
        "approved_at": version.approved_at.isoformat() if version.approved_at else None,
    }


@router.post("/versions/{version_id}/publish")
def publish_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Publish a version (make it the official timetable)."""
    manager = TimetableVersionManager(db)
    
    try:
        version = manager.publish_version(version_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": version.id,
        "status": version.status.value,
        "published_by": version.approved_by,
        "published_at": version.approved_at.isoformat() if version.approved_at else None,
    }


@router.post("/versions/{version_id}/rollback")
def rollback_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Create a new version that rolls back to a previous version."""
    manager = TimetableVersionManager(db)
    
    try:
        version = manager.rollback_to_version(version_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "name": version.name,
        "status": version.status.value,
        "created_at": version.created_at.isoformat(),
    }


@router.post("/versions/{version_id}/apply")
def apply_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Apply a version's events to the official timetable (only for published versions)."""
    manager = TimetableVersionManager(db)
    
    try:
        result = manager.apply_version_to_timetable(version_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.post("/versions/compare")
def compare_versions(
    payload: VersionCompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two timetable versions."""
    manager = TimetableVersionManager(db)
    
    try:
        comparison = manager.compare_versions(payload.version_a_id, payload.version_b_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return comparison


@router.delete("/versions/{version_id}")
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Delete a version (only draft or rejected)."""
    manager = TimetableVersionManager(db)
    
    try:
        deleted = manager.delete_version(version_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {"deleted": True, "version_id": version_id}


# =============================================================================
# R&D Evaluation (M3-12)
# =============================================================================

@router.post("/rnd/evaluate")
def run_rnd_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """Run comprehensive R&D evaluation comparing all three approaches."""
    from app.scheduling.benchmark import run_rnd_evaluation
    
    service = SchedulingService.from_db(db)
    events = [e.to_dict() for e in service.events]
    capacities = {}  # TODO: Get from config
    
    # For now, use a default scenario
    from app.scheduling.benchmark import build_optimization_scenario
    scenario = build_optimization_scenario()
    
    result = run_rnd_evaluation(scenario)
    return result
