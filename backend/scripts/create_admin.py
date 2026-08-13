"""
Development-only script for provisioning the initial admin user.

This script must not be used as a production user-management mechanism.
"""

import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


USERNAME = "admin"
EMAIL = "admin@coe.local"
ROLE_NAME = "admin"


def create_admin() -> None:
    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required."
        )

    db = SessionLocal()

    try:
        role = db.scalar(
            select(Role).where(Role.name == ROLE_NAME)
        )

        if role is None:
            role = Role(name=ROLE_NAME)
            db.add(role)
            db.flush()

        existing_user = db.scalar(
            select(User).where(User.username == USERNAME)
        )

        if existing_user is not None:
            print(f"User '{USERNAME}' already exists.")
            return

        user = User(
            username=USERNAME,
            email=EMAIL,
            password_hash=hash_password(password),
            role_id=role.id,
        )

        db.add(user)
        db.commit()

        print(f"Created role: {ROLE_NAME}")
        print(f"Created user: {USERNAME}")
        print(f"Email: {EMAIL}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()