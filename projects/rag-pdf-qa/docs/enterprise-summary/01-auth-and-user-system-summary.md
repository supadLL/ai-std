# 企业级第 01 步完成总结：登录鉴权与用户体系

## 1. 本次完成了什么

本次完成企业级改造的第一步：建立最小用户身份体系。

新增能力：

```text
初始化管理员
用户名密码登录
密码哈希存储
Bearer token 签发与校验
当前用户接口
退出登录接口
核心 API 登录保护
Web UI 登录态
Swagger Docs Bearer token 授权方案
```

当前仍使用本地 JSON 用户存储：

```text
data/users.json
```

这是刻意保留的轻量实现，数据库迁移放到企业级第 02 步执行。

## 2. 改动文件

代码：

```text
app/security.py
app/user_store.py
app/auth.py
app/config.py
app/runtime_settings.py
app/main.py
web/index.html
web/app.js
web/styles.css
tests/conftest.py
tests/test_auth.py
```

配置和文档：

```text
.env.example
.gitignore
README.md
docs/00-project-continuation-guide.md
docs/enterprise-summary/01-auth-and-user-system-summary.md
```

## 3. 接口变化

新增公开接口：

```text
POST /auth/bootstrap-admin
POST /auth/login
```

新增需要登录的接口：

```text
GET /auth/me
POST /auth/logout
```

已保护核心接口：

```text
/documents*
/rag/ask
/agent/ask
/settings*
/evaluation*
/chat
/embeddings/text
```

公开保留：

```text
GET /health
GET /app
GET /docs
GET /openapi.json
```

## 4. 验证结果

已通过：

```powershell
python -m compileall app tests
```

当前机器没有项目 `.venv`，系统 Python 也没有安装 `pytest` 和 `fastapi`，所以未能运行：

```powershell
python -m pytest
```

待本地环境恢复后，建议优先运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_main_api.py
```

## 5. 后续影响

后续企业级改造可以基于 `get_current_user` 继续扩展：

```text
文档归属
知识库归属
多租户隔离
审计日志 user_id
LLM profile 归属
```

## 6. 下一步建议

下一步进入：

```text
企业级第 02 步：数据库持久化替代本地 JSON
```

重点把 `users`、`documents`、`llm_profiles` 迁移到数据库模型，同时保持当前鉴权接口和 Web UI 登录体验不倒退。
## 7. 补充决策：注册能力延后

当前不在 `data/users.json` 阶段新增开放注册。

原因是开放注册会立刻涉及：

```text
用户唯一性
账号启用/禁用
默认角色
默认组织或知识库归属
是否允许任何人注册
管理员审核或邀请
```

这些能力更适合和后续数据库持久化、多租户隔离一起实现。

后续建议：

```text
第 02 步：把 users 迁入数据库，并预留注册/用户管理接口结构
第 03 步：结合 Organization / KnowledgeBase / membership 决定新用户归属
```
## 8. 补充验证结果

后续已创建 `.venv` 并安装 `requirements.txt`，完整回归测试通过：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
56 passed
```
