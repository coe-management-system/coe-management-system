"""
Development-only script for provisioning application roles.

This script must not be used as a production user-management mechanism.
"""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.role import Role


ROLE_NAMES = (
    "faculty",
    "student",
)


def seed_roles() -> None:
    db = SessionLocal()

    try:
        for role_name in ROLE_NAMES:
            role = db.scalar(
                select(Role).where(Role.name == role_name)
            )

            if role is None:
                db.add(Role(name=role_name))
                print(f"Created role: {role_name}")
            else:
                print(f"Role '{role_name}' already exists.")

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()