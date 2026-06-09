# 企业级第 16 步完成总结：LLM-as-a-judge 回答质量评估

## 完成内容

本步骤把第 07 步预留的 `judge_reserved` 落成最小可用能力：

- 新增 `POST /evaluation/judge-answer`。
- 请求包含 `question`、`answer`、`sources`、可选 `knowledge_base_id` 和 `route`。
- 使用当前启用的 LLM profile 做单次回答质量评估。
- 支持解析纯 JSON 或 Markdown 代码围栏中的 JSON。
- 返回 `groundedness`、`answer_quality`、`completeness`、`risk_level`、`verdict`、`rationale` 和 token `usage`。
- 新增 `answer_quality_judgements` 表保存 Judge 结果。
- Judge 调用写入审计事件 `evaluation.judge_answer`。
- 未配置 LLM API Key 时返回明确错误，不写入虚假评分。

## 涉及文件

```text
app/models.py
app/evaluation_judge.py
app/main.py
migrations/versions/008_answer_quality_judgements.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/16-llm-answer-quality-judge-summary.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤只做单次回答 Judge，不做批量评测任务、人工标注流、多模型投票、线上自动拦截或 Web UI 图形化 Judge 面板。
