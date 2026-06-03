# 第 11 步学习笔记：RAG score_threshold 低分过滤

这一步的目标是：

> 给 `/rag/ask` 增加 `score_threshold`，过滤低相关 chunk，避免不相关资料进入 DeepSeek prompt。

当前优化的接口：

```text
POST /rag/ask
```

---

## 1. 为什么需要 score_threshold

第 10 步测试结果显示：

```text
检索可以返回 top_k 结果，但部分问题的 top5 会混入不够相关的 chunk。
```

如果这些 chunk 直接进入 RAG prompt，DeepSeek 就可能被噪声资料干扰。

所以要增加一个过滤参数：

```text
score_threshold
```

含义：

```text
只保留 score >= score_threshold 的 chunk
```

---

## 2. 请求格式

原来的请求：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

现在可以加：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `question` | 用户问题 |
| `limit` | 先从 Qdrant 取回多少个 top_k 结果 |
| `score_threshold` | 过滤低于该分数的 chunk，可不传 |

如果不传 `score_threshold`：

```text
行为和之前一致，不做分数过滤。
```

---

## 3. 当前处理流程

现在 `/rag/ask` 的流程是：

```text
question
-> embed_text(question)
-> Qdrant search top_k
-> 按 score_threshold 过滤
-> 如果没有剩余 sources，直接返回 404
-> 如果有 sources，拼 RAG prompt
-> 调用 DeepSeek
-> 返回 reply 和 sources
```

注意：

```text
score_threshold 只影响 /rag/ask
/documents/search 仍然返回完整 top_k，方便调试检索质量
```

---

## 4. 响应新增字段

`/rag/ask` 响应新增：

```text
score_threshold
retrieved_count
source_count
```

示例：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "reply": "...",
  "model": "...",
  "collection": "rag_chunks",
  "score_threshold": 0.5,
  "retrieved_count": 5,
  "source_count": 3,
  "sources": [...],
  "usage": {...}
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `score_threshold` | 本次使用的分数阈值 |
| `retrieved_count` | Qdrant 原始返回数量 |
| `source_count` | 过滤后实际进入 RAG prompt 的 sources 数量 |

这样可以看出：

```text
检索到了多少
过滤后还剩多少
```

---

## 5. 过滤后为空怎么办

如果 Qdrant 检索到了结果，但全部低于阈值，会返回：

```text
No document chunks met score_threshold. Lower score_threshold or try another question.
```

这表示：

```text
不是没有索引文档
而是阈值太高，或者问题和知识库不够相关
```

---

## 6. 在 Swagger Docs 中测试

打开：

```text
http://127.0.0.1:8000/docs
```

测试：

```text
POST /rag/ask
```

请求体：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

再测试一个较高阈值：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.9
}
```

预期：

```text
0.5 可能保留部分 sources
0.9 很可能过滤为空并返回 404
```

---

## 7. 代码改动位置

| 内容 | 对应代码 |
|---|---|
| 请求参数 | [`app/main.py`](../../app/main.py) 里的 `RagAskRequest.score_threshold` |
| 响应字段 | [`app/main.py`](../../app/main.py) 里的 `RagAskResponse` |
| 过滤逻辑 | [`app/main.py`](../../app/main.py) 里的 `_filter_results_by_score()` |
| RAG 主流程 | [`app/main.py`](../../app/main.py) 里的 `ask_with_rag()` |

---

## 8. 下一步

第 11 步完成后，下一步是：

```text
优化 /rag/ask 的 sources 返回结构
```

也就是第 12 步：

```text
source_id
preview
source_count
更适合 UI 展示的 sources
```

