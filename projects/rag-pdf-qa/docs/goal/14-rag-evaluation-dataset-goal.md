# 第 14 步执行目标：建立 RAG 评估问题集

这一步的目标是：

> 先建立一份可复用的 RAG 测试问题集，让后续调参和改 prompt 都有对比依据。

状态：已完成。

完成记录：

```text
docs/summary/14-rag-evaluation-dataset-summary.md
data/eval/rag_eval_cases.json
data/eval/rag_eval_result-baseline.json
```

---

## 1. 背景

当前项目已经能完成最小 RAG 闭环：

```text
PDF -> chunk -> embedding -> Qdrant -> search -> DeepSeek answer
```

但现在判断效果主要靠临时提问。

这会导致：

```text
每次测试问题不一致
调参前后无法对比
很难判断检索到底有没有变好
新对话接手时不知道用什么问题验收
```

所以第 14 步要先建立评估问题集。

---

## 2. 本次目标

建立一份 10-20 条的 RAG 评估用例，至少包含：

```text
question
expected_keywords
expected_pages
expected_source_hint
question_type
notes
```

建议问题类型覆盖：

```text
概念解释
流程总结
细节查找
对比类问题
资料不足类问题
```

这一阶段重点评估：

```text
/documents/search 的检索命中情况
```

不是优先评估 LLM 文采。

---

## 3. 不做什么

本次不做：

- 修改 RAG prompt
- 修改 embedding 模型
- 修改 chunk 逻辑
- 新增 UI
- 新增 Agent
- 引入自动评测大框架

---

## 4. 预计修改文件

建议新增：

```text
docs/summary/14-rag-evaluation-dataset-summary.md
```

可选新增：

```text
data/eval/rag_eval_cases.json
data/eval/rag_eval_result-baseline.json
```

需要同步更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/09-rag-test-spec.md
docs/summary/10-rag-test-result.md
```

---

## 5. 接口变化

本次不要求新增接口。

主要使用已有接口：

```text
POST /documents/search
POST /rag/ask
```

---

## 6. 验收标准

完成后应满足：

```text
1. 至少有 10 条评估问题
2. 每条问题有预期命中页码或预期关键词
3. 至少包含 1 条资料不足类问题
4. 能说明每条问题为什么适合作为测试用例
5. 有一份 baseline 测试记录
6. README 和 00 号文档能指向这一步产物
```

---

## 7. 测试方式

建议流程：

```text
1. 确认 Qdrant 已经有测试 PDF 的索引
2. 逐条调用 /documents/search
3. 记录 top_k 返回的 page_number、chunk_id、score
4. 判断是否命中 expected_pages 或 expected_keywords
5. 再抽样调用 /rag/ask 看回答是否引用正确 sources
```

建议记录字段：

```text
question
top_k
score_threshold
hit
matched_source_id
matched_page_number
comment
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/14-rag-evaluation-dataset-summary.md
```

并更新：

```text
docs/summary/09-rag-test-spec.md
docs/summary/10-rag-test-result.md
README.md
docs/00-project-continuation-guide.md
```
