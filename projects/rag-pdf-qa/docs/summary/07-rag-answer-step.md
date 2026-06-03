# 第 7 步学习笔记：DeepSeek RAG 问答最小实现

这一步的目标是：

> 把 Qdrant 检索出来的相关 chunk 交给 DeepSeek，让模型基于本地资料回答问题。

当前新增一个接口：

```text
POST /rag/ask
```

这一步开始，项目从“能检索知识库”进入到“能基于知识库生成回答”。

---

## 1. 这一阶段在 RAG 链路里的位置

前面已经完成：

```text
PDF -> 提取文本 -> chunk 切分 -> embedding 向量化 -> Qdrant 存储 -> Qdrant 检索
```

本次补上的部分是：

```text
用户问题
-> 生成 query embedding
-> Qdrant 找 top_k 个相关的 chunk
-> 拼成 RAG prompt
-> 调用 DeepSeek
-> 返回回答和 sources
```

所以当前最小完整 RAG 链路是：

```text
问题 -> 检索 -> 组装上下文 -> LLM 生成 -> 返回答案和来源
```

---

## 2. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|
| DeepSeek 自定义 messages 调用 | [`app/deepseek_client.py`](../../app/deepseek_client.py) 里的 `chat_messages()` |
| RAG 请求和响应结构 | [`app/main.py`](../../app/main.py) 里的 `RagAskRequest` 和 `RagAskResponse` |
| RAG 问答接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/rag/ask")` |
| RAG prompt 组装 | [`app/main.py`](../../app/main.py) 里的 `_build_rag_messages()` |
| 使用说明 | [`README.md`](../../README.md) 里的“测试最小 RAG 问答” |

---

## 3. `/rag/ask` 做了什么

接口输入：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `question` | 用户问题 |
| `limit` | 从 Qdrant 取多少个最相关 chunk，也就是 top_k |

接口内部流程：

```text
question
-> embed_text(question)
-> search_chunks(...)
-> _build_rag_messages(...)
-> deepseek_client.chat_messages(...)
-> RagAskResponse
```

---

## 4. 为什么不直接把问题发给 DeepSeek

如果直接调用 `/chat`：

```text
用户问题 -> DeepSeek
```

模型只能依赖自身训练知识回答，不知道本地 PDF 里的内容。

RAG 的关键变化是中间多了一步检索：

```text
用户问题 -> 本地 Qdrant 检索 -> 带资料调用 DeepSeek
```

这样回答会更贴近你已经索引的 PDF。

---

## 5. RAG prompt 是什么

当前 `_build_rag_messages()` 会生成两类消息：

```text
system message:
告诉模型只能基于检索资料回答，不要编造，优先中文，并标注来源。

user message:
包含用户问题和 Qdrant 检索出来的 chunks。
```

其中每个 chunk 会带上：

```text
Source 编号
filename
page_number
chunk_id
score
text
```

这样 DeepSeek 回答时就有资料来源，接口返回时也能把 `sources` 一起给前端或调试页面。

---

## 6. 如何在 Swagger Docs 页面测试

启动服务：

```powershell
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

测试顺序一定是：

```text
1. POST /documents/index
2. POST /documents/search
3. POST /rag/ask
```

如果还没有索引 PDF，`/rag/ask` 没有可检索资料，回答质量一定不会稳定。

---

## 7. 先索引 PDF

在 Swagger Docs 里展开：

```text
POST /documents/index
```

点击：

```text
Try it out
```

上传 PDF，并填写：

```text
chunk_size = 800
overlap = 100
```

成功时会返回类似：

```json
{
  "filename": "GUIagent.pdf",
  "collection": "rag_chunks",
  "chunk_count": 43,
  "indexed_count": 43,
  "dimension": 512,
  "local_path": ".qdrant"
}
```

这表示 PDF 已经写入本地 Qdrant。

---

## 8. 再测试纯检索

在 Swagger Docs 里展开：

```text
POST /documents/search
```

请求示例：

```json
{
  "query": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

先看 `results` 是否相关。

如果这里检索不到相关 chunk，后面的 `/rag/ask` 也不会答好。

---

## 9. 最后测试 RAG 问答

在 Swagger Docs 里展开：

```text
POST /rag/ask
```

请求示例：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

返回结果重点看三个字段：

| 字段 | 含义 |
|---|---|
| `reply` | DeepSeek 基于检索资料生成的回答 |
| `sources` | 本次喂给 DeepSeek 的 chunk |
| `usage` | DeepSeek 返回的 token 用量 |

---

## 10. `/rag/ask` 和 `/documents/search` 的区别

| 接口 | 作用 |
|---|---|
| `/documents/search` | 只做检索，不调用 DeepSeek |
| `/rag/ask` | 先检索，再调用 DeepSeek 生成回答 |

调试 RAG 时，建议先看 `/documents/search`。

检索结果对了，再看 `/rag/ask` 的回答是否好。

---

## 11. 常见错误

### 还没有索引 PDF

如果还没调用 `/documents/index`，可能会报：

```text
Collection 'rag_chunks' does not exist. Index a document first.
```

解决：

```text
先上传 PDF 调用 /documents/index
```

### DeepSeek API Key 没配置

如果 `.env` 没有配置：

```text
DEEPSEEK_API_KEY
```

会报：

```text
DEEPSEEK_API_KEY is not configured
```

解决：

```text
检查 .env 文件
重启 uvicorn 服务
```

### 检索结果不相关

如果 `/documents/search` 返回的 chunk 和问题不相关，先不要改 prompt。

优先检查：

```text
问题是否问得太泛
PDF 是否已经正确索引
chunk_size 是否太大或太小
overlap 是否合理
limit 是否太小
```

---

## 12. 当前这一步还没有做什么

当前只是最小 RAG 实现，还没有做：

- 多轮对话记忆
- rerank
- hybrid search
- 分数阈值过滤
- 答案流式输出
- 前端页面
- Agent 工具调用

这些都可以后续再做。

现在最重要的是先验证：

```text
检索是否命中正确资料
回答是否严格基于 sources
```

---

## 13. 下一步建议

下一步不要急着做 Agent。

先准备 10-20 个测试问题，每个问题记录：

```text
问题
期望命中的页码
/documents/search 的 top_k 结果
/rag/ask 的回答
是否引用了正确来源
```

然后再调：

```text
chunk_size
overlap
limit/top_k
prompt
```

这样后面写项目总结时，才有真实的 RAG 调优数据。

