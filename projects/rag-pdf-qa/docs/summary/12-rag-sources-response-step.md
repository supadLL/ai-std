# 第 12 步学习笔记：RAG sources 返回结构优化

这一步的目标是：

> 让 `/rag/ask` 返回的 sources 更适合 UI 展示、调试和后续 Agent 使用。

当前优化的接口：

```text
POST /rag/ask
```

---

## 1. 为什么要优化 sources

第 7 步实现最小 RAG 时，`/rag/ask` 直接复用了 `/documents/search` 的结果结构。

原来的 sources 大概是：

```json
{
  "score": 0.56,
  "filename": "GUIagent.pdf",
  "page_number": 23,
  "chunk_id": 23,
  "text": "完整 chunk 文本..."
}
```

这个结构适合调试检索，但不适合最终 RAG 回答展示。

原因：

```text
完整 text 太长
前端展示不方便
模型引用 Source 时没有稳定 source_id
后续 UI 右侧 sources 面板需要更短的 preview
```

所以这一步把 `/rag/ask` 的 sources 改成更轻的结构。

---

## 2. 当前新的 sources 结构

现在 `/rag/ask` 的响应里会多一个：

```text
source_count
```

每个 source 的结构变成：

```json
{
  "source_id": 1,
  "score": 0.5638,
  "filename": "GUIagent.pdf",
  "page_number": 23,
  "chunk_id": 23,
  "preview": "面向动态场景的解决方案..."
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `source_id` | 当前回答中的来源编号，对应 prompt 里的 `[Source 1]` |
| `score` | Qdrant 返回的相似度分数 |
| `filename` | 来源文件名 |
| `page_number` | 来源页码 |
| `chunk_id` | chunk 编号 |
| `preview` | chunk 文本预览，不返回完整正文 |

---

## 3. `/documents/search` 为什么不改

`/documents/search` 仍然保留完整 `text`。

原因：

```text
/documents/search 是调试检索质量用的接口
/rag/ask 是面向 RAG 回答和 UI 展示的接口
```

也就是说：

| 接口 | sources/text 策略 |
|---|---|
| `/documents/search` | 返回完整 text，方便看检索是否命中 |
| `/rag/ask` | 返回 preview，方便展示和引用 |

这样两个接口职责更清楚。

---

## 4. 代码改动位置

| 内容 | 对应代码 |
|---|---|
| RAG source 响应结构 | [`app/main.py`](../../app/main.py) 里的 `RagSourceResponse` |
| RAG 回答响应结构 | [`app/main.py`](../../app/main.py) 里的 `RagAskResponse` |
| source 转换逻辑 | [`app/main.py`](../../app/main.py) 里的 `_to_rag_source_response()` |
| `/rag/ask` 返回 sources | [`app/main.py`](../../app/main.py) 里的 `ask_with_rag()` |

---

## 5. 在 Swagger Docs 中测试

打开：

```text
http://127.0.0.1:8000/docs
```

先确保已经索引 PDF：

```text
POST /documents/index
```

再测试：

```text
POST /rag/ask
```

请求体：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

重点看响应：

```json
{
  "question": "...",
  "reply": "...",
  "model": "...",
  "collection": "rag_chunks",
  "source_count": 5,
  "sources": [
    {
      "source_id": 1,
      "score": 0.5638,
      "filename": "GUIagent.pdf",
      "page_number": 23,
      "chunk_id": 23,
      "preview": "..."
    }
  ],
  "usage": {...}
}
```

如果 `sources` 里还有完整 `text`，说明服务没有重启，或者代码没有更新。

---

## 6. 这一步对后续 UI 的价值

后续 UI 可以直接用 `sources` 渲染右侧面板：

```text
[Source 1] GUIagent.pdf / page 23 / score 0.5638
preview...
```

用户点击 source 时，后续再考虑：

```text
展开完整 chunk
跳转页码
查看原文
```

当前先不做这些扩展。

这一步只做最小展示结构。

---

## 7. 当前还没做什么

这一步还没有实现：

- `used_sources`
- source 点击展开全文
- source 对应 PDF 页预览
- 前端 UI
- rerank

这些后续继续做。

---

## 8. 下一步建议

第 12 步完成后，下一步最适合做：

```text
固定 RAG 输出格式
```

原因：

```text
score_threshold 和 sources 展示结构都已经补上
接下来要让 reply 的格式更稳定
```

建议输出格式逐步固定为：

```text
答案
依据
资料不足之处
```

