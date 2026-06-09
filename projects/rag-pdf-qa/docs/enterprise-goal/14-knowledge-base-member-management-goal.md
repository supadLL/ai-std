# 企业级第 14 步执行目标：知识库成员共享管理

## 1. 背景

第 13 步已经补齐用户注册和管理员创建普通用户。此时系统里可以有多个用户，但每个普通用户默认只有自己的个人知识库。

企业/团队场景还需要：

```text
把某个知识库共享给其他已注册用户
查看当前知识库成员
移除不再需要访问的成员
```

本步骤基于已有 `knowledge_base_memberships` 表实现最小成员管理 API。

## 2. 本次目标

```text
1. 新增知识库成员列表 API
2. 新增知识库成员添加 API
3. 新增知识库成员移除 API
4. owner 或平台 admin 才能管理成员
5. 被加入成员可以在 /knowledge-bases 中看到该知识库
6. 被移除成员不能再访问该知识库
7. 成员变更写入 audit log
8. README、续接文档和 enterprise summary 同步更新
```

## 3. 不做什么

本次不做：

```text
复杂 RBAC
细粒度 read/write/admin 权限
邀请链接
审批流程
组织级用户组
成员角色编辑
批量导入成员
```

## 4. 预计修改文件

```text
app/permissions.py
app/main.py
tests/test_permissions.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/14-knowledge-base-member-management-summary.md
```

## 5. API 设计

```text
GET /knowledge-bases/{knowledge_base_id}/members
POST /knowledge-bases/{knowledge_base_id}/members
DELETE /knowledge-bases/{knowledge_base_id}/members/{user_id}
```

添加成员请求：

```json
{
  "username": "alice"
}
```

新增成员默认 `role=member`。

## 6. 验收标准

```text
1. owner/admin 可以查看、添加和移除成员
2. 普通 member 不能管理成员
3. 添加不存在用户返回 404
4. 添加后目标用户可以访问该 knowledge base
5. 移除后目标用户不能访问该 knowledge base
6. 不能移除最后一个 owner
7. OpenAPI 出现新接口
8. 测试全部通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
