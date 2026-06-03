from typing import Literal


AgentRoute = Literal["rag", "chat"]


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
    normalized = " ".join(question.lower().strip().split())

    if any(keyword in normalized for keyword in RAG_ROUTE_KEYWORDS):
        return "rag"

    if any(keyword in normalized for keyword in CHAT_ROUTE_KEYWORDS):
        return "chat"

    if len(normalized) <= 12 and not any(mark in normalized for mark in ("?", "？", "什么", "如何", "为什么")):
        return "chat"

    return "rag"
