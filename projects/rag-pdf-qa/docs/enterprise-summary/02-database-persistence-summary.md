# 企业级第 02 步完成总结：数据库持久化替代本地 JSON

## 1. 本次完成了什么

本次建立企业级数据库持久化基础。

新增能力：

```text
SQLAlchemy 数据库基础设施
SQLite 默认 DATABASE_URL
PostgreSQL DATABASE_URL 预留
users 表
documents 表
runtime_settings 表
llm_profiles 表
Alembic 基础迁移文件
```

当前这些数据不再以本地 JSON 作为主存储：

```text
users
documents metadata
runtime settings
LLM profiles
```

## 2. 改动文件

代码：

```text
app/db.py
app/models.py
app/user_store.py
app/document_store.py
app/runtime_settings.py
app/config.py
app/main.py
app/auth.py
```

迁移：

```text
alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/001_enterprise_persistence.py
```

测试和文档：

```text
tests/test_database.py
tests/test_auth.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-summary/02-database-persistence-summary.md
```

## 3. 配置变化

新增：

```text
DATABASE_URL=sqlite:///data/app.db
```

本地开发默认使用 SQLite。后续可以切换为 PostgreSQL：

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/rag
```

## 4. 验证结果

已通过：

```powershell
python -m compileall app tests
```

当前机器没有项目 `.venv`，系统 Python 也没有安装 `pytest`、`fastapi` 和 `SQLAlchemy`，所以未能运行完整 pytest。

待本地环境恢复后，建议优先运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests\test_database.py tests\test_auth.py tests\test_main_api.py
```

## 5. 后续影响

后续第 03 步可以基于数据库继续实现：

```text
organizations
knowledge_bases
memberships
document ownership
tenant-aware vector payload
permission checks
```

## 6. 下一步建议

下一步进入：

```text
企业级第 03 步：多租户和权限隔离
```

重点是确定新用户、文档和知识库的归属规则，再决定是否开放局域网成员自助注册。
## 7. 补充验证结果

后续已创建 `.venv` 并安装 `requirements.txt`，完整回归测试通过：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
56 passed
```
