from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.scheduling import (
    OptimizeRequest,
    RescheduleRequest,
    WhatIfRequest,
)
from app.scheduling.optimizer import OptimizationConfig
from app.scheduling.service import SchedulingService


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