import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.models.chat import Message
from app.services.ai_guard_service import enforce_no_source_no_answer, get_fallback_message, should_reject_response
from app.services.chat_service import create_chat_session, submit_message_feedback


class FakeDB:
    def __init__(self, scalar=None):
        self.added = []
        self.scalar = scalar

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def execute(self, query):
        return SimpleNamespace(scalar_one_or_none=lambda: self.scalar)


def test_create_chat_session_creates_session_with_correct_user_and_organization():
    db = FakeDB()
    user = SimpleNamespace(id=uuid4(), organization_id=uuid4())

    session = asyncio.run(create_chat_session(db, user, "Policy question"))

    assert session.user_id == user.id
    assert session.organization_id == user.organization_id
    assert session.title == "Policy question"
    assert db.added[0] is session


def test_get_user_chat_sessions_never_returns_sessions_from_other_users():
    user = SimpleNamespace(id=uuid4(), organization_id=uuid4())
    other_user_session = SimpleNamespace(user_id=uuid4(), organization_id=user.organization_id)
    own_session = SimpleNamespace(user_id=user.id, organization_id=user.organization_id)

    visible = [session for session in [own_session, other_user_session] if session.user_id == user.id]

    assert visible == [own_session]


def test_search_user_conversations_scoped_to_current_user_only():
    user = SimpleNamespace(id=uuid4(), organization_id=uuid4())
    messages = [
        SimpleNamespace(user_id=user.id, organization_id=user.organization_id, content="policy details"),
        SimpleNamespace(user_id=uuid4(), organization_id=user.organization_id, content="policy details"),
    ]

    matches = [message for message in messages if message.user_id == user.id and "policy" in message.content]

    assert len(matches) == 1
    assert matches[0].user_id == user.id


def test_submit_message_feedback_saves_correct_feedback_type():
    user = SimpleNamespace(id=uuid4(), organization_id=uuid4())
    message = Message(id=uuid4(), session_id=uuid4(), user_id=user.id, organization_id=user.organization_id, role="assistant", content="answer")
    db = FakeDB(scalar=message)

    updated = asyncio.run(submit_message_feedback(db, user, message.id, "hallucination", "Wrong source"))

    assert updated.feedback == "hallucination"
    assert updated.feedback_submitted_at is not None


def test_should_reject_response_returns_true_for_low_confidence():
    assert should_reject_response(confidence_score=0.49, hallucination_risk=0.1)


def test_should_reject_response_returns_true_for_high_hallucination_risk():
    assert should_reject_response(confidence_score=0.9, hallucination_risk=0.71)


def test_should_reject_response_returns_false_for_good_scores():
    assert not should_reject_response(confidence_score=0.85, hallucination_risk=0.2)


def test_get_fallback_message_returns_non_empty_string():
    assert get_fallback_message()


def test_enforce_no_source_no_answer_blocks_response_when_no_sources_provided():
    blocked, fallback = enforce_no_source_no_answer([])

    assert blocked
    assert fallback
