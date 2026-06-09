# 企业级第 15 步执行目标：Web UI 账号与成员管理

## 1. 背景

第 13 步和第 14 步已经补齐后端 API：

```text
POST /auth/register
GET /admin/users
POST /admin/users
GET /knowledge-bases/{knowledge_base_id}/members
POST /knowledge-bases/{knowledge_base_id}/members
DELETE /knowledge-bases/{knowledge_base_id}/members/{user_id}
```

但如果局域网用户只能通过 Swagger 操作注册、创建用户和共享知识库，项目落地体验仍然不完整。本步骤把这些企业协作能力接入现有 Web UI。

## 2. 本次目标

```text
1. 登录面板新增 Register 按钮
2. Settings 页新增 Team Access 管理区
3. admin 可以在 UI 查看用户列表和创建普通用户
4. owner/admin 可以在 UI 查看知识库成员
5. owner/admin 可以添加已注册用户为知识库成员
6. owner/admin 可以移除 member
7. 非 admin 不显示用户管理表
8. Web UI 语法和页面路由测试通过
```

## 3. 不做什么

本次不做：

```text
用户禁用/启用
删除用户
修改密码
成员角色编辑
邀请链接
复杂 RBAC
单独管理员后台页面
```

## 4. 预计修改文件

```text
web/index.html
web/app.js
web/styles.css
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/15-web-ui-account-and-member-management-summary.md
```

## 5. 验收标准

```text
1. 登录面板可点击 Register 并调用 /auth/register
2. Settings 页出现 Team Access 区域
3. admin 用户可以创建普通用户并刷新用户列表
4. owner/admin 可以添加和移除知识库成员
5. member 用户不能看到管理员用户管理入口
6. node --check web/app.js 通过
7. pytest 全部通过
```

## 6. 测试方式

```powershell
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
