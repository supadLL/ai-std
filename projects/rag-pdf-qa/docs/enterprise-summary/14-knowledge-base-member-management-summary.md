# 企业级第 14 步完成总结：知识库成员共享管理

本步骤在已有 `knowledge_base_memberships` 表基础上补齐最小知识库成员管理能力，让 owner/admin 可以把已注册用户加入共享知识库。

---

## 1. 本次新增能力

```text
GET /knowledge-bases/{knowledge_base_id}/members
POST /knowledge-bases/{knowledge_base_id}/members
DELETE /knowledge-bases/{knowledge_base_id}/members/{user_id}
owner/admin 成员管理权限检查
添加成员后目标用户可访问该 knowledge base
移除成员后目标用户不能再访问该 knowledge base
保护最后一个 owner 不被移除
成员添加/移除写入 audit_logs
```

---

## 2. 新增 API

| 接口 | 说明 |
|---|---|
| `GET /knowledge-bases/{knowledge_base_id}/members` | 查看知识库成员 |
| `POST /knowledge-bases/{knowledge_base_id}/members` | 添加已注册用户为知识库成员 |
| `DELETE /knowledge-bases/{knowledge_base_id}/members/{user_id}` | 移除知识库成员 |

添加成员请求：

```json
{
  "username": "alice"
}
```

新增成员默认 `role=member`。

---

## 3. 权限边界

```text
平台 admin 可以管理任意 active knowledge base 的成员
普通用户必须是该 knowledge base 的 owner 才能管理成员
member 可以访问知识库，但不能管理成员
当前 member 权限仍是最小协作者模型，不做 read/write 细粒度区分
```

---

## 4. 修改文件

| 文件 | 说明 |
|---|---|
| `app/permissions.py` | 新增成员 dataclass、列表、添加、移除和知识库管理查询 |
| `app/main.py` | 新增 members API、权限 helper 和审计记录 |
| `tests/test_permissions.py` | 覆盖 owner/admin 管理、member 禁止管理、移除后禁止访问、最后 owner 保护 |
| `tests/test_main_api.py` | 覆盖 OpenAPI members 路径 |
| `README.md` | 更新核心能力和接口 |
| `docs/00-project-continuation-guide.md` | 更新当前阶段、接口和支持范围 |
| `docs/enterprise-goal/14-knowledge-base-member-management-goal.md` | 第 14 步目标 |
| `docs/enterprise-goal/README.md` | 登记 Step 14 goal |

---

## 5. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

阶段结果：

```text
targeted tests: 28 passed
full pytest: 89 passed
```

---

## 6. 当前边界

本步骤只实现最小知识库共享，不包含：

```text
复杂 RBAC
细粒度 read/write/admin 权限
邀请链接
审批流程
组织级用户组
成员角色编辑
批量导入成员
```

后续可以继续扩展成员角色编辑、知识库只读成员、组织级成员组和邀请链接。
