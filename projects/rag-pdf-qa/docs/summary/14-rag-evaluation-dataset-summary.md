# 第 14 步完成总结：建立 RAG 评估问题集

本 summary 记录第 14 步实际完成内容。

对应 goal：

```text
docs/goal/14-rag-evaluation-dataset-goal.md
```

---

## 1. 本次完成了什么

完成：

```text
1. 建立 15 条 RAG 评估问题
2. 每条问题标注 expected_pages / expected_keywords / expected_source_hint
3. 覆盖概念、总结、细节、对比、流程和资料不足类问题
4. 调用 /documents/search 生成 baseline 检索记录
5. 形成 page_hit_rate / keyword_hit_rate / hit_rate 指标
```

---

## 2. 新增文件

```text
data/eval/rag_eval_cases.json
data/eval/rag_eval_result-baseline.json
docs/summary/14-rag-evaluation-dataset-summary.md
```

---

## 3. 测试数据

测试 PDF：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

索引参数：

```text
chunk_size = 800
overlap = 100
embedding_model = BAAI/bge-small-zh-v1.5
collection = rag_chunks
```

检索参数：

```text
top_k = 5
score_threshold = null
```

---

## 4. baseline 结果

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

综合命中定义：

```text
hit = hit_by_page OR hit_by_keyword
```

注意：

```text
hit_rate = 1.0000 不代表检索已经完美。
page_hit_rate = 0.8571 更适合作为后续调参时的严格指标。
```

---

## 5. 发现的问题

两条问题没有命中预期页码：

```text
Q03：GUI 智能体和 API 智能体有什么区别？
Q07：AppAgentX 的特点是什么？
```

说明当前检索存在：

```text
关键词相关但页码不理想
命名实体细节问题不够稳定
```

这会直接进入第 15 步调参重点。

---

## 6. 验证结果

已验证：

```text
测试 PDF 存在
GET /health 通过
GET /openapi.json 包含 /documents/search 和 /rag/ask
本地 .qdrant 存在 rag_chunks 数据
15 条问题均完成 /documents/search baseline
```

本次没有调用真实 DeepSeek API。

---

## 7. 后续影响

第 14 步之后，项目已经有固定评估输入。

后续第 15 步可以基于同一批问题对比：

```text
chunk_size = 500 / 800 / 1000
overlap = 80 / 100 / 150
top_k = 3 / 5 / 8
score_threshold = 0.45 / 0.5 / 0.55
```

这样调参结果才有可复盘性。

---

## 8. 下一步

下一步进入：

```text
第 15 步：评估 chunk 参数和 top_k
```

对应 goal：

```text
docs/goal/15-chunk-topk-parameter-evaluation-goal.md
```
