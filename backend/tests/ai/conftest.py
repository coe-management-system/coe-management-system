import pytest
from datetime import date
from app.core.database import engine, Base, SessionLocal
import app.models  # Import all SQLAlchemy models to register with Base.metadata
from app.models.department import Department
from app.models.batch import Batch
from app.models.group import Group
from app.models.subject import Subject
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.training import TrainingSession, TrainingProgram

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates all database tables in the test database engine and seeds test dependencies."""
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        # Ensure department exists
        dept = db.query(Department).first()
        if not dept:
            dept = Department(name="Computer Science Test", code="CSE_TEST")
            db.add(dept)
            db.commit()
            db.refresh(dept)
            
        # Ensure batch exists
        batch = db.query(Batch).filter_by(department_id=dept.id).first()
        if not batch:
            batch = Batch(name="Batch 2026 Test", year=2026, department_id=dept.id)
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
        # Ensure group exists
        group = db.query(Group).filter_by(batch_id=batch.id).first()
        if not group:
            group = Group(name="Group A Test", batch_id=batch.id)
            db.add(group)
            db.commit()
            db.refresh(group)

        # Ensure subject exists
        subject = db.query(Subject).filter_by(department_id=dept.id).first()
        if not subject:
            subject = Subject(name="Data Structures Test", code="CS_TEST_101", department_id=dept.id)
            db.add(subject)
            db.commit()
            db.refresh(subject)

        student1 = db.query(Student).filter_by(roll_no="CSE101").first()
        if not student1:
            student1 = Student(roll_no="CSE101", name="Rahul", email="rahul_test_ai@example.com", department_id=dept.id, batch_id=batch.id, group_id=group.id)
            db.add(student1)
            db.commit()
            db.refresh(student1)

        student2 = db.query(Student).filter_by(roll_no="CSE102").first()
        if not student2:
            student2 = Student(roll_no="CSE102", name="Aman", email="aman_test_ai@example.com", department_id=dept.id, batch_id=batch.id, group_id=group.id)
            db.add(student2)
            db.commit()
            db.refresh(student2)

        # Seed attendance records for student1 (60% attendance)
        att_count = db.query(Attendance).filter_by(student_id=student1.id, subject_id=subject.id).count()
        if att_count == 0:
            att_records = [
                Attendance(student_id=student1.id, subject_id=subject.id, session_date=date(2026, 8, i + 1), status="PRESENT" if i < 6 else "ABSENT")
                for i in range(10)
            ]
            db.add_all(att_records)
            db.commit()
    yield
