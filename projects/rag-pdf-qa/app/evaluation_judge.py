from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.db import session_scope
from app.models import AnswerQualityJudgementModel


class AnswerQualityJudgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class AnswerQualityJudgement:
    groundedness: int
    answer_quality: int
    completeness: int
    risk_level: str
    verdict: str
    rationale: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class AnswerQualityJudgementRecord:
    judgement_id: str
    created_at: str
    request_id: str | None
    user_id: str
    username: str
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    route: str | None
    llm_provider: str
    llm_model: str
    groundedness: int
    answer_quality: int
    completeness: int
    risk_level: str
    verdict: str
    rationale: str
    usage: dict[str, Any] | None


class AnswerQualityJudgeStore:
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
        route: str | None,
        question: str,
        answer: str,
        sources: list[dict[str, Any]],
        llm_provider: str,
        llm_model: str,
        judgement: AnswerQualityJudgement,
        usage: dict[str, Any] | None,
    ) -> AnswerQualityJudgementRecord:
        row = AnswerQualityJudgementModel(
            judgement_id=f"judge_{uuid4().hex[:16]}",
            created_at=datetime.now(UTC).isoformat(),
            request_id=request_id,
            user_id=user_id,
            username=username,
            organization_id=organization_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            route=route,
            question=question,
            answer_preview=" ".join(answer.split())[:1000],
            sources_json=json.dumps(sources, ensure_ascii=False, sort_keys=True) if sources else None,
            llm_provider=llm_provider,
            llm_model=llm_model,
            groundedness=judgement.groundedness,
            answer_quality=judgement.answer_quality,
            completeness=judgement.completeness,
            risk_level=judgement.risk_level,
            verdict=judgement.verdict,
            rationale=judgement.rationale,
            raw_judge_json=json.dumps(judgement.raw, ensure_ascii=False, sort_keys=True),
            usage_json=json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage else None,
        )
        try:
            with session_scope(self.database_url) as session:
                session.add(row)
                session.flush()
                return _record_from_model(row)
        except SQLAlchemyError as exc:
            raise AnswerQualityJudgeError(f"Failed to record answer quality judgement: {exc}") from exc


def build_answer_quality_judge_messages(
    *,
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
) -> list[dict[str, str]]:
    source_lines = []
    for index, source in enumerate(sources[:20], start=1):
        label = source.get("source_id") or index
        filename = source.get("filename") or "unknown"
        page_number = source.get("page_number")
        chunk_id = source.get("chunk_id")
        preview = " ".join(str(source.get("preview") or "").split())[:900]
        source_lines.append(
            f"[Source {label}] file={filename} page={page_number} chunk={chunk_id}\n{preview}"
        )
    source_text = "\n\n".join(source_lines) if source_lines else "No retrieved sources were supplied."

    return [
        {
            "role": "system",
            "content": (
                "You are an enterprise RAG answer quality judge. "
                "Evaluate only whether the answer is supported by the supplied retrieved sources. "
                "Return only valid JSON without Markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                "Use this JSON schema exactly:\n"
                "{\n"
                '  "groundedness": 0-5,\n'
                '  "answer_quality": 0-5,\n'
                '  "completeness": 0-5,\n'
                '  "risk_level": "low" | "medium" | "high",\n'
                '  "verdict": "pass" | "warn" | "fail",\n'
                '  "rationale": "short reason"\n'
                "}\n\n"
                f"Question:\n{question}\n\n"
                f"Answer:\n{answer}\n\n"
                f"Retrieved sources:\n{source_text}"
            ),
        },
    ]


def parse_answer_quality_judgement(raw_text: str) -> AnswerQualityJudgement:
    data = _load_json_object(raw_text)
    groundedness = _score(data.get("groundedness"))
    answer_quality = _score(data.get("answer_quality"))
    completeness = _score(data.get("completeness"))
    risk_level = _normalize_choice(data.get("risk_level"), {"low", "medium", "high"}, default="medium")
    verdict = _normalize_choice(data.get("verdict"), {"pass", "warn", "fail"}, default="")
    if not verdict:
        verdict = _infer_verdict(
            groundedness=groundedness,
            answer_quality=answer_quality,
            completeness=completeness,
            risk_level=risk_level,
        )
    rationale = str(data.get("rationale") or "").strip()
    if not rationale:
        rationale = "Judge did not provide a rationale."
    rationale = rationale[:2000]
    normalized = {
        **data,
        "groundedness": groundedness,
        "answer_quality": answer_quality,
        "completeness": completeness,
        "risk_level": risk_level,
        "verdict": verdict,
        "rationale": rationale,
    }
    return AnswerQualityJudgement(
        groundedness=groundedness,
        answer_quality=answer_quality,
        completeness=completeness,
        risk_level=risk_level,
        verdict=verdict,
        rationale=rationale,
        raw=normalized,
    )


def _load_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AnswerQualityJudgeError("Judge response is not valid JSON") from exc
    if not isinstance(data, dict):
        raise AnswerQualityJudgeError("Judge response must be a JSON object")
    return data


def _score(value: Any) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(5, number))


def _normalize_choice(value: Any, allowed: set[str], *, default: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else default


def _infer_verdict(
    *,
    groundedness: int,
    answer_quality: int,
    completeness: int,
    risk_level: str,
) -> str:
    average = (groundedness + answer_quality + completeness) / 3
    if risk_level == "high" or groundedness <= 2:
        return "fail"
    if average >= 4 and risk_level == "low":
        return "pass"
    return "warn"


def _record_from_model(row: AnswerQualityJudgementModel) -> AnswerQualityJudgementRecord:
    usage = json.loads(row.usage_json) if row.usage_json else None
    return AnswerQualityJudgementRecord(
        judgement_id=row.judgement_id,
        created_at=row.created_at,
        request_id=row.request_id,
        user_id=row.user_id,
        username=row.username,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        knowledge_base_id=row.knowledge_base_id,
        route=row.route,
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        groundedness=row.groundedness,
        answer_quality=row.answer_quality,
        completeness=row.completeness,
        risk_level=row.risk_level,
        verdict=row.verdict,
        rationale=row.rationale,
        usage=usage if isinstance(usage, dict) else None,
    )
