"""
Development-only demo seed script.

Populates roles, users, and representative master/demo data so the
application can be showcased end-to-end. Idempotent: safe to re-run.

Demo credentials:
    admin    / admin123   (admin role, can access everything)
    faculty1 / faculty123 (faculty role)
    student1 / student123 (student role)
"""

import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import select, text

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.attendance import Attendance
from app.models.batch import Batch
from app.models.certification import Certification, CertificationAttempt
from app.models.coe import CoE
from app.models.coe_lab import CoELab
from app.models.company import Company
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.group import Group
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.syllabus import SyllabusTopic
from app.models.technology import Technology
from app.models.timetable import TimetableEvent
from app.models.training import TrainingProgram, TrainingSession
from app.models.user import User

DEPARTMENTS = [
    ("Computer Science & Engineering", "CSE"),
    ("Electronics & Communication", "ECE"),
    ("Mechanical Engineering", "MECH"),
]

FACULTY = [
    ("FAC001", "Dr. Sarah Jenkins", "sarah.jenkins@coe.local", "CSE"),
    ("FAC002", "Prof. Ramesh Kumar", "ramesh.kumar@coe.local", "CSE"),
    ("FAC003", "Dr. Anita Desai", "anita.desai@coe.local", "ECE"),
    ("FAC004", "Prof. John Mathew", "john.mathew@coe.local", "ECE"),
    ("FAC005", "Dr. Vikram Rao", "vikram.rao@coe.local", "MECH"),
    ("FAC006", "Prof. Meera Nair", "meera.nair@coe.local", "MECH"),
]

SUBJECTS = [
    ("CS101", "Data Structures", "CSE"),
    ("CS102", "Operating Systems", "CSE"),
    ("CS201", "Database Systems", "CSE"),
    ("EC101", "Digital Electronics", "ECE"),
    ("EC102", "Signals & Systems", "ECE"),
    ("EC201", "Microprocessors", "ECE"),
    ("ME101", "Engineering Mechanics", "MECH"),
    ("ME201", "Thermodynamics", "MECH"),
]

COMPANIES = [
    ("TechNova Solutions", "IT Services"),
    ("InnoSoft Labs", "Product"),
    ("CloudWorks Inc.", "Cloud Infrastructure"),
    ("GreenGrid Energy", "Manufacturing"),
]

TECHNOLOGIES = ["Python", "Java", "Machine Learning", "Embedded Systems"]

COES = [
    ("Center of Excellence - AI & Data Science", "active"),
    ("Center of Excellence - IoT & Embedded", "active"),
]

COE_LABS = [
    (1, "AI Innovation Lab", "Block A, Floor 3", 40),
    (1, "Data Science Lab", "Block A, Floor 3", 30),
    (2, "IoT Lab", "Block B, Floor 1", 25),
    (2, "Embedded Systems Lab", "Block B, Floor 1", 20),
]

CERTIFICATIONS = [
    ("Python Professional Certificate", "Python Institute"),
    ("AWS Cloud Practitioner", "Amazon Web Services"),
    ("Full-Stack Web Development", "Meta"),
]

FIRST_NAMES = ["Aarav", "Diya", "Karan", "Isha", "Rohan", "Sneha", "Aditya", "Priya",
               "Nikhil", "Ananya", "Vivek", "Kavya", "Siddharth", "Tanvi", "Arjun", "Megha"]
LAST_NAMES = ["Sharma", "Patel", "Reddy", "Iyer", "Gupta", "Singh", "Verma", "Nair",
              "Joshi", "Kulkarni", "Das", "Bose"]


def get_or_create(db, model, **kwargs):
    existing = db.scalar(select(model).where(*[getattr(model, k) == v for k, v in kwargs.items()]))
    if existing is not None:
        return existing
    instance = model(**kwargs)
    db.add(instance)
    db.flush()
    return instance


def seed_users_and_roles(db):
    admin_role = get_or_create(db, Role, name="admin")
    faculty_role = get_or_create(db, Role, name="faculty")
    student_role = get_or_create(db, Role, name="student")

    def user(username, email, password, role):
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            return existing
        u = User(username=username, email=email, password_hash=hash_password(password), role_id=role.id)
        db.add(u)
        db.flush()
        return u

    user("admin", "admin@coe.local", "admin123", admin_role)
    user("faculty1", "faculty1@coe.local", "faculty123", faculty_role)
    user("student1", "student1@coe.local", "student123", student_role)


