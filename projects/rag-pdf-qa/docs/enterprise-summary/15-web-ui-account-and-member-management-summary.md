# 企业级第 15 步完成总结：Web UI 账号和成员管理

## 完成内容

本步骤把第 13/14 步的账号和知识库成员 API 接入现有 Web UI：

- 登录面板新增 `Register` 按钮，调用 `POST /auth/register` 完成普通用户注册并自动进入应用。
- Settings 页新增 `Team Access` 区域。
- admin 用户可以在 UI 中查看用户列表，并通过 `POST /admin/users` 创建普通用户。
- owner/admin 可以查看当前知识库成员，添加已注册用户为 member，并移除可移除成员。
- 非 admin 不显示管理员用户列表；非 owner 的知识库成员会看到权限提示，不能进行成员管理。

## 涉及文件

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

## 验收方式

```powershell
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤只做最小账号和成员管理闭环，不包含用户禁用/启用、删除用户、修改密码、成员角色编辑、邀请链接、复杂 RBAC 或独立管理员后台。
