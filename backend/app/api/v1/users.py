from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.chat import ChatSession, Message
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        organization_id=user.organization_id,
        department_id=user.department_id,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_first_login=user.is_first_login,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> UserResponse:
    return _user_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    await db.commit()
    await db.refresh(current_user)
    return _user_response(current_user)


@router.get("/me/usage-stats")
async def usage_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    question_count = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.user_id == current_user.id,
            Message.organization_id == current_user.organization_id,
            Message.role == "user",
        )
    )
    session_count = await db.execute(
        select(func.count()).select_from(ChatSession).where(
            ChatSession.user_id == current_user.id,
            ChatSession.organization_id == current_user.organization_id,
        )
    )
    confidence_avg = await db.execute(
        select(func.avg(Message.confidence_score)).where(
            Message.user_id == current_user.id,
            Message.organization_id == current_user.organization_id,
            Message.role == "assistant",
        )
    )
    feedback_count = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.user_id == current_user.id,
            Message.organization_id == current_user.organization_id,
            Message.feedback.is_not(None),
        )
    )
    return {
        "total_questions_asked": int(question_count.scalar_one()),
        "total_sessions_created": int(session_count.scalar_one()),
        "most_active_day": None,
        "average_confidence_score": float(confidence_avg.scalar() or 0.0),
        "feedback_submissions": int(feedback_count.scalar_one()),
    }