def seed_master_data(db):
    dept_map = {}
    for name, code in DEPARTMENTS:
        dept = get_or_create(db, Department, name=name, code=code)
        dept_map[code] = dept

    batch_map = {}
    group_map = {}
    for dept_code, dept in dept_map.items():
        for year in (2023, 2024, 2025):
            batch = get_or_create(db, Batch, name=f"{dept.name} Batch {year}", year=year, department_id=dept.id)
            batch_map[(dept_code, year)] = batch
            for group_name in ("A", "B"):
                grp = get_or_create(db, Group, name=f"{dept_code}-{year}-{group_name}", batch_id=batch.id)
                group_map[(dept_code, year, group_name)] = grp

    faculty_map = {}
    for code, name, email, dept_code in FACULTY:
        fac = get_or_create(db, Faculty, employee_code=code, name=name, email=email,
                            department_id=dept_map[dept_code].id)
        faculty_map[dept_code] = fac

    subject_map = {}
    for code, name, dept_code in SUBJECTS:
        subj = get_or_create(db, Subject, code=code, name=name, department_id=dept_map[dept_code].id)
        subject_map[code] = subj

    random.seed(42)
    student_names = set()
    for dept_code, dept in dept_map.items():
        for year in (2023, 2024, 2025):
            for group_name in ("A", "B"):
                batch = batch_map[(dept_code, year)]
                group = group_map[(dept_code, year, group_name)]
                for i in range(4):
                    first = random.choice(FIRST_NAMES)
                    last = random.choice(LAST_NAMES)
                    full = f"{first} {last}"
                    while full in student_names:
                        first = random.choice(FIRST_NAMES)
                        last = random.choice(LAST_NAMES)
                        full = f"{first} {last}"
                    student_names.add(full)
                    roll = f"{dept_code}{year % 100}{group_name}{i + 1:02d}"
                    email = f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@student.example.com"
                    get_or_create(
                        db, Student,
                        roll_no=roll, name=full, email=email,
                        department_id=dept.id, batch_id=batch.id, group_id=group.id,
                    )

    return dept_map, batch_map, group_map, faculty_map, subject_map


