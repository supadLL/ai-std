# 企业级第 07 步完成总结：评估历史和质量治理

## 本步目标

把一次性的本地检索评估升级成可追踪的企业级质量治理能力：评估 run 入库、评估用例带知识库归属、支持历史查询、保留质量门禁结果，并支持用户对回答做 up/down 反馈。

## 已完成内容

1. 新增评估治理表：

```text
evaluation_cases
evaluation_runs
answer_feedback
```

2. 每次 `POST /evaluation/run` 都会生成独立 `run_id`，并保存：

```text
dataset
knowledge_base_id
collection
embedding_model
llm_provider / llm_model
top_k
score_threshold
hit_rate / page_hit_rate / keyword_hit_rate
quality_gate
完整 cases 结果 JSON
```

3. `evaluation_cases` 会按知识库归属同步评估用例：

```text
dataset_name
dataset_version
knowledge_base_id
case_id
question
question_type
expected pages / keywords / notes
```

4. 新增质量门禁 `quality_gate`：

```text
min_hit_rate
min_page_hit_rate
max_low_score_result_count
status: pass/fail
failures
judge_reserved: true
```

`judge_reserved` 为后续 LLM-as-a-judge 预留。

5. 新增 API：

```text
GET /evaluation/runs
GET /evaluation/runs/{run_id}
POST /feedback/answers
```

6. Web UI 评估页新增历史列表：

```text
刷新历史
最近 run 列表
点击 run 查看完整结果
```

7. Web UI 问答气泡新增反馈按钮：

```text
thumbs up
thumbs down
```

提交后写入 `answer_feedback`，同时写入审计事件 `feedback.answer`。

## 涉及文件

```text
app/evaluation.py
app/feedback.py
app/main.py
app/models.py
migrations/versions/005_evaluation_quality_governance.py
web/index.html
web/app.js
web/styles.css
tests/test_rag_evaluation.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 下一步

建议进入企业级第 08 步：部署、环境和密钥治理。重点是让 API、数据库、Qdrant、环境变量、密钥和启动方式形成更可靠的部署闭环。
