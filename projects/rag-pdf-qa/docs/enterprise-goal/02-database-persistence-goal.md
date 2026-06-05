# 企业级第 02 步执行目标：数据库持久化替代本地 JSON

## 1. 背景

当前项目的运行时数据主要存储在：

```text
data/documents.json
data/runtime_settings.json
```

这适合本地学习项目，但不适合企业级场景。

企业级平台需要数据库管理：

```text
用户
组织
知识库
文档 metadata
LLM profile
索引任务
评估记录
审计日志
```

## 2. 本次目标

本次建立数据库持久化基础：

```text
1. 引入 SQLAlchemy 或 SQLModel
2. 新增 PostgreSQL / SQLite 双环境配置
3. 新增数据库 session 依赖
4. 新增 Alembic migration
5. 将 User、Document metadata、LLM profile 迁移到数据库模型
6. 保留本地开发可快速启动
```

## 3. 不做什么

本次不做：

```text
复杂分库分表
读写分离
数据库性能调优
历史 JSON 自动全量迁移工具
多租户权限逻辑完整实现
```

## 4. 预计修改文件

```text
app/db.py
app/models.py
app/document_store.py
app/runtime_settings.py
app/main.py
alembic.ini
migrations/
tests/test_database.py
requirements.txt
.env.example
README.md
```

## 5. 数据表建议

```text
users
organizations
knowledge_bases
documents
llm_profiles
index_jobs
evaluation_runs
audit_logs
```

第一步可以只实现：

```text
users
documents
llm_profiles
```

## 6. 验收标准

```text
1. 应用启动时能连接数据库
2. 文档 metadata 写入数据库
3. LLM profile 写入数据库
4. JSON 文件不再作为主存储
5. 测试环境可使用 SQLite
6. pytest 通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_database.py tests\test_main_api.py
```