def seed_demo_data(db, dept_map, batch_map, group_map, faculty_map, subject_map):
    today = date.today()

    # Timetable events across this week; intentionally include one faculty overlap
    # (same faculty, overlapping slots) so conflict detection has something to show.
    day = today - timedelta(days=today.weekday())
    slots = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]
    event_seed = [
        ("CS101", "CSE", "CSE", 2024, "A", 1, 0, 2),
        ("CS102", "CSE", "CSE", 2024, "B", 2, 1, 2),
        ("CS201", "CSE", "CSE", 2025, "A", 3, 2, 3),
        ("EC101", "ECE", "ECE", 2023, "A", 1, 3, 2),
        ("EC102", "ECE", "ECE", 2024, "A", 2, 4, 3),
        ("EC201", "ECE", "ECE", 2025, "B", 3, 5, 3),
        ("ME101", "MECH", "MECH", 2023, "A", 1, 6, 2),
        ("ME201", "MECH", "MECH", 2024, "B", 2, 7, 3),
    ]
    room_pool = ["101", "102", "103", "201", "202", "301"]
    for i, (subj_code, fac_dept, stu_dept, year, group_name, slot_idx, slot_fac, priority) in enumerate(event_seed):
        batch = batch_map[(stu_dept, year)]
        group = group_map[(stu_dept, year, group_name)]
        faculty = faculty_map[f"{fac_dept}"]
        start, end = slots[slot_idx]
        event_day = day + timedelta(days=i % 5)
        existing = db.scalar(
            select(TimetableEvent).where(
                TimetableEvent.subject_id == subject_map[subj_code].id,
                TimetableEvent.batch_id == batch.id,
                TimetableEvent.event_date == event_day,
            )
        )
        if existing is None:
            db.add(TimetableEvent(
                subject_id=subject_map[subj_code].id,
                faculty_id=faculty.id,
                batch_id=batch.id,
                room_id=room_pool[i % len(room_pool)],
                event_date=event_day,
                start_time=start,
                end_time=end,
                priority=priority,
            ))
    # Add an overlapping event: faculty FAC001 teaches CS101 at 09:00 and also
    # a session for CS201 at 09:30 on the same day (intentional conflict).
    fac1 = faculty_map["CSE"]
    overlapping = db.scalar(
        select(TimetableEvent).where(TimetableEvent.room_id == "CONFLICT-1")
    )
    if overlapping is None:
        db.add(TimetableEvent(
            subject_id=subject_map["CS201"].id,
            faculty_id=fac1.id,
            batch_id=batch_map[("CSE", 2025)].id,
            room_id="CONFLICT-1",
            event_date=day,
            start_time=time(9, 30),
            end_time=time(10, 30),
            priority=3,
        ))

    # Attendance records for students over the past ~8 weeks
    students = db.scalars(select(Student).limit(40)).all()
    subjects = list(subject_map.values())
    attendance_days = [day - timedelta(days=7 * w + d) for w in range(8) for d in range(5)]
    for student in students[:30]:
        for subj in subjects[:4]:
            for session_date in attendance_days:
                status = "present" if random.random() > 0.2 else "absent"
                exists = db.scalar(
                    select(Attendance).where(
                        Attendance.student_id == student.id,
                        Attendance.subject_id == subj.id,
                        Attendance.session_date == session_date,
                    )
                )
                if exists is None:
                    db.add(Attendance(student_id=student.id, subject_id=subj.id,
                                      session_date=session_date, status=status))

    # Syllabus topics
    for subj in subjects:
        for unit_idx in range(1, 4):
            topic = db.scalar(
                select(SyllabusTopic).where(
                    SyllabusTopic.subject_id == subj.id,
                    SyllabusTopic.unit == f"Unit {unit_idx}",
                )
            )
            if topic is None:
                planned = random.randint(8, 14)
                completed = random.randint(0, planned)
                db.add(SyllabusTopic(
                    subject_id=subj.id,
                    unit=f"Unit {unit_idx}",
                    topic=f"{subj.name} - Unit {unit_idx} topics",
                    planned_classes=planned,
                    completed_classes=completed,
                    target_date=today + timedelta(days=random.randint(-5, 30)),
                ))

    # CoE / Labs / Companies / Technologies
    coe_map = {}
    for name, status in COES:
        coe = get_or_create(db, CoE, name=name, status=status)
        coe_map[name] = coe
    for coe_id, name, location, capacity in COE_LABS:
        get_or_create(db, CoELab, coe_id=coe_map[COES[coe_id - 1][0]].id, name=name,
                      location=location, capacity=capacity)

    company_map = {}
    for name, ctype in COMPANIES:
        comp = get_or_create(db, Company, name=name, type=ctype)
        company_map[name] = comp

    tech_map = {}
    for name in TECHNOLOGIES:
        tech = get_or_create(db, Technology, name=name)
        tech_map[name] = tech

    # Training programs + sessions
    for idx, (prog_name, coe_name, company_name, tech_name, hours) in enumerate([
        ("AI & Data Science Bootcamp", COES[0][0], COMPANIES[0][0], TECHNOLOGIES[2], 40.0),
        ("IoT for Industry", COES[1][0], COMPANIES[3][0], TECHNOLOGIES[3], 30.0),
    ]):
        program = db.scalar(select(TrainingProgram).where(TrainingProgram.name == prog_name))
        if program is None:
            program = TrainingProgram(
                name=prog_name,
                description=f"Hands-on {prog_name} program.",
                coe_id=coe_map[coe_name].id,
                company_id=company_map[company_name].id,
                technology_id=tech_map[tech_name].id,
                start_date=today - timedelta(days=20),
                end_date=today + timedelta(days=40),
                planned_hours=hours,
            )
            db.add(program)
            db.flush()
        if db.scalar(select(TrainingSession).where(TrainingSession.program_id == program.id)) is None:
            db.add(TrainingSession(
                program_id=program.id,
                batch_id=batch_map[("CSE", 2024)].id,
                group_id=group_map[("CSE", 2024, "A")].id,
                title=f"{prog_name} - Session",
                faculty_id=faculty_map["CSE"].id,
                start_at=datetime.combine(day, time(9, 0)),
                end_at=datetime.combine(day, time(17, 0)),
                hours=8.0,
            ))

    # Certifications
    cert_map = {}
    for name, org in CERTIFICATIONS:
        cert = get_or_create(db, Certification, name=name, issuing_organization=org)
        cert_map[name] = cert
    for student in students[:20]:
        for cert in list(cert_map.values())[:2]:
            exists = db.scalar(
                select(CertificationAttempt).where(
                    CertificationAttempt.student_id == student.id,
                    CertificationAttempt.certification_id == cert.id,
                )
            )
            if exists is None:
                status = random.choice(["completed", "in_progress", "pending"])
                score = random.randint(55, 98) if status == "completed" else None
                db.add(CertificationAttempt(
                    student_id=student.id,
                    certification_id=cert.id,
                    status=status,
                    score=score,
                ))


def reset_demo_tables(db):
    tables = [
        "certification_attempts",
        "training_sessions",
        "training_programs",
        "timetable_events",
        "attendance",
        "syllabus_topics",
        "certifications",
        "coe_labs",
        "students",
        "groups",
        "batches",
        "subjects",
        "faculty",
        "departments",
        "companies",
        "technologies",
        "coes",
        "users",
        "roles",
    ]
    for table in tables:
        db.execute(text(f"DELETE FROM {table}"))


def main():
    db = SessionLocal()
    try:
        reset_demo_tables(db)
        seed_users_and_roles(db)
        dept_map, batch_map, group_map, faculty_map, subject_map = seed_master_data(db)
        seed_demo_data(db, dept_map, batch_map, group_map, faculty_map, subject_map)
        db.commit()
        print("Demo seed completed successfully.")
        print("Users: admin/admin123, faculty1/faculty123, student1/student123")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
