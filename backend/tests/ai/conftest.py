import pytest
from datetime import date
from app.core.database import engine, Base, SessionLocal
import app.models  # Import all SQLAlchemy models to register with Base.metadata
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.training import TrainingSession, TrainingProgram

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates all database tables in the test database engine."""
    Base.metadata.create_all(bind=engine)
    
    # Seed initial test data into SQLite/PostgreSQL test instance
    with SessionLocal() as db:
        if not db.query(Student).filter_by(roll_no="CSE101").first():
            s1 = Student(id=1, roll_no="CSE101", name="Rahul", email="rahul@example.com", department_id=1, batch_id=1, group_id=1)
            s2 = Student(id=2, roll_no="CSE102", name="Aman", email="aman@example.com", department_id=1, batch_id=1, group_id=1)
            db.add_all([s1, s2])
            db.commit()

            # Seed attendance records for CSE101 (68% attendance)
            # 10 sessions total: 6 PRESENT, 4 ABSENT -> 60%
            att_records = [
                Attendance(student_id=1, subject_id=101, session_date=date(2026, 8, i + 1), status="PRESENT" if i < 6 else "ABSENT")
                for i in range(10)
            ]
            db.add_all(att_records)
            db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
