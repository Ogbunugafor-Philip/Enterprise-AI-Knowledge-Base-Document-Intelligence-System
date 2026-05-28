from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, Message
from app.models.monitoring import MonitoringLog
from app.models.user import User

ONBOARDING_TOTAL_STEPS = 5


async def create_chat_session(db: AsyncSession, user: User, title: str | None = None) -> ChatSession:
    session = ChatSession(
        user_id=user.id,
        organization_id=user.organization_id,
        title=title or "New chat",
    )
    db.add(session)
    await db.flush()
    from app.services.audit_service import log_action
    await log_action(db, organization_id=user.organization_id, user_id=user.id, action="CHAT_SESSION_CREATED", resource_type="chat_session", resource_id=str(session.id))
    return session


async def get_user_chat_sessions(db: AsyncSession, user: User, limit: int = 20, offset: int = 0) -> tuple[list[ChatSession], int]:
    filters = [ChatSession.user_id == user.id, ChatSession.organization_id == user.organization_id]
    total_result = await db.execute(select(func.count()).select_from(ChatSession).where(*filters))
    result = await db.execute(
        select(ChatSession).where(*filters).order_by(desc(ChatSession.updated_at)).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), int(total_result.scalar_one())


async def get_session_messages(db: AsyncSession, user: User, session_id: UUID) -> tuple[ChatSession | None, list[Message]]:
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.organization_id == user.organization_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        return None, []
    message_result = await db.execute(
        select(Message).where(Message.session_id == session.id, Message.organization_id == user.organization_id).order_by(Message.created_at)
    )
    return session, list(message_result.scalars().all())


async def save_user_message(db: AsyncSession, user: User, session: ChatSession, content: str) -> Message:
    message = Message(
        session_id=session.id,
        user_id=user.id,
        organization_id=user.organization_id,
        role="user",
        content=content,
        source_documents=None,
    )
    db.add(message)
    await db.flush()
    return message


async def save_ai_response(
    db: AsyncSession,
    user: User,
    session: ChatSession,
    answer: str,
    source_documents: list[dict],
    confidence_score: float,
    retrieval_score: float,
    hallucination_risk_score: float,
    response_rejected: bool,
) -> Message:
    message = Message(
        session_id=session.id,
        user_id=user.id,
        organization_id=user.organization_id,
        role="assistant",
        content=answer,
        source_documents=source_documents,
        confidence_score=confidence_score,
        retrieval_score=retrieval_score,
        hallucination_risk_score=hallucination_risk_score,
        response_rejected=response_rejected,
    )
    db.add(message)
    await db.flush()
    return message


async def search_user_conversations(db: AsyncSession, user: User, query: str, limit: int = 20, offset: int = 0) -> tuple[list[ChatSession], list[Message], int]:
    scoped_sessions = select(ChatSession.id).where(
        ChatSession.user_id == user.id,
        ChatSession.organization_id == user.organization_id,
    )
    session_result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id.in_(scoped_sessions), ChatSession.title.ilike(f"%{query}%"))
        .limit(limit)
        .offset(offset)
    )
    message_result = await db.execute(
        select(Message)
        .where(
            Message.session_id.in_(scoped_sessions),
            Message.user_id == user.id,
            Message.organization_id == user.organization_id,
            Message.content.ilike(f"%{query}%"),
        )
        .limit(limit)
        .offset(offset)
    )
    sessions = list(session_result.scalars().all())
    messages = list(message_result.scalars().all())
    return sessions, messages, len(sessions) + len(messages)


async def submit_message_feedback(db: AsyncSession, user: User, message_id: UUID, feedback_type: str, feedback_note: str | None = None) -> Message | None:
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == user.id, Message.organization_id == user.organization_id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        return None
    message.feedback = feedback_type
    message.feedback_submitted_at = datetime.now(timezone.utc)
    from app.services.audit_service import log_action
    await log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="HALLUCINATION_REPORTED" if feedback_type == "hallucination" else "FEEDBACK_SUBMITTED",
        resource_type="message",
        resource_id=str(message.id),
        new_value={"feedback": feedback_type, "note": feedback_note},
    )
    await db.flush()
    return message


async def track_ai_usage(db: AsyncSession, user: User, response_time_ms: int, token_usage: dict) -> None:
    db.add(
        MonitoringLog(
            organization_id=user.organization_id,
            event_type="ai_query",
            service_name="chat",
            endpoint="/api/v1/chat/ask",
            method="POST",
            status_code=200,
            response_time_ms=response_time_ms,
            user_id=user.id,
            token_usage=token_usage,
        )
    )
    from app.services.audit_service import log_action
    await log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="AI_QUERY_MADE",
        resource_type="chat",
        new_value={"response_time_ms": response_time_ms, "token_usage": token_usage},
    )


def get_sample_questions(user: User) -> dict:
    department = user.department.name if getattr(user, "department", None) else None
    role = user.role.name if getattr(user, "role", None) else None
    questions = [
        "What policies apply to my department?",
        "Summarize the latest approved procedure documents.",
        "Which documents mention compliance requirements?",
        "What are the key onboarding steps for my role?",
        "Show approved guidance for this workflow.",
        "What changed in the most recent document version?",
    ]
    return {"department": department, "role": role, "questions": questions}


def get_onboarding_status(user: User) -> dict:
    return {
        "is_completed": bool(getattr(user, "onboarding_completed", False)),
        "current_step": int(getattr(user, "onboarding_step", 0)),
        "total_steps": ONBOARDING_TOTAL_STEPS,
    }


async def complete_onboarding_step(db: AsyncSession, user: User, step_number: int) -> dict:
    user.onboarding_step = max(int(getattr(user, "onboarding_step", 0)), step_number)
    if user.onboarding_step >= ONBOARDING_TOTAL_STEPS:
        user.onboarding_completed = True
    await db.flush()
    return get_onboarding_status(user)


async def complete_onboarding(db: AsyncSession, user: User) -> dict:
    user.onboarding_step = ONBOARDING_TOTAL_STEPS
    user.onboarding_completed = True
    await db.flush()
    return get_onboarding_status(user)
