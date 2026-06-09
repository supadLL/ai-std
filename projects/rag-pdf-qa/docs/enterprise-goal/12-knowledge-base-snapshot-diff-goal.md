# 企业级第 12 步执行目标：知识库快照差异比较

## 1. 背景

第 11 步已经能为知识库保存某一时刻的版本快照，记录文档数量、索引 chunk 数、稳定 `content_hash` 和文档摘要清单。

但只保存快照还不够，企业用户还需要知道：

```text
两次快照之间新增了哪些文档
删除了哪些文档
哪些文档内容或关键 metadata 发生变化
是否存在未变化的文档
```

本步骤在不引入回滚和审批复杂度的前提下，先实现文档级快照差异比较。

## 2. 本次目标

```text
1. 新增快照文档级 diff 计算逻辑
2. 支持同一 knowledge base 内两个快照比较
3. diff 返回 added / removed / changed / unchanged_count
4. changed 返回 before / after 文档摘要和 changed_fields
5. API 按 knowledge base 权限隔离
6. OpenAPI 出现新接口
7. README、续接文档和 enterprise summary 同步更新
```

## 3. 不做什么

本次不做：

```text
快照回滚
快照发布审批
chunk 级差异比较
跨 knowledge base 比较
跨环境发布比较
Web UI 图形化对比页面
```

## 4. 预计修改文件

```text
app/knowledge_base_snapshots.py
app/main.py
tests/test_knowledge_base_snapshots.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/12-knowledge-base-snapshot-diff-summary.md
```

## 5. API 设计

```text
GET /knowledge-bases/{knowledge_base_id}/snapshots/{base_snapshot_id}/diff/{target_snapshot_id}
```

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

## 6. 验收标准

```text
1. 用户只能比较自己有权限的 knowledge base 快照
2. 两个快照必须属于同一个 knowledge base
3. 新增文档进入 added_documents
4. 删除文档进入 removed_documents
5. 同 document_id 但 content_hash 或关键 metadata 变化进入 changed_documents
6. 相同文档计入 unchanged_count
7. 测试全部通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_knowledge_base_snapshots.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
