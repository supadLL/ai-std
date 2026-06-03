# 第 21 步执行目标：实现最小 RAG Agent 工具路由

这一步的目标是：

> 在 RAG 检索质量和 UI 基础可用之后，实现一个能选择是否检索的最小 Agent。

---

## 1. 背景

当前 `/rag/ask` 是固定流程：

```text
用户问题 -> 一定检索 -> 一定把 sources 交给 DeepSeek -> 回答
```

Agent 多一层决策：

```text
用户问题 -> 判断是否需要知识库 -> 选择工具 -> 观察结果 -> 回答
```

但当前阶段不需要复杂多 Agent。

先实现最小工具路由即可。

---

## 2. 本次目标

新增最小 Agent 流程：

```text
1. 判断问题是否需要检索
2. 如果需要，调用本地 search_documents
3. 基于 sources 调用 answer_with_context
4. 如果不需要，走普通 /chat
5. 返回 route、reply、sources、usage
```

建议新增接口：

```text
POST /agent/ask
```

建议内部工具：

```text
search_documents(query, limit, score_threshold)
answer_with_context(question, sources)
direct_chat(question)
```

---

## 3. 不做什么

本次不做：

- 多 Agent 协作
- LangChain Agent
- Graph 工作流
- 复杂 function calling
- 长期记忆
- 权限系统
- 自动联网搜索

---

## 4. 预计修改文件

可能新增：

```text
app/agent.py
```

可能修改：

```text
app/main.py
app/deepseek_client.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/21-rag-agent-tool-routing-step.md
docs/summary/21-rag-agent-tool-routing-summary.md
```

---

## 5. 接口变化

建议新增请求：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

建议响应：

```json
{
  "question": "...",
  "route": "rag",
  "reply": "...",
  "sources": [],
  "usage": {}
}
```

`route` 可以是：

```text
rag
chat
insufficient_context
```

---

## 6. 验收标准

完成后应满足：

```text
1. POST /agent/ask 出现在 Swagger Docs
2. 文档相关问题走 rag route
3. 普通闲聊或非资料问题走 chat route
4. RAG route 返回 sources
5. 资料不足时能给出清晰提示
6. /rag/ask 原接口仍然可用
7. /chat 原接口仍然可用
```

---

## 7. 测试方式

建议测试三类问题：

```text
1. 明确需要知识库的问题
2. 普通聊天问题
3. 知识库中不存在答案的问题
```

验证：

```text
route 是否合理
sources 是否符合预期
reply 是否引用资料
usage 是否返回
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/21-rag-agent-tool-routing-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

