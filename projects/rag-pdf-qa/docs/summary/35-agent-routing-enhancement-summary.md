# 第 35 步完成总结：Agent 工具路由增强

## 1. 本次完成了什么

本次在已有 `/agent/ask` 最小路由能力上，增强了 Agent 的可解释性和前端可观察性。

新增能力：

```text
1. /agent/ask 返回 route_reason
2. /agent/ask 返回 tools_used
3. /agent/ask 返回 routing_debug
4. 无检索结果和阈值过滤场景返回清晰回退原因
5. Web UI 知识问答页支持 RAG / Agent 模式切换
6. Web UI debug 区展示 route、tools、reason 和 fallback
```

本次没有引入 LangChain、Graph 工作流或复杂多 Agent 框架，仍然保持当前项目的最小可解释实现路线。

---

## 2. 改动文件

核心代码：

```text
app/agent.py
app/main.py
```

前端：

```text
web/index.html
web/app.js
web/styles.css
```

测试：

```text
tests/test_agent.py
tests/test_main_api.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
docs/summary/35-agent-routing-enhancement-summary.md
```

---

## 3. 接口变化

扩展接口：

```text
POST /agent/ask
```

响应新增字段：

```json
{
  "route_reason": "问题命中了知识库、文档、RAG 或资料相关关键词，需要先检索本地知识库。",
  "tools_used": ["local_embedding", "qdrant_search", "deepseek_rag"],
  "routing_debug": {
    "selected_route": "rag",
    "matched_keywords": ["知识库"],
    "normalized_question": "请根据知识库回答...",
    "requested_limit": 5,
    "score_threshold": null,
    "retrieved_count": 3,
    "filtered_count": 3,
    "top_score": 0.82,
    "fallback": null
  }
}
```

旧字段仍然保留：

```text
question
route
reply
model
collection
score_threshold
retrieved_count
source_count
sources
usage
```

---

## 4. 路由和回退逻辑

当前 Agent 路由仍然是轻量规则：

```text
chat：闲聊、感谢、自我介绍、短普通问题
rag：知识库、资料、文档、PDF、RAG、Qdrant、chunk、embedding 等相关问题
insufficient_context：选择 RAG 后，本地知识库没有可用资料
```

回退场景：

| 场景 | route | tools_used | fallback |
|---|---|---|---|
| 闲聊问题 | `chat` | `deepseek_chat` | `null` |
| 检索命中并生成回答 | `rag` | `local_embedding`, `qdrant_search`, `deepseek_rag` | `null` |
| Qdrant 无返回 | `insufficient_context` | `local_embedding`, `qdrant_search` | `no_retrieved_chunks` |
| score_threshold 过滤掉全部结果 | `insufficient_context` | `local_embedding`, `qdrant_search` | `score_threshold_filtered_all` |

---

## 5. Web UI 变化

知识问答页新增：

```text
模式：RAG / Agent
```

行为：

```text
RAG 模式：调用 /rag/ask
Agent 模式：调用 /agent/ask
```

Agent 模式下，右侧 debug 区新增展示：

```text
route
tools
reason
fallback
```

这样在页面上就能看到 Agent 为什么选择某条路径，以及是否发生了资料不足回退。

---

## 6. 验证结果

编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
```

结果：

```text
通过
```

pytest：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
40 passed
```

新增覆盖：

```text
chat 路由返回 route_reason / tools_used / routing_debug
rag 路由返回 route_reason / tools_used / routing_debug
无检索结果返回 no_retrieved_chunks
阈值过滤返回 score_threshold_filtered_all
Web UI 包含 RAG / Agent 模式切换控件
```

---

## 7. 当前限制

当前 Agent 仍是轻量规则路由，不是完整智能规划器。

还没有做：

```text
LLM 路由决策
多工具并行
多轮记忆
复杂任务拆解
Graph 工作流
外部联网工具
```

这符合当前学习阶段目标：先把 RAG Agent 的可解释链路跑清楚。

---

## 8. 下一步

下一步建议进入：

```text
第 36 步：知识库管理能力增强
```

重点方向：

```text
1. Web UI 支持文档详情查看
2. Web UI 支持删除文档
3. 展示文档 chunk 数、OCR 来源、hash、索引时间
4. 增强知识库管理的可操作性
```
