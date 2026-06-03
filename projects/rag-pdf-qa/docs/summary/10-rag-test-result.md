# 第 10 步测试结果：最小 RAG 检索与问答基线

本次测试目标：

> 按照 [`09-rag-test-spec.md`](09-rag-test-spec.md) 对当前最小 RAG 系统做一轮自主测试，形成后续调参基线。

测试时间：

```text
2026-06-03
```

服务地址：

```text
http://127.0.0.1:8000
```

测试文件：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

---

## 1. 总体结论

本次测试结论：

```text
基础链路通过。
PDF 可以成功索引到 Qdrant。
/documents/search 可以返回检索结果。
/rag/ask 可以调用 DeepSeek 并返回回答、sources 和 usage。
```

但也暴露出一个质量问题：

```text
对于“GUI Agent 的核心流程是什么？”这类泛问题，top1 命中不一定是最理想的总览页，而是命中了某些技术分支页面。
```

说明后续需要继续做：

```text
检索评估
chunk 参数调优
score_threshold
sources 结构优化
RAG prompt 输出格式固定
```

---

## 2. 健康检查

接口：

```text
GET /health
```

结果：

| 状态码 | 耗时 |
|---:|---:|
| 200 | 6.22 ms |

返回：

```json
{
  "status": "ok"
}
```

结论：

```text
通过
```

---

## 3. OpenAPI 检查

接口：

```text
GET /openapi.json
```

结果：

| 状态码 | 耗时 | paths 数量 | 是否包含 /rag/ask |
|---:|---:|---:|---|
| 200 | 3.22 ms | 8 | 是 |

结论：

```text
通过，Swagger Docs 页面可以测试 /rag/ask。
```

---

## 4. 文档索引测试

接口：

```text
POST /documents/index
```

参数：

```text
chunk_size = 800
overlap = 100
```

结果：

| 字段 | 值 |
|---|---:|
| 状态码 | 200 |
| 耗时 | 6383.64 ms |
| page_count | 43 |
| chunk_count | 43 |
| indexed_count | 43 |
| dimension | 512 |

其他信息：

```text
filename = GUIagent.pdf
collection = rag_chunks
local_path = .qdrant
```

结论：

```text
通过。PDF 已成功解析、切分、向量化并写入本地 Qdrant。
```

---

## 5. 检索测试结果

统一参数：

```text
limit/top_k = 5
```

### Q1：GUI Agent 的核心流程是什么？

结果：

| rank | score | page | chunk_id | 内容摘要 |
|---:|---:|---:|---:|---|
| 1 | 0.5638 | 23 | 23 | DistRL，强化学习和分布式训练 |
| 2 | 0.5533 | 12 | 12 | Mobile-Agent-v2，多智能体系统 |
| 3 | 0.5483 | 13 | 13 | AppAgentX，任务执行过程中的行为学习 |
| 4 | 0.5468 | 27 | 27 | UI-NEXUS，复杂任务测试基准 |
| 5 | 0.5455 | 16 | 16 | GUI 智能体部署和开源项目 |

判断：

```text
部分相关，但 top1 不是“核心流程”总览页。
这个问题偏泛，检索结果更偏技术分支和框架代表。
```

### Q2：GUI Agent 为什么需要观察环境？

结果：

| rank | score | page | chunk_id | 内容摘要 |
|---:|---:|---:|---:|---|
| 1 | 0.5527 | 22 | 22 | DigiRL，适应动态环境 |
| 2 | 0.5460 | 21 | 21 | 现实环境动态变化，网页布局、软件更新等 |
| 3 | 0.5299 | 30 | 30 | 部署环境安全风险 |
| 4 | 0.5226 | 19 | 19 | 静态场景下监督微调 |
| 5 | 0.5197 | 23 | 23 | DistRL，动态场景强化学习 |

判断：

```text
相关性较好。
page 21 和 page 22 明确命中了“动态环境”和“适应环境”的主题。
```

### Q3：GUI Agent 和传统 RPA 有什么区别？

结果：

| rank | score | page | chunk_id | 内容摘要 |
|---:|---:|---:|---:|---|
| 1 | 0.5390 | 7 | 7 | GUI vs API，GUI 智能体点击、输入、滑动等 |
| 2 | 0.4974 | 12 | 12 | Mobile-Agent 系列 |
| 3 | 0.4908 | 13 | 13 | AppAgent 系列 |
| 4 | 0.4868 | 11 | 11 | GUI Agent 技术分支 |
| 5 | 0.4831 | 4 | 4 | AGI 阶段和智能体背景 |

判断：

```text
相关性较好。
虽然文档里未必直接写“RPA”，但 top1 命中了 GUI vs API 的背景页，适合回答差异。
```

---

## 6. RAG 问答测试

接口：

```text
POST /rag/ask
```

问题：

```text
GUI Agent 的核心流程是什么？
```

参数：

```text
limit = 5
```

结果：

| 字段 | 值 |
|---|---:|
| 状态码 | 200 |
| 耗时 | 5196.09 ms |
| source_count | 5 |
| prompt_tokens | 744 |
| completion_tokens | 360 |
| total_tokens | 1104 |

回答摘要：

```text
模型认为资料中没有统一的“核心流程”定义，并基于 sources 总结了 Mobile-Agent-v2、DistRL、AppAgentX 等代表性实现。
```

判断：

