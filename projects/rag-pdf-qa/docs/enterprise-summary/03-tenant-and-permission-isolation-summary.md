# 企业级第 03 步完成总结：多租户和权限隔离

## 1. 本次完成内容

本次实现了最小多租户隔离骨架：

```text
Organization / Workspace / KnowledgeBase / Membership 数据模型
用户默认知识库初始化
知识库列表和创建接口
文档 metadata 归属 knowledge_base
Qdrant payload 写入 tenant_id / workspace_id / knowledge_base_id
文档列表、详情、删除、批量删除、重建索引按知识库校验
RAG / Agent / search 检索按 knowledge_base_id 过滤
Web UI 支持选择和创建当前知识库
```

旧接口仍然保留，例如 `/documents/index`、`/rag/ask`、`/agent/ask`，内部会映射到当前用户的默认知识库。新增显式知识库路径：

```text
GET /knowledge-bases
POST /knowledge-bases
GET /knowledge-bases/{knowledge_base_id}/documents
POST /knowledge-bases/{knowledge_base_id}/documents/index
POST /knowledge-bases/{knowledge_base_id}/documents/search
POST /knowledge-bases/{knowledge_base_id}/rag/ask
POST /knowledge-bases/{knowledge_base_id}/agent/ask
```

## 2. 关键设计

本步没有做复杂 RBAC，只做最小 membership 校验：

```text
用户必须拥有某个 knowledge_base 的 membership 才能访问
admin 默认获得 kb_default
普通用户默认获得自己的个人 knowledge_base
新建 knowledge_base 后创建者自动成为 owner
```

去重策略从全局 content_hash 调整为：

```text
同一 knowledge_base 内 content_hash 去重
不同 knowledge_base 可以上传相同内容
```

## 3. 修改文件

```text
app/models.py
app/permissions.py
app/document_store.py
app/vector_store.py
app/evaluation.py
app/main.py
app/db.py
web/index.html
web/app.js
web/styles.css
migrations/versions/002_tenant_knowledge_base_isolation.py
tests/test_permissions.py
tests/test_main_api.py
tests/test_agent.py
tests/test_rag_evaluation.py
README.md
docs/00-project-continuation-guide.md
```

## 4. 验证结果

已通过：

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp
```

结果：

```text
58 passed
```

说明：

```text
本机默认 Temp 目录存在权限问题，所以 pytest 使用项目内 .pytest_tmp 作为 basetemp。
```

## 5. 下一步

下一步进入企业级第 04 步：

```text
异步索引任务
索引任务状态
大文件入库不阻塞请求
失败重试和任务记录
```
