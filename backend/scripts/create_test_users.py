"""
Development-only script for provisioning RBAC test users.

This script must not be used as a production user-management mechanism.
"""

import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


TEST_USERS = (
    {
        "username": "faculty1",
        "email": "faculty1@coe.local",
        "role": "faculty",
        "password_env": "FACULTY_TEST_PASSWORD",
    },
    {
        "username": "student1",
        "email": "student1@coe.local",
        "role": "student",
        "password_env": "STUDENT_TEST_PASSWORD",
    },
)


def create_test_users() -> None:
    db = SessionLocal()

    try:
        for user_data in TEST_USERS:
            role = db.scalar(
                select(Role).where(Role.name == user_data["role"])
            )

            if role is None:
                raise RuntimeError(
                    f"Required role '{user_data['role']}' does not exist. "
                    "Run seed_roles.py first."
                )

            existing_user = db.scalar(
                select(User).where(
                    User.username == user_data["username"]
                )
            )

            if existing_user is not None:
                print(
                    f"User '{user_data['username']}' already exists."
                )
                continue

            password = os.getenv(user_data["password_env"])

            if not password:
                raise RuntimeError(
                    f"{user_data['password_env']} environment variable "
                    "is required."
                )

            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(password),
                role_id=role.id,
            )

            db.add(user)

            print(
                f"Created user: {user_data['username']} "
                f"({user_data['role']})"
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()