```text
通过。
回答基本基于 sources，并且没有强行编造统一流程。
但由于检索结果偏技术分支，最终回答也偏“代表性实现总结”，不是理想的“核心流程总览”。
```

---

## 7. 本次发现的问题

### 7.1 泛问题检索不够稳定

例如：

```text
GUI Agent 的核心流程是什么？
```

top1 命中了 DistRL 页面，而不是更概括的流程介绍。

可能原因：

```text
chunk 粒度按页切分，缺少章节级结构
问题太泛
embedding 对“核心流程”理解不一定对应总览页
没有 rerank
没有 hybrid search
```

### 7.2 score 整体偏接近

几个结果分数差距不大：

```text
0.5638
0.5533
0.5483
0.5468
0.5455
```

说明：

```text
仅靠当前向量分数很难判断哪个 chunk 最应该排第一。
```

### 7.3 RAG 回答质量依赖检索结果

RAG 回答没有明显脱离 sources。

但 sources 偏技术分支时，回答也会跟着偏。

这说明后续优先优化：

```text
检索质量
```

而不是只改 prompt。

---

## 8. 下一步建议

建议后续按这个顺序做：

```text
1. 固定 RAG 输出格式：答案 / 依据 / 资料不足之处
2. 准备 10-20 个问题，人工标注期望页码
3. 测试 top_k = 3 / 5 / 8 的差异
4. 测试 chunk_size = 500 / 800 / 1000 的差异
5. 考虑增加章节标题或 heading_path 元数据
```

当前最适合进入的下一步：

```text
固定 RAG 输出格式
```

该建议已在第 13 步完成。

因为第 11/12 步已经完成：

```text
score_threshold 低分过滤
sources source_id / preview 展示结构
```

---

## 9. 第 11/12 步补充验证结果

本次补充验证内容：

```text
第 11 步：score_threshold 低分过滤
第 12 步：sources 返回结构优化
```

### 9.1 TestClient 结构验证

为了避免重复消耗 DeepSeek token，结构验证时 mock 了 `DeepSeekClient.chat_messages()`。

请求：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

结果：

| 字段 | 值 |
|---|---:|
| 状态码 | 200 |
| retrieved_count | 5 |
| source_count | 5 |
| score_threshold | 0.5 |

返回的 `sources` 已包含：

```text
source_id
score
filename
page_number
chunk_id
preview
```

并且 `/rag/ask` 的 sources 不再直接返回完整 `text`。

结论：

```text
第 12 步 sources 返回结构优化通过。
```

### 9.2 高阈值过滤验证

请求：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.99
}
```

HTTP 验证结果：

| 字段 | 值 |
|---|---:|
| 状态码 | 404 |

返回：

```json
{
  "detail": "No document chunks met score_threshold. Lower score_threshold or try another question."
}
```

结论：

```text
第 11 步 score_threshold 过滤逻辑通过。
当阈值过高导致没有 sources 时，接口不会继续调用 DeepSeek。
```

### 9.3 当前下一步

第 11/12 步完成后，当前最适合继续做：

```text
固定 RAG 输出格式
```

建议让 `/rag/ask` 的 reply 更稳定地按以下格式输出：

```text
答案
依据
资料不足之处
```

第 13 步已经完成上述固定输出格式。

---

## 10. 第 14 步补充验证结果

第 14 步已经建立固定 RAG 评估问题集：

```text
data/eval/rag_eval_cases.json
```

并生成 baseline 检索结果：

```text
data/eval/rag_eval_result-baseline.json
```

本次只调用：

```text
POST /documents/search
```

没有调用 DeepSeek API。

baseline 汇总：

| 指标 | 值 |
|---|---:|
| case_count | 15 |
| scored_case_count | 14 |
| insufficient_context_case_count | 1 |
| hit_count | 14 |
| hit_rate | 1.0000 |
| page_hit_count | 12 |
| page_hit_rate | 0.8571 |
| keyword_hit_count | 14 |
| keyword_hit_rate | 1.0000 |

页码未命中的问题：

| case_id | 问题 | 预期页码 | top_k 页码 |
|---|---|---|---|
| Q03 | GUI 智能体和 API 智能体有什么区别？ | 7 | 38, 5, 9, 6, 37 |
| Q07 | AppAgentX 的特点是什么？ | 13 | 7, 14, 23, 9, 5 |

当前下一步：

```text
第 18 步：支持 Markdown 和 txt 文档入库
```

对应 goal：

```text
docs/goal/18-markdown-txt-loader-goal.md
```

---

## 11. 第 15/16 步补充验证结果

第 15 步已经完成 chunk/top_k 参数评估：

```text
data/eval/chunk_topk_eval_result.json
data/eval/chunk_topk_eval_result.md
```

当前推荐：

```text
chunk_size = 800
overlap = 100
top_k = 5
```

第 16 步已经新增知识库文档管理接口：

```text
GET /documents
GET /documents/{document_id}
DELETE /documents/{document_id}
```

已运行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
pytest 8 passed
```

---

## 12. 第 17 步补充验证结果

第 17 步已经新增：

```text
content_hash
duplicate check
reindex=true
```

`POST /documents/index` 重复上传同一份文件时，默认返回：

```text
is_duplicate = true
indexed = false
```

使用 `reindex=true` 时，会先删除旧 chunks，再重新索引。

已运行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
pytest 10 passed
```

