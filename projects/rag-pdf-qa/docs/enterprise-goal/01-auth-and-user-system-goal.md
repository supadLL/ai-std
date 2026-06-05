# 企业级第 01 步执行目标：登录鉴权与用户体系

## 1. 背景

当前项目是本地单机工具，所有用户访问同一套知识库和运行配置。

企业级改造第一步必须先建立用户身份，否则后续无法做：

```text
文档归属
知识库隔离
权限控制
审计日志
API Key 归属
用户操作追踪
```

## 2. 本次目标

本次实现企业级最小用户体系：

```text
1. 新增 User 数据模型
2. 新增登录接口
3. 新增注册或初始化管理员机制
4. 新增 JWT access token
5. 新增当前用户依赖 get_current_user
6. Web UI 支持登录态
7. 受保护接口要求登录
8. Swagger Docs 可以测试鉴权接口
```

## 3. 不做什么

本次不做：

```text
企业 SSO
OAuth 第三方登录
短信 / 邮箱验证码
复杂 RBAC 权限
多租户组织模型
刷新 token
密码找回
```

## 4. 预计修改文件

```text
app/main.py
app/config.py
app/auth.py
app/security.py
app/models.py 或 app/user_store.py
web/index.html
web/app.js
web/styles.css
tests/test_auth.py
tests/test_main_api.py
.env.example
README.md
docs/00-project-continuation-guide.md
```

## 5. 接口设计建议

```text
POST /auth/login
POST /auth/logout
GET /auth/me
POST /auth/bootstrap-admin
```

请求示例：

```json
{
  "username": "admin",
  "password": "change-me"
}
```

响应示例：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "user_id": "u_001",
    "username": "admin",
    "role": "admin"
  }
}
```

## 6. 验收标准

```text
1. 未登录访问受保护接口返回 401
2. 登录后可以访问 /documents、/rag/ask、/settings
3. Swagger Docs 可以通过 Authorize 测试 Bearer token
4. Web UI 可以登录、退出、保持本地 token
5. 密码不明文存储
6. pytest 通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_main_api.py
```

手工测试：

```text
1. 打开 /app
2. 未登录时显示登录界面
3. 登录成功进入文件导入页
4. 刷新页面仍保持登录
5. 退出后无法访问受保护数据
```
