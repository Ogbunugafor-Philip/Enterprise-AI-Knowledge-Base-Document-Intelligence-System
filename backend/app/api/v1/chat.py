from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_permission
from app.core.database import get_db
from app.core.permissions import PermissionEnum
from app.models.audit import AuditLog
from app.models.chat import ChatSession, Message
from app.models.user import User
from app.schemas.chat import (
    AskQuestionRequest,
    AskQuestionResponse,
    ChatSearchResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
    FeedbackRequest,
    FeedbackResponse,
    MessageResponse,
    OnboardingStatusResponse,
    OnboardingStepRequest,
    SampleQuestionsResponse,
)
from app.services import ai_guard_service
from app.services.chat_service import (
    complete_onboarding,
    complete_onboarding_step,
    create_chat_session,
    get_onboarding_status,
    get_sample_questions,
    get_session_messages,
    get_user_chat_sessions,
    save_ai_response,
    save_user_message,
    search_user_conversations,
    submit_message_feedback,
    track_ai_usage,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        source_documents=message.source_documents,
        confidence_score=float(message.confidence_score) if message.confidence_score is not None else None,
        retrieval_score=float(message.retrieval_score) if message.retrieval_score is not None else None,
        hallucination_risk_score=float(message.hallucination_risk_score) if message.hallucination_risk_score is not None else None,
        response_rejected=message.response_rejected,
        feedback=message.feedback,
        created_at=message.created_at,
    )


async def _session_response(db: AsyncSession, session: ChatSession) -> ChatSessionResponse:
    messages = await db.execute(select(Message).where(Message.session_id == session.id))
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(list(messages.scalars().all())),
    )


@router.post("/sessions", response_model=ChatSessionResponse, dependencies=[Depends(require_permission(PermissionEnum.CHAT_ASK_QUESTION))])
async def create_session(
    payload: ChatSessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ChatSessionResponse:
    session = await create_chat_session(db, current_user, payload.title)
    await db.commit()
    await db.refresh(session)
    return await _session_response(db, session)


@router.get("/sessions", response_model=ChatSessionListResponse, dependencies=[Depends(require_permission(PermissionEnum.CHAT_VIEW_OWN_HISTORY))])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ChatSessionListResponse:
    sessions, total = await get_user_chat_sessions(db, current_user, limit, offset)
    return ChatSessionListResponse(sessions=[await _session_response(db, session) for session in sessions], total=total)


@router.get("/sessions/{session_id}", dependencies=[Depends(require_permission(PermissionEnum.CHAT_VIEW_OWN_HISTORY))])
async def get_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    session, messages = await get_session_messages(db, current_user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat session access denied")
    return {"session": await _session_response(db, session), "messages": [_message_response(message) for message in messages]}


@router.delete("/sessions/{session_id}", dependencies=[Depends(require_permission(PermissionEnum.CHAT_VIEW_OWN_HISTORY))])
async def delete_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    session, _ = await get_session_messages(db, current_user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat session access denied")
    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="chat_session_deleted",
            resource_type="chat_session",
            resource_id=str(session.id),
        )
    )
    await db.delete(session)
    await db.commit()
    return {"message": "Chat session deleted"}


@router.post("/ask", response_model=AskQuestionResponse, dependencies=[Depends(require_permission(PermissionEnum.CHAT_ASK_QUESTION))])
async def ask_question(
    payload: AskQuestionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AskQuestionResponse:
    if payload.session_id:
        session, _ = await get_session_messages(db, current_user, payload.session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat session access denied")
    else:
        session = await create_chat_session(db, current_user, payload.question[:80])

    await save_user_message(db, current_user, session, payload.question)
    retrieved_chunks: list[dict] = []
    eligible_sources = await ai_guard_service.filter_eligible_documents(db, current_user, retrieved_chunks)
    blocked, fallback = ai_guard_service.enforce_no_source_no_answer(eligible_sources)

    if blocked:
        answer = fallback or ai_guard_service.get_fallback_message()
        confidence_score = 0.0
        retrieval_score = 0.0
        hallucination_risk_score = 1.0
        response_rejected = True
    else:
        answer = "Based on the approved source documents, here is a grounded answer placeholder for Phase 9 RAG."
        retrieval_score = ai_guard_service.calculate_retrieval_score(eligible_sources)
        confidence_score = ai_guard_service.calculate_confidence_score(eligible_sources, answer)
        hallucination_risk_score = ai_guard_service.calculate_hallucination_risk(confidence_score, retrieval_score)
        response_rejected = ai_guard_service.should_reject_response(confidence_score, hallucination_risk_score)
        if response_rejected:
            answer = ai_guard_service.get_fallback_message()
            fallback = answer

    ai_message = await save_ai_response(
        db,
        current_user,
        session,
        answer,
        eligible_sources,
        confidence_score,
        retrieval_score,
        hallucination_risk_score,
        response_rejected,
    )
    await track_ai_usage(db, current_user, response_time_ms=0, token_usage={"prompt_tokens": 0, "completion_tokens": 0})
    await db.commit()
    await db.refresh(ai_message)
    return AskQuestionResponse(
        message_id=ai_message.id,
        answer=answer,
        source_documents=eligible_sources,
        confidence_score=confidence_score,
        retrieval_score=retrieval_score,
        hallucination_risk_score=hallucination_risk_score,
        response_rejected=response_rejected,
        fallback_message=fallback,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    payload: FeedbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FeedbackResponse:
    message = await submit_message_feedback(db, current_user, payload.message_id, payload.feedback_type, payload.feedback_note)
    if message is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Message access denied")
    await db.commit()
    return FeedbackResponse(message_id=message.id, feedback_type=payload.feedback_type, submitted_at=message.feedback_submitted_at or datetime.now(timezone.utc))


@router.get("/search", response_model=ChatSearchResponse, dependencies=[Depends(require_permission(PermissionEnum.CHAT_VIEW_OWN_HISTORY))])
async def search(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    query: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ChatSearchResponse:
    sessions, messages, total = await search_user_conversations(db, current_user, query, limit, offset)
    return ChatSearchResponse(
        sessions=[await _session_response(db, session) for session in sessions],
        messages=[_message_response(message) for message in messages],
        total_results=total,
    )


@router.get("/sample-questions", response_model=SampleQuestionsResponse)
async def sample_questions(current_user: Annotated[User, Depends(get_current_active_user)]) -> SampleQuestionsResponse:
    return SampleQuestionsResponse(**get_sample_questions(current_user))


@router.get("/onboarding-status", response_model=OnboardingStatusResponse)
async def onboarding_status(current_user: Annotated[User, Depends(get_current_active_user)]) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(**get_onboarding_status(current_user))


@router.post("/onboarding/complete-step", response_model=OnboardingStatusResponse)
async def onboarding_complete_step(
    payload: OnboardingStepRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> OnboardingStatusResponse:
    status_payload = await complete_onboarding_step(db, current_user, payload.step_number)
    await db.commit()
    return OnboardingStatusResponse(**status_payload)


@router.post("/onboarding/complete")
async def onboarding_complete(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    await complete_onboarding(db, current_user)
    await db.commit()
    return {"message": "Onboarding completed"}
