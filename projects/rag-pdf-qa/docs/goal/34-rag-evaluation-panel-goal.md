# 第 34 步执行目标：RAG 评估脚本与评估面板

这一步的目标是：

> 把当前已有的评估问题集，从文档记录升级为可运行、可复测、可展示的 RAG 质量评估能力。

---

## 1. 背景

当前项目已经有 RAG 评估问题和 chunk/top_k baseline 记录，但更多是文档层面的记录。

后续如果想证明项目质量，需要能回答：

```text
当前检索命中率如何？
不同 top_k 差异如何？
不同 score_threshold 是否影响回答？
回答是否引用了正确 sources？
```

---

## 2. 本次目标

本次完成：

```text
1. 新增可运行评估脚本
2. 从固定评估数据集读取问题
3. 批量调用 /documents/search 或内部检索函数
4. 记录命中 source、score、chunk_id、是否命中预期文档
5. 输出 JSON / Markdown 评估报告
6. Web UI 增加最小评估结果查看入口
```

---

## 3. 不做什么

本次不做：

- 大规模自动标注
- 复杂 LLM-as-a-judge
- 成本较高的批量 DeepSeek 调用
- 在线排行榜
- 多模型横评

---

## 4. 需要修改的文件

预计新增：

```text
scripts/run_rag_evaluation.py
data/evaluation_questions.json
```

预计修改：

```text
app/main.py
web/index.html
web/app.js
web/styles.css
README.md
docs/00-project-continuation-guide.md
```

测试：

```text
tests/test_rag_evaluation.py
```

完成后新增：

```text
docs/summary/34-rag-evaluation-panel-summary.md
```

---

## 5. 接口变化

可选新增：

```text
GET /evaluation/questions
POST /evaluation/run
GET /evaluation/latest
```

如果先做脚本版，可以暂不新增接口。

---

## 6. 验收标准

完成后应满足：

```text
1. 评估脚本可以独立运行
2. 能输出每个问题的 top_k 命中结果
3. 能保存最近一次评估结果
4. Web UI 能查看评估摘要
5. 不会默认调用 DeepSeek 消耗 token
6. pytest 通过
```

---

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

脚本测试：

```powershell
.\.venv\Scripts\python.exe scripts\run_rag_evaluation.py
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
查看评估结果入口
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/34-rag-evaluation-panel-summary.md
```
