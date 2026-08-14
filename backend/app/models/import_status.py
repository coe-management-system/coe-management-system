"""
Import job status lifecycle.

Normal path:
    CREATED -> PROCESSING -> VALIDATED -> PREVIEW_READY -> COMMITTED

Failure paths:
    PROCESSING -> FAILED
    PREVIEW_READY -> REJECTED
    PREVIEW_READY -> CANCELLED
"""


class ImportStatus:
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    VALIDATED = "VALIDATED"
    PREVIEW_READY = "PREVIEW_READY"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

    ALL = [
        CREATED, PROCESSING, VALIDATED, PREVIEW_READY,
        COMMITTED, FAILED, REJECTED, CANCELLED,
    ]

    # Valid forward transitions — used to guard against invalid status jumps
    TRANSITIONS = {
        CREATED: [PROCESSING],
        PROCESSING: [VALIDATED, FAILED],
        VALIDATED: [PREVIEW_READY],
        PREVIEW_READY: [COMMITTED, REJECTED, CANCELLED],
        COMMITTED: [],
        FAILED: [],
        REJECTED: [],
        CANCELLED: [],
    }

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        return to_status in cls.TRANSITIONS.get(from_status, [])