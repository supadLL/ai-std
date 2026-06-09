# 企业级第 12 步完成总结：知识库快照差异比较

本步骤基于第 11 步的知识库快照能力，补齐两个快照之间的文档级差异比较，让企业用户可以快速判断某次知识库版本变化包含哪些新增、删除和变更。

---

## 1. 本次新增能力

```text
快照文档级 diff 纯函数
同一 knowledge base 内两个快照比较 API
added_documents / removed_documents / changed_documents / unchanged_count
changed_documents 返回 before / after 文档摘要和 changed_fields
API 继续复用 knowledge base membership 权限隔离
OpenAPI 暴露新 diff 接口
```

---

## 2. 新增 API

| 接口 | 说明 |
|---|---|
| `GET /knowledge-bases/{knowledge_base_id}/snapshots/{base_snapshot_id}/diff/{target_snapshot_id}` | 比较两个知识库快照的文档级差异 |

响应核心字段：

```text
knowledge_base_id
base_snapshot_id
target_snapshot_id
base_content_hash
target_content_hash
added_count
removed_count
changed_count
unchanged_count
added_documents
removed_documents
changed_documents
```

---

## 3. 差异判断规则

```text
document_id 只存在于 target 快照 -> added_documents
document_id 只存在于 base 快照 -> removed_documents
document_id 同时存在但关键摘要字段不同 -> changed_documents
document_id 同时存在且关键摘要字段一致 -> unchanged_count
```

changed 对比字段：

```text
filename
file_type
content_hash
chunk_count
indexed_count
source_file_size
source_storage_backend
source_storage_key
indexed_at
```

---

## 4. 修改文件

| 文件 | 说明 |
|---|---|
| `app/knowledge_base_snapshots.py` | 新增 `diff_snapshots`、diff dataclass 和 changed 字段规则 |
| `app/main.py` | 新增 diff 响应模型和 API 路由 |
| `tests/test_knowledge_base_snapshots.py` | 覆盖纯 diff、API diff 和越权 diff |
| `tests/test_main_api.py` | 覆盖 OpenAPI diff 路径 |
| `README.md` | 更新核心能力和接口 |
| `docs/00-project-continuation-guide.md` | 更新当前阶段、接口和支持范围 |
| `docs/enterprise-goal/12-knowledge-base-snapshot-diff-goal.md` | 第 12 步目标 |
| `docs/enterprise-goal/README.md` | 登记 Step 12 goal |

---

## 5. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_knowledge_base_snapshots.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

阶段结果：

```text
targeted tests: 29 passed
full pytest: 83 passed
```

---

## 6. 当前边界

本步骤只做文档级快照差异比较，不包含：

```text
快照回滚
快照发布审批
chunk 级差异比较
跨 knowledge base 比较
跨环境发布比较
Web UI 图形化对比页面
```

后续可以在此基础上继续扩展 Web UI 对比面板、版本发布说明生成和快照回滚工作流。
