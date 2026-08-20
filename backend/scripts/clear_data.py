"""
Script to clear all operational / imported data from the database
while preserving system roles and the admin / test user accounts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User

def clear_all_data():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version'"))
        tables = [r[0] for r in res.fetchall()]
        print(f"Found {len(tables)} tables: {tables}")
        
        # Tables to preserve
        preserved_tables = {"roles", "users", "alembic_version"}
        tables_to_truncate = [t for t in tables if t not in preserved_tables]
        
        if tables_to_truncate:
            truncate_sql = f"TRUNCATE TABLE {', '.join(tables_to_truncate)} RESTART IDENTITY CASCADE"
            print(f"Executing: {truncate_sql}")
            conn.execute(text(truncate_sql))
            conn.commit()
            print("Successfully truncated operational tables.")
            
    # Verify/ensure admin & faculty & student roles and users exist
    with SessionLocal() as db:
        role_map = {}
        for r_name in ["admin", "faculty", "student"]:
            r = db.query(Role).filter_by(name=r_name).first()
            if not r:
                r = Role(name=r_name)
                db.add(r)
                db.flush()
            role_map[r_name] = r.id
            
        # Admin user
        admin_user = db.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@coe.local",
                password_hash=hash_password("admin123"),
                role_id=role_map["admin"]
            )
            db.add(admin_user)
        else:
            admin_user.password_hash = hash_password("admin123")
            admin_user.role_id = role_map["admin"]
            
        # Faculty user
        faculty_user = db.query(User).filter_by(username="faculty").first()
        if not faculty_user:
            faculty_user = User(
                username="faculty",
                email="faculty@coe.local",
                password_hash=hash_password("faculty123"),
                role_id=role_map["faculty"]
            )
            db.add(faculty_user)
            
        # Student user
        student_user = db.query(User).filter_by(username="student").first()
        if not student_user:
            student_user = User(
                username="student",
                email="student@coe.local",
                password_hash=hash_password("student123"),
                role_id=role_map["student"]
            )
            db.add(student_user)
            
        db.commit()
        print("Ensured admin (admin/admin123), faculty (faculty/faculty123), and student (student/student123) exist.")

    # Show count of records in all tables
    with engine.connect() as conn:
        print("\nCurrent Table Row Counts:")
        for t in sorted(tables):
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  - {t}: {count} rows")

if __name__ == "__main__":
    clear_all_data()
