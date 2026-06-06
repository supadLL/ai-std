# 企业级第 06 步完成总结：审计日志与基础观测

## 本步目标

建立企业级平台最小可用的审计和观测骨架，让关键操作能追踪到人、租户、知识库、资源、请求 ID、耗时和 LLM usage。

## 已完成内容

1. 新增 `audit_logs` 数据表：

```text
audit_log_id
created_at
request_id
user_id / username
organization_id / workspace_id / knowledge_base_id
action
resource_type / resource_id
status
duration_ms
llm_provider / llm_model
usage_json
details_json
error_message
```

2. 新增审计写入封装：

```text
app/audit.py
```

支持写入、列表查询和基础聚合统计。

3. 新增请求 ID 和结构化日志：

```text
app/logging_config.py
X-Request-ID
```

每个请求会生成或沿用 `X-Request-ID`，响应头也会返回同一个 ID。

4. 关键操作写入审计：

```text
auth.login
settings.update
llm_profile.create
llm_profile.update
llm_profile.activate
llm_profile.delete
document.index
document.index_job.create
document.delete
document.reindex
rag.ask
agent.ask
```

5. RAG / Agent 观测字段：

```text
retrieval_ms
llm_ms
duration_ms
retrieved_count
source_count
score_threshold
llm_provider
llm_model
token usage
route / fallback
```

6. 新增接口：

```text
GET /audit-logs
GET /metrics
```

`/audit-logs` 返回最近审计事件；`/metrics` 返回文档数、索引任务状态、审计事件数、失败数和 action 聚合。

7. 新增迁移：

```text
migrations/versions/004_audit_logs.py
```

## 涉及文件

```text
app/audit.py
app/logging_config.py
app/models.py
app/main.py
migrations/versions/004_audit_logs.py
tests/test_audit.py
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

建议进入企业级第 07 步：企业级评估和质量治理。重点是让评估数据、评估运行、命中率、低分样本和质量门禁具备更强的可追踪性。
