from dataclasses import dataclass
from typing import Literal


AgentRoute = Literal["rag", "chat"]


@dataclass(frozen=True)
class AgentRouteDecision:
    route: AgentRoute
    reason: str
    matched_keywords: list[str]
    normalized_question: str


RAG_ROUTE_KEYWORDS = (
    "知识库",
    "资料",
    "文档",
    "pdf",
    "source",
    "sources",
    "来源",
    "根据",
    "检索",
    "论文",
    "报告",
    "章节",
    "页面",
    "页码",
    "gui agent",
    "agent",
    "rag",
    "qdrant",
    "chunk",
    "embedding",
)

CHAT_ROUTE_KEYWORDS = (
    "你好",
    "您好",
    "hello",
    "hi",
    "谢谢",
    "感谢",
    "你是谁",
    "自我介绍",
    "讲个笑话",
    "天气",
    "现在几点",
    "翻译",
    "润色",
    "改写",
)


def decide_agent_route(question: str) -> AgentRoute:
    return explain_agent_route(question).route


def explain_agent_route(question: str) -> AgentRouteDecision:
    normalized = " ".join(question.lower().strip().split())
    rag_matches = [keyword for keyword in RAG_ROUTE_KEYWORDS if keyword in normalized]
    chat_matches = [keyword for keyword in CHAT_ROUTE_KEYWORDS if keyword in normalized]

    if rag_matches:
        return AgentRouteDecision(
            route="rag",
            reason="问题命中了知识库、文档、RAG 或资料相关关键词，需要先检索本地知识库。",
            matched_keywords=rag_matches,
            normalized_question=normalized,
        )

    if chat_matches:
        return AgentRouteDecision(
            route="chat",
            reason="问题命中了闲聊或通用对话关键词，不需要检索本地知识库。",
            matched_keywords=chat_matches,
            normalized_question=normalized,
        )

    if len(normalized) <= 12 and not any(mark in normalized for mark in ("?", "？", "什么", "如何", "为什么")):
        return AgentRouteDecision(
            route="chat",
            reason="问题较短且没有明显的检索型疑问词，按普通对话处理。",
            matched_keywords=[],
            normalized_question=normalized,
        )

    return AgentRouteDecision(
        route="rag",
        reason="问题更像需要依据资料回答的开放问题，默认先走本地知识库检索。",
        matched_keywords=[],
        normalized_question=normalized,
    )
