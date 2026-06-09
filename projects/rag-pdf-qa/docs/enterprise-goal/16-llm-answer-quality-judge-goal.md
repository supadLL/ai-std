# 企业级第 16 步执行目标：LLM-as-a-judge 回答质量评估

## 1. 背景

第 07 步已经把检索评估历史、质量门禁和用户反馈入库，并在 `quality_gate` 中预留了 `judge_reserved`。

当前系统仍然只能评估检索命中，不能对某一次 RAG/Agent 回答本身进行结构化质量判断。企业落地时，需要能把“这次回答是否基于来源、是否回答了问题、是否存在幻觉风险”记录下来，作为后续质检、演示和回归优化的依据。

## 2. 本次目标

```text
1. 新增 LLM-as-a-judge 最小 API
2. Judge 请求包含 question、answer、sources 和可选 knowledge_base_id / route
3. 使用当前启用的 LLM profile 生成结构化 JSON 评分
4. 评分结果包含 groundedness、answer_quality、completeness、risk_level、verdict 和 rationale
5. Judge 结果写入数据库，保留当前用户、知识库、provider/model、usage 和 sources 摘要
6. Judge 调用写入 audit log
7. OpenAPI、单元测试和文档更新
```

## 3. 不做什么

本步骤不做：

```text
批量评测任务
人工标注工作流
多 Judge 模型投票
自动拦截线上回答
Web UI 图形化 Judge 面板
复杂事实核查引擎
```

## 4. 预期接口

```text
POST /evaluation/judge-answer
```

请求示例：

```json
{
  "knowledge_base_id": "kb_default",
  "route": "rag",
  "question": "What is RAG?",
  "answer": "RAG retrieves context before answering.",
  "sources": [
    {
      "source_id": 1,
      "filename": "demo.md",
      "page_number": 1,
      "chunk_id": 1,
      "preview": "RAG retrieves relevant context..."
    }
  ]
}
```

## 5. 预期修改文件

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

## 6. 验收标准

```text
1. POST /evaluation/judge-answer 返回结构化评分
2. LLM 返回纯 JSON 或带代码围栏 JSON 都能解析
3. Judge 记录写入 answer_quality_judgements 表
4. Judge 调用写入 audit action=evaluation.judge_answer
5. 未配置 LLM API Key 时返回明确错误，不写假评分
6. pytest tests/test_main_api.py 通过
7. pytest 全量通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
