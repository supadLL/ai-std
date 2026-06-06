from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.db import session_scope
from app.models import AnswerFeedbackModel


@dataclass(frozen=True)
class AnswerFeedbackRecord:
    feedback_id: str
    created_at: str
    request_id: str | None
    user_id: str
    username: str
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    rating: str
    route: str | None
    question: str
    answer_preview: str
    details: dict[str, Any] | None = None


class FeedbackError(RuntimeError):
    pass


class AnswerFeedbackStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def record(
        self,
        *,
        request_id: str | None,
        user_id: str,
        username: str,
        organization_id: str,
        workspace_id: str,
        knowledge_base_id: str,
        rating: str,
        question: str,
        answer: str,
        route: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AnswerFeedbackRecord:
        if rating not in {"up", "down"}:
            raise FeedbackError("rating must be 'up' or 'down'")
        feedback = AnswerFeedbackModel(
            feedback_id=f"feedback_{uuid4().hex[:16]}",
            created_at=datetime.now(UTC).isoformat(),
            request_id=request_id,
            user_id=user_id,
            username=username,
            organization_id=organization_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            rating=rating,
            route=route,
            question=question,
            answer_preview=" ".join(answer.split())[:500],
            details_json=json.dumps(details, ensure_ascii=False, sort_keys=True) if details else None,
        )
        try:
            with session_scope(self.database_url) as session:
                session.add(feedback)
                session.flush()
                return _record_from_model(feedback)
        except SQLAlchemyError as exc:
            raise FeedbackError(f"Failed to record answer feedback: {exc}") from exc


def _record_from_model(feedback: AnswerFeedbackModel) -> AnswerFeedbackRecord:
    details = json.loads(feedback.details_json) if feedback.details_json else None
    return AnswerFeedbackRecord(
        feedback_id=feedback.feedback_id,
        created_at=feedback.created_at,
        request_id=feedback.request_id,
        user_id=feedback.user_id,
        username=feedback.username,
        organization_id=feedback.organization_id,
        workspace_id=feedback.workspace_id,
        knowledge_base_id=feedback.knowledge_base_id,
        rating=feedback.rating,
        route=feedback.route,
        question=feedback.question,
        answer_preview=feedback.answer_preview,
        details=details if isinstance(details, dict) else None,
    )
