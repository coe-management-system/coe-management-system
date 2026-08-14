from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.syllabus import SyllabusTopic
from app.models.user import User
from app.schemas.syllabus import (
    SyllabusTopicCreate,
    SyllabusTopicResponse,
    SyllabusTopicUpdate,
)
from app.services.syllabus_service import SyllabusService


router = APIRouter(
    prefix="/syllabus",
    tags=["Syllabus"],
)

faculty_required = require_role("faculty")


def _response(topic: SyllabusTopic) -> dict:
    return SyllabusService.build_response_data(topic)


@router.post(
    "",
    response_model=SyllabusTopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_syllabus_topic(
    topic_data: SyllabusTopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SyllabusService(db)

    try:
        topic = service.create_topic(
            subject_id=topic_data.subject_id,
            unit=topic_data.unit,
            topic=topic_data.topic,
            planned_classes=topic_data.planned_classes,
            completed_classes=topic_data.completed_classes,
            target_date=topic_data.target_date,
            actual_date=topic_data.actual_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return _response(topic)


@router.get(
    "",
    response_model=list[SyllabusTopicResponse],
)
def get_syllabus_topics(
    subject_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SyllabusService(db)

    topics = service.get_topics(
        subject_id=subject_id,
    )

    return [
        _response(topic)
        for topic in topics
    ]


@router.get(
    "/{topic_id}",
    response_model=SyllabusTopicResponse,
)
def get_syllabus_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SyllabusService(db)

    topic = service.get_topic(topic_id)

    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus topic not found",
        )

    return _response(topic)


@router.patch(
    "/{topic_id}",
    response_model=SyllabusTopicResponse,
)
def update_syllabus_topic(
    topic_id: int,
    topic_data: SyllabusTopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SyllabusService(db)

    topic = service.get_topic(topic_id)

    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus topic not found",
        )

    try:
        topic = service.update_topic(
            topic=topic,
            unit=topic_data.unit,
            topic_name=topic_data.topic,
            planned_classes=topic_data.planned_classes,
            completed_classes=topic_data.completed_classes,
            target_date=topic_data.target_date,
            actual_date=topic_data.actual_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return _response(topic)
