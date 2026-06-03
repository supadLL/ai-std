# 第 13 步执行目标：固定 RAG 输出格式

这份 goal 文档用于指导下一步开发。

状态：已完成。

完成记录：

```text
docs/summary/13-rag-output-format-step.md
docs/summary/13-rag-output-format-summary.md
```

---

## 1. 背景

当前已经完成：

```text
第 11 步：score_threshold 低分过滤
第 12 步：sources 返回结构优化
```

现在 `/rag/ask` 的 sources 已经更适合展示：

```text
source_id
score
filename
page_number
chunk_id
preview
```

但 `reply` 仍然是模型自由生成的自然语言。

这会带来问题：

```text
回答格式不稳定
有时不清楚依据来自哪个 Source
后续 UI 不好拆分“答案 / 依据 / 资料不足”
测试时不容易判断回答是否合格
```

所以第 13 步要固定 RAG 输出格式。

---

## 2. 本次目标

优化 `_build_rag_messages()` 的 prompt，让 DeepSeek 尽量按固定结构回答：

```text
答案：
...

依据：
- [Source 1] ...
- [Source 3] ...

资料不足之处：
...
```

目标不是让模型返回严格 JSON。

当前先用 Markdown 文本格式，降低实现复杂度。

---

## 3. 不做什么

本次不做：

- 前端 UI
- JSON mode
- function calling
- Agent 工具路由
- rerank
- hybrid search
- 多文档管理
- PDF 页预览

只优化 RAG 回答格式。

---

## 4. 预计修改文件

代码：

```text
app/main.py
```

文档：

```text
docs/summary/13-rag-output-format-step.md
docs/summary/13-rag-output-format-summary.md
README.md
docs/00-project-continuation-guide.md
docs/summary/10-rag-test-result.md
```

---

## 5. 接口变化

请求结构不变：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

响应结构暂时不变：

```text
question
reply
model
collection
score_threshold
retrieved_count
source_count
sources
usage
```

变化点只在：

```text
reply 的内容格式更稳定
```

---

## 6. 验收标准

完成后应满足：

```text
1. /rag/ask 正常返回 200
2. reply 中包含“答案：”
3. reply 中包含“依据：”
4. reply 中包含“资料不足之处：”
5. 回答尽量引用 [Source N]
6. sources 结构仍保持第 12 步格式
7. score_threshold 仍然生效
8. /documents/search 不受影响
```

---

## 7. 测试方式

建议测试：

```text
GET /health
GET /openapi.json
POST /documents/search
POST /rag/ask
POST /rag/ask with score_threshold = 0.99
```

其中 `/rag/ask` 使用：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

检查：

```text
reply 格式
sources 结构
usage
```

---

## 8. 完成后的 summary 文档

完成第 13 步后，创建：

```text
docs/summary/13-rag-output-format-summary.md
```

并更新：

```text
docs/summary/13-rag-output-format-step.md
docs/summary/10-rag-test-result.md
README.md
docs/00-project-continuation-guide.md
```

