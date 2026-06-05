# 企业级第 03 步执行目标：多租户和权限隔离

## 1. 背景

企业场景中，不同用户、团队、组织不能共享同一套文档数据。

当前项目所有文档都进入同一个 collection 和 metadata store，缺少隔离边界。

## 2. 本次目标

本次实现最小多租户隔离：

```text
1. 新增 Organization / Workspace / KnowledgeBase 概念
2. 文档归属于 knowledge_base
3. 用户通过 membership 访问知识库
4. 查询、删除、重建索引都必须校验权限
5. Qdrant payload 带 tenant_id / knowledge_base_id
6. Web UI 支持选择当前知识库
```

## 3. 不做什么

本次不做：

```text
复杂 RBAC 权限矩阵
部门树
跨组织共享
审批流
付费套餐权限
```

## 4. 预计修改文件

```text
app/models.py
app/permissions.py
app/main.py
app/vector_store.py
app/document_store.py
web/index.html
web/app.js
tests/test_permissions.py
tests/test_main_api.py
```

## 5. 接口变化建议

```text
GET /knowledge-bases
POST /knowledge-bases
GET /knowledge-bases/{knowledge_base_id}/documents
POST /knowledge-bases/{knowledge_base_id}/documents/index
POST /knowledge-bases/{knowledge_base_id}/rag/ask
```

旧接口可以保留兼容，但内部映射到默认知识库。

## 6. 验收标准

```text
1. 用户只能看到自己有权限的知识库
2. 用户不能删除其他知识库的文档
3. RAG 检索只命中当前知识库
4. Qdrant payload 中有 knowledge_base_id
5. pytest 覆盖越权访问
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_main_api.py
```
