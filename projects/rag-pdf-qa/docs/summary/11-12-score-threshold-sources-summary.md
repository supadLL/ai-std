# 第 11/12 步完成总结：score_threshold 与 sources 结构优化

本 summary 记录第 11、12 步实际完成内容。

对应 goal：

```text
本次是在建立 goal/summary 规范前完成的，因此没有独立 goal 文件。
后续新步骤应先写 docs/goal/*.md。
```

---

## 1. 本次完成了什么

完成两项能力：

```text
第 11 步：/rag/ask 支持 score_threshold 低分过滤
第 12 步：/rag/ask sources 返回结构优化
```

---

## 2. 代码改动

主要文件：

```text
app/main.py
```

新增能力：

```text
RagAskRequest.score_threshold
RagAskResponse.score_threshold
RagAskResponse.retrieved_count
RagAskResponse.source_count
RagSourceResponse
_filter_results_by_score()
_to_rag_source_response()
```

---

## 3. 接口变化

`POST /rag/ask` 请求现在支持：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

响应新增：

```text
score_threshold
retrieved_count
source_count
```

sources 结构变为：

```json
{
  "source_id": 1,
  "score": 0.5638,
  "filename": "GUIagent.pdf",
  "page_number": 23,
  "chunk_id": 23,
  "preview": "..."
}
```

`/documents/search` 不变，仍返回完整 `text`，用于调试检索质量。

---

## 4. 文档改动

新增：

```text
docs/summary/11-rag-score-threshold-step.md
docs/summary/12-rag-sources-response-step.md
```

更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
docs/summary/09-rag-test-spec.md
docs/summary/10-rag-test-result.md
```

---

## 5. 验证结果

已执行：

```text
python -m compileall app
GET /health
GET /openapi.json
TestClient /rag/ask with score_threshold = 0.5
HTTP /rag/ask with score_threshold = 0.99
```

验证结果：

```text
compileall 通过
/health ok
/openapi.json 包含 /rag/ask
OpenAPI schema 包含 score_threshold
OpenAPI schema 包含 RagSourceResponse
score_threshold = 0.5 返回 200
score_threshold = 0.99 返回 404
404 detail 明确提示降低 score_threshold 或换问题
```

---

## 6. 遇到的问题

实现过程中发现一个 bug：

```text
retrieved_results 变量名没有完全替换，导致 NameError
```

已修复。

还遇到 PowerShell 中文输出编码问题：

```text
中文和特殊符号在直接打印 JSON 时可能触发 UnicodeEncodeError
```

后续测试脚本建议：

```python
json.dumps(data, ensure_ascii=True)
```

---

## 7. 后续影响

这两步让 RAG 回答更适合后续 UI：

```text
source_id 可用于引用
preview 可用于右侧 sources 面板
source_count/retrieved_count 可用于调试
score_threshold 可减少低相关 chunk 进入 prompt
```

---

## 8. 下一步建议

下一步建议进入：

```text
第 13 步：固定 RAG 输出格式
```

对应 goal：

```text
docs/goal/13-rag-output-format-goal.md
```

