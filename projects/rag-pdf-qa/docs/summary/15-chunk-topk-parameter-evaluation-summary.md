# 第 15 步完成总结：chunk 参数和 top_k 评估

本 summary 记录第 15 步实际完成内容。

---

## 1. 本次完成了什么

完成内容：

```text
1. 新增本地参数评估脚本
2. 用第 14 步问题集比较 3 组 chunk 参数
3. 比较 top_k=3 和 top_k=5
4. 生成 JSON 和 Markdown 评估结果
5. 给出当前推荐默认参数
```

---

## 2. 改动文件

新增：

```text
scripts/evaluate_chunk_topk.py
data/eval/chunk_topk_eval_result.json
data/eval/chunk_topk_eval_result.md
docs/summary/15-chunk-topk-parameter-evaluation-summary.md
```

更新：

```text
docs/goal/15-chunk-topk-parameter-evaluation-goal.md
README.md
docs/00-project-continuation-guide.md
docs/summary/10-rag-test-result.md
```

---

## 3. 接口变化

第 15 步不新增接口。

已有接口保持不变：

```text
POST /documents/index
POST /documents/search
POST /rag/ask
```

---

## 4. 验证结果

已运行：

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_chunk_topk.py
```

生成结果：

```text
data/eval/chunk_topk_eval_result.json
data/eval/chunk_topk_eval_result.md
```

推荐参数：

```text
chunk_size = 800
overlap = 100
top_k = 5
```

推荐理由：

```text
当前几组参数命中率一致。
top_k=5 的 page_hit_rate 高于 top_k=3。
800/100 是当前默认值，保留较完整上下文，不需要为了同等命中率改成更小 chunk。
```

---

## 5. 遇到的问题

评估脚本第一次直接运行时出现：

```text
ModuleNotFoundError: No module named 'app'
```

原因：

```text
直接运行 scripts/evaluate_chunk_topk.py 时，Python import 路径指向 scripts 目录。
```

已处理：

```text
脚本开头显式把项目根目录加入 sys.path。
```

---

## 6. 后续影响

第 15 步让后续调参有了可复用方式：

```text
修改 chunk 参数
运行 scripts/evaluate_chunk_topk.py
对比 data/eval/chunk_topk_eval_result.*
```

这样后续支持 Markdown、docx、表格和 OCR 后，也可以复用同样思路建立新数据集。

---

## 7. 下一步建议

继续第 16 步：

```text
新增知识库文档管理能力
```

核心是让系统知道当前索引了哪些文档，并支持按 `document_id` 删除。
