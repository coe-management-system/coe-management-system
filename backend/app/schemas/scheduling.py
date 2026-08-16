from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class ConflictViolation(BaseModel):
    constraint_type: str
    severity: str
    event_id: int
    conflicting_event_id: int | None = None
    resource: int | str | None = None
    message: str


class CandidateSlot(BaseModel):
    date: date | str
    start_time: str
    end_time: str


class RescheduleRequest(BaseModel):
    event_id: int
    candidates: list[CandidateSlot] | None = None
    preferred_time: str | None = None
    capacities: dict[int, float] | None = None
    hard_capacities: dict[int, float] | None = None


class WhatIfRequest(BaseModel):
    type: Literal[
        "room_unavailable",
        "faculty_unavailable",
        "batch_unavailable",
        "event_change",
    ]
    resource: int | str | None = None
    date: date | str | None = None
    start_time: str | None = None
    end_time: str | None = None
    event_id: int | None = None
    changes: dict | None = None
    capacities: dict[int, float] | None = None
    hard_capacities: dict[int, float] | None = None


class OptimizeRequest(BaseModel):
    mode: Literal[
        "BALANCED",
        "CONFLICT_MINIMIZATION",
        "WORKLOAD_BALANCING",
    ] = "BALANCED"
    dates: list[date | str] | None = None
    day_start: str = "08:00"
    day_end: str = "18:00"
    slot_minutes: int = 60
    max_moves: int = 50
    capacities: dict[int, float] | None = None
    hard_capacities: dict[int, float] | None = None


# =============================================================================
# Analytics Schemas
# =============================================================================

class AttendanceAnalyticsRequest(BaseModel):
    student_id: Optional[int] = None
    batch_id: Optional[int] = None
    subject_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SyllabusAnalyticsRequest(BaseModel):
    subject_id: int
    batch_id: Optional[int] = None
    days_ahead: int = 14


class SyllabusConflictRequest(BaseModel):
    subject_id: Optional[int] = None
    batch_id: Optional[int] = None


# =============================================================================
# Versioning Schemas
# =============================================================================

class VersionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    status: Literal["draft", "proposed"] = "draft"


class VersionChangesRequest(BaseModel):
    name: str
    description: str
    added_events: List[Dict[str, Any]] = []
    modified_events: List[Dict[str, Any]] = []  # [{"old": {...}, "new": {...}}]
    removed_event_ids: List[int] = []


class VersionCompareRequest(BaseModel):
    version_a_id: int
    version_b_id: int


class VersionActionRequest(BaseModel):
    version_id: int
    user_id: int


# =============================================================================
# Candidate/Recommendation Schemas
# =============================================================================

class CandidateRequest(BaseModel):
    event_id: int
    capacities: Optional[Dict[int, float]] = None
    hard_capacities: Optional[Dict[int, float]] = None
    date_range: Optional[Dict[str, str]] = None


class RecommendationRequest(BaseModel):
    event_id: int
    preferred_time: Optional[str] = None
    capacities: Optional[Dict[int, float]] = None
    hard_capacities: Optional[Dict[int, float]] = None
