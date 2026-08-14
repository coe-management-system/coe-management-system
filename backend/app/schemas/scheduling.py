from datetime import date
from typing import Literal

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