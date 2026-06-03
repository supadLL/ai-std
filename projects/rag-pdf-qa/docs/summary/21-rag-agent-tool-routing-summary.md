# 第 21 步完成总结：最小 RAG Agent 工具路由

本 summary 记录第 21 步实际完成内容。

对应 goal：

```text
docs/goal/21-rag-agent-tool-routing-goal.md
```

---

## 1. 本次完成了什么

完成内容：

```text
1. 新增最小 Agent 路由模块 app/agent.py
2. 新增 POST /agent/ask 接口
3. 支持 route = chat
4. 支持 route = rag
5. 支持 route = insufficient_context
6. chat route 复用 DeepSeek 普通聊天
7. rag route 复用本地 embedding、Qdrant search、RAG prompt 和 sources 结构
8. insufficient_context route 在检索不到资料或 score_threshold 过滤后返回清晰提示
9. /chat、/rag/ask、/documents/search 原接口保持可用
10. 新增 pytest 覆盖三条 Agent 路由分支
```

---

## 2. 改动文件

代码：

```text
app/agent.py
app/main.py
```

测试：

```text
tests/test_agent.py
```

文档：

```text
README.md
../../README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/08-rag-agent-advanced-roadmap.md
docs/summary/10-rag-test-result.md
docs/summary/21-rag-agent-tool-routing-summary.md
```

---

## 3. 新增接口

新增：

```text
POST /agent/ask
```

请求示例：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

响应核心字段：

```json
{
  "question": "...",
  "route": "rag",
  "reply": "...",
  "model": "...",
  "collection": "rag_chunks",
  "retrieved_count": 5,
  "source_count": 5,
  "sources": [],
  "usage": {}
}
```

`route` 可能为：

```text
chat
rag
insufficient_context
```

---

## 4. 路由策略

当前使用启发式规则：

```text
明显闲聊、感谢、自我介绍、翻译、润色等问题 -> chat
包含知识库、资料、文档、PDF、sources、GUI Agent 等关键词的问题 -> rag
较长的事实型问题默认优先尝试 rag
```

说明：

```text
这是最小 Agent 工具路由，不是复杂 function calling。
它的目标是先建立“判断 -> 选择工具 -> 执行 -> 返回”的 Agent 骨架。
```

后续可以继续优化：

```text
规则表
模型路由
工具调用 JSON
多轮追问
更细的 route_reason
```

---

## 5. 三条路线说明

### chat

适合：

```text
你好
谢谢
你是谁
翻译、润色、改写等通用任务
```

执行：

```text
直接调用 DeepSeek chat
不调用 embedding
不调用 Qdrant
不返回 sources
```

### rag

适合：

```text
需要基于本地知识库回答的问题
明确提到文档、资料、PDF、sources、GUI Agent 等关键词的问题
```

执行：

```text
embedding
-> Qdrant search
-> score_threshold 过滤
-> DeepSeek 基于 sources 回答
```

### insufficient_context

适合：

```text
检索不到相关 chunk
或 score_threshold 过滤后没有可用 sources
```

执行：

```text
不继续调用 DeepSeek
直接返回资料不足提示
```

这样可以避免在没有资料时浪费 token 或让模型编造。

---

## 6. 验证结果

已运行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
compileall 通过
pytest 25 passed
```

测试覆盖：

```text
decide_agent_route 闲聊问题 -> chat
decide_agent_route 文档问题 -> rag
/agent/ask 闲聊问题 -> chat
/agent/ask 文档问题 -> rag，返回 sources
/agent/ask 检索为空 -> insufficient_context，不调用 DeepSeek
/agent/ask 出现在 OpenAPI / Swagger Docs
```

本次没有自动调用真实 DeepSeek API，避免消耗 token。

---

## 7. 当前限制

本次没有做：

```text
复杂多 Agent
LangChain Agent
Graph 工作流
长期记忆
联网搜索
模型级 function calling
Web UI 中的 Agent 模式切换
```

当前路由是启发式规则，可能会有误判。

这在学习阶段是可以接受的，因为本次重点是先打通最小 Agent 工具路由骨架。

---

## 8. 下一步建议

进入第 22 步：

```text
项目测试、收口和最终总结
```

对应 goal：

```text
docs/goal/22-tests-and-project-final-summary-goal.md
```
