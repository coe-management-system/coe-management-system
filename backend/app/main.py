from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.students import router as students_router
from app.api.routes.departments import router as departments_router
from app.api.routes.batches import router as batches_router
from app.api.routes.groups import router as groups_router
from app.api.routes.faculty import router as faculty_router
from app.api.routes.auth import router as auth_router
from app.api.routes.imports import router as imports_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.syllabus import router as syllabus_router

app = FastAPI(
    title="COE Management System",
    version="1.0.0",
)


app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    students_router,
    prefix="/api/v1",
)

app.include_router(
    departments_router,
    prefix="/api/v1",
)

app.include_router(
    batches_router,
    prefix="/api/v1",
)

app.include_router(
    groups_router,
    prefix="/api/v1",
)

app.include_router(
    faculty_router,
    prefix="/api/v1",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    imports_router,
    prefix="/api/v1",
)

app.include_router(
    attendance_router,
    prefix="/api/v1",
)

app.include_router(
    syllabus_router,
    prefix="/api/v1",
)