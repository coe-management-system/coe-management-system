from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = AuthService.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password,
    )

    access_token = AuthService.create_access_token_for_user(user)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    role = db.scalar(
        select(Role).where(Role.id == current_user.role_id)
    )

    return CurrentUserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role_id=current_user.role_id,
        role_name=role.name if role else None,
    )