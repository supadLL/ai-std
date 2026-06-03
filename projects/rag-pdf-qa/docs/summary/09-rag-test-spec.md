# 第 9 步测试规范：RAG 检索与问答质量评估

这份文档定义当前最小 RAG 系统的测试方式。

目标是：

> 用固定样例 PDF 和固定问题，验证索引、检索、RAG 回答是否稳定，并为后续调参提供基线。

---

## 1. 测试范围

当前测试覆盖：

```text
GET /health
GET /openapi.json
POST /documents/index
POST /documents/search
POST /rag/ask
```

暂不覆盖：

```text
OCR
Word / Markdown / 表格文档
多文档管理
UI 页面
Agent 工具路由
```

---

## 2. 测试环境

服务地址：

```text
http://127.0.0.1:8000
```

启动方式：

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

要求：

```text
/docs 页面可以访问
/openapi.json 中包含 /rag/ask
.env 已配置 DEEPSEEK_API_KEY
```

---

## 3. 测试样例文件

当前使用：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

文件类型：

```text
文本型 PDF
```

测试索引参数：

```text
chunk_size = 800
overlap = 100
limit/top_k = 5
```

---

## 4. 测试流程

### 4.1 健康检查

请求：

```text
GET /health
```

通过标准：

```json
{
  "status": "ok"
}
```

### 4.2 OpenAPI 检查

请求：

```text
GET /openapi.json
```

通过标准：

```text
paths 中包含 /rag/ask
```

### 4.3 文档索引

请求：

```text
POST /documents/index
```

表单参数：

```text
file = GUIagent.pdf
chunk_size = 800
overlap = 100
```

通过标准：

```text
HTTP 200
chunk_count > 0
indexed_count = chunk_count
dimension = 512
collection = rag_chunks
```

### 4.4 纯检索测试

请求：

```text
POST /documents/search
```

测试问题：

| 编号 | 问题 | limit |
|---|---|---:|
| Q1 | GUI Agent 的核心流程是什么？ | 5 |
| Q2 | GUI Agent 为什么需要观察环境？ | 5 |
| Q3 | GUI Agent 和传统 RPA 有什么区别？ | 5 |

通过标准：

```text
HTTP 200
每个问题返回 5 个结果
结果包含 page_number、chunk_id、score、text
top results 和问题语义相关
```

### 4.5 RAG 问答测试

请求：

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

通过标准：

```text
HTTP 200
reply 非空
retrieved_count > 0
sources 数量 > 0
sources 包含 source_id 和 preview
usage 非空
回答中尽量引用 Source
回答没有明显脱离 sources 编造
```

---

## 5. 记录指标

每次测试记录：

| 指标 | 说明 |
|---|---|
| status_code | 接口状态码 |
| elapsed_ms | 请求耗时 |
| chunk_count | 切分出来的 chunk 数 |
| indexed_count | 写入 Qdrant 的 chunk 数 |
| dimension | embedding 向量维度 |
| top_k | 检索返回数量 |
| top1_score | 第一条检索分数 |
| top1_page | 第一条命中页码 |
| score_threshold | RAG 低分过滤阈值 |
| retrieved_count | Qdrant 原始返回数量 |
| source_count | RAG 使用的 sources 数量 |
| token usage | DeepSeek token 用量 |

---

## 6. 质量判断标准

当前不是只看接口是否 200。

还要看：

```text
检索是否相关
top1 是否合理
top5 是否覆盖关键信息
RAG 回答是否基于 sources
RAG 回答是否承认资料不足
```

如果 search 不相关，优先调：

```text
chunk_size
overlap
embedding 模型
top_k
score_threshold
```

如果 search 相关但 RAG 回答不好，再调：

```text
RAG prompt
输出格式
sources 编号
回答约束
```

---

## 7. 后续扩展测试

后续可以补：

```text
score_threshold 测试
sources source_id / preview 结构测试
不同 chunk_size / overlap 对比
top_k = 3 / 5 / 8 对比
多 PDF 索引测试
Markdown / Word / 表格文档测试
UI 页面端到端测试
Agent 工具路由测试
```

