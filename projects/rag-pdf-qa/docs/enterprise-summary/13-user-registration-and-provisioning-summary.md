# 企业级第 13 步完成总结：用户注册与管理员开通

本步骤补齐局域网多人使用时的账号开通路径：可信环境可开放普通用户自助注册，生产或半开放环境可由管理员创建普通用户。

---

## 1. 本次新增能力

```text
USER_REGISTRATION_ENABLED 配置
POST /auth/register 自助注册普通用户
GET /admin/users 管理员查看用户列表
POST /admin/users 管理员创建普通用户
新用户默认 role=user、status=active
新用户创建后自动获得个人默认 knowledge base
注册和管理员创建用户写入 audit_logs
OpenAPI 暴露新认证和管理端点
```

---

## 2. 新增配置

```text
USER_REGISTRATION_ENABLED=true
```

默认策略：

```text
development: 默认开启
production: 默认关闭
```

可信局域网演示可以开启自助注册；生产或半公开网络建议关闭自助注册，改由管理员创建用户。

---

## 3. 新增 API

| 接口 | 说明 |
|---|---|
| `POST /auth/register` | 自助注册普通 user，并返回 bearer token |
| `GET /admin/users` | 管理员查看用户列表 |
| `POST /admin/users` | 管理员创建普通 user |

注册和管理员创建用户都不会返回 `password` 或 `password_hash`。

---

## 4. 关键行为

```text
系统第一位用户仍必须通过 POST /auth/bootstrap-admin 初始化 admin
如果还没有任何用户，POST /auth/register 返回 409，提示先初始化 admin
USER_REGISTRATION_ENABLED=false 时，POST /auth/register 返回 403
POST /admin/users 只创建 role=user，不开放直接创建 admin
普通 user 访问 /admin/users 返回 403
```

---

## 5. 修改文件

| 文件 | 说明 |
|---|---|
| `app/config.py` | 新增 `user_registration_enabled` 配置 |
| `.env.example` | 新增 `USER_REGISTRATION_ENABLED` |
| `docker-compose.yml` | Compose 显式传入注册开关，生产默认关闭 |
| `app/main.py` | 新增注册、管理员用户接口和 admin 权限检查 |
| `tests/test_auth.py` | 覆盖注册开启/关闭、管理员创建用户、普通用户禁止访问 |
| `tests/test_main_api.py` | 覆盖 OpenAPI 新端点 |
| `README.md` | 更新核心能力、接口和配置说明 |
| `docs/00-project-continuation-guide.md` | 更新当前阶段、接口和支持范围 |
| `docs/deployment.md` | 更新部署账号开通说明 |
| `docs/enterprise-goal/13-user-registration-and-provisioning-goal.md` | 第 13 步目标 |
| `docs/enterprise-goal/README.md` | 登记 Step 13 goal |

---

## 6. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

阶段结果：

```text
targeted tests: 29 passed
full pytest: 86 passed
```

---

## 7. 当前边界

本步骤只做最小账号开通能力，不包含：

```text
邮箱验证
找回密码
修改密码
禁用/启用用户
删除用户
复杂 RBAC
邀请链接
SSO / OAuth
```

后续可以继续扩展用户状态管理、知识库共享成员管理、邀请链接和组织级 RBAC。
