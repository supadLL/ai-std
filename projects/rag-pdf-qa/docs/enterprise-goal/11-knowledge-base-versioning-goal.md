# 企业级第 11 步执行目标：知识库版本快照

## 1. 背景

企业团队使用 RAG 平台时，知识库会持续上传、删除、重建索引。只知道“当前有哪些文档”还不够，还需要能记录某一刻的知识库组成，便于：

```text
审计知识库变更
比较索引前后差异
回溯某次评估对应的知识库状态
后续扩展回滚和发布版本
```

路线图 Phase D 已经预留“知识库版本”，本步骤先实现最小可落地快照。

## 2. 本次目标

```text
1. 新增 knowledge_base_snapshots 表
2. 支持手动创建知识库快照
3. 快照记录 document_count、indexed_chunk_count、content_hash
4. 快照保存当时文档清单摘要
5. 提供列表和详情 API
6. API 按 knowledge base 权限隔离
7. README、续接文档和 summary 同步更新
```

## 3. 不做什么

本次不做：

```text
自动定时快照
快照回滚
快照发布审批
逐 chunk 级差异比较
跨环境版本发布
```

这些后续可以基于本次快照表继续扩展。

## 4. 预计修改文件

```text
app/models.py
app/knowledge_base_snapshots.py
app/main.py
migrations/versions/007_knowledge_base_snapshots.py
tests/test_main_api.py
tests/test_knowledge_base_snapshots.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-summary/11-knowledge-base-versioning-summary.md
```

## 5. API 设计

```text
POST /knowledge-bases/{knowledge_base_id}/snapshots
GET /knowledge-bases/{knowledge_base_id}/snapshots
GET /knowledge-bases/{knowledge_base_id}/snapshots/{snapshot_id}
```

## 6. 验收标准

```text
1. 用户只能为有权限的 knowledge base 创建和读取快照
2. 快照内容来自当前 document metadata
3. content_hash 对相同文档组成稳定
4. OpenAPI 出现新接口
5. 测试全部通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_knowledge_base_snapshots.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
