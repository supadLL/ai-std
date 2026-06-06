# 企业级第 11 步完成总结：知识库版本快照

本步骤为企业级 RAG 平台补齐最小知识库版本记录能力，用于审计某一时刻的知识库文档组成，并为后续回滚、版本对比和评估回溯预留基础。

---

## 1. 本次新增能力

```text
knowledge_base_snapshots 数据表
手动创建知识库快照 API
按 knowledge base 权限隔离快照创建、列表和详情
快照记录 document_count、indexed_chunk_count、content_hash
快照保存当前文档摘要清单 documents_json
content_hash 基于排序后的文档摘要 JSON 生成，文档顺序变化不会改变同一组成的指纹
创建快照写入 audit_logs
```

---

## 2. 新增 API

| 接口 | 说明 |
|---|---|
| `POST /knowledge-bases/{knowledge_base_id}/snapshots` | 手动创建指定知识库快照 |
| `GET /knowledge-bases/{knowledge_base_id}/snapshots` | 查看指定知识库快照列表 |
| `GET /knowledge-bases/{knowledge_base_id}/snapshots/{snapshot_id}` | 查看快照详情和文档摘要 |

创建请求体：

```json
{
  "reason": "before release"
}
```

`reason` 可选，用于记录创建快照的业务原因。

---

## 3. 快照文档摘要字段

每个快照会保存当时的文档摘要：

```text
document_id
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

列表接口只返回快照摘要；详情接口返回完整 `documents` 清单。

---

## 4. 修改文件

| 文件 | 说明 |
|---|---|
| `app/models.py` | 新增 `KnowledgeBaseSnapshotModel` |
| `app/knowledge_base_snapshots.py` | 新增快照存储层、文档摘要和稳定哈希 |
| `app/main.py` | 新增快照请求/响应模型和 API 路由 |
| `migrations/versions/007_knowledge_base_snapshots.py` | 新增 Alembic 迁移 |
| `tests/test_knowledge_base_snapshots.py` | 覆盖存储层、API 和越权访问 |
| `tests/test_main_api.py` | 覆盖 OpenAPI 新端点 |
| `README.md` | 更新核心能力和接口 |
| `docs/00-project-continuation-guide.md` | 更新当前阶段、接口和支持范围 |
| `docs/enterprise-goal/README.md` | 登记 Step 11 goal |

---

## 5. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_knowledge_base_snapshots.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

阶段结果：

```text
targeted tests: 27 passed
full pytest: 81 passed
```

---

## 6. 当前边界

本步骤只实现最小可落地版本快照，不包含：

```text
定时自动快照
快照回滚
快照发布审批
chunk 级差异比较
跨环境版本发布
```

后续可以基于 `knowledge_base_snapshots` 表继续扩展版本对比、质量评估绑定和回滚工作流。
