# 企业级第 13 步执行目标：用户注册与管理员开通

## 1. 背景

当前企业级分支已经支持：

```text
首次 bootstrap-admin
登录 / 当前用户 / 退出
Bearer token 保护核心接口
登录后自动获得默认知识库 access
```

但在局域网团队部署场景下，仅靠首次管理员初始化还不够。其他成员需要一种清晰的账号开通方式：

```text
局域网可信环境：允许用户自助注册普通账号
生产或半开放环境：管理员手动创建普通账号
```

本步骤补齐最小用户注册和管理员开通能力。

## 2. 本次目标

```text
1. 新增 USER_REGISTRATION_ENABLED 配置
2. 新增 POST /auth/register 自助注册普通用户
3. 新增 GET /admin/users 管理员查看用户列表
4. 新增 POST /admin/users 管理员创建用户
5. 新注册/新创建用户默认 role=user、status=active
6. 新用户创建后自动确保个人默认 knowledge base access
7. 注册和管理员创建用户写入 audit log
8. README、续接文档和 enterprise summary 同步更新
```

## 3. 不做什么

本次不做：

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

## 4. 预计修改文件

```text
app/config.py
app/main.py
.env.example
tests/test_auth.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/13-user-registration-and-provisioning-summary.md
```

## 5. API 设计

```text
POST /auth/register
GET /admin/users
POST /admin/users
```

`POST /auth/register` 请求体沿用：

```json
{
  "username": "alice",
  "password": "change-me-123"
}
```

`POST /admin/users` 也使用同样请求体，创建普通用户，不允许通过接口直接创建 admin。

## 6. 配置设计

```text
USER_REGISTRATION_ENABLED=true
```

建议：

```text
development / 可信局域网演示：true
production / 半开放网络：false，改由管理员创建用户
```

## 7. 验收标准

```text
1. 开启 USER_REGISTRATION_ENABLED 时，未登录用户可以注册普通 user
2. 关闭 USER_REGISTRATION_ENABLED 时，注册返回 403
3. 注册成功后返回 bearer token 且不泄露 password/password_hash
4. 管理员可以查看用户列表和创建普通用户
5. 普通用户不能访问 /admin/users
6. 新用户可以登录并拥有默认 knowledge base
7. OpenAPI 出现新接口
8. 测试全部通过
```

## 8. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
