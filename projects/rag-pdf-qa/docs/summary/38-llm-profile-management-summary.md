# 第 38 步完成总结：LLM API 配置档案管理

## 1. 本次完成了什么

本次把第 37 步的“单个 LLM Provider 表单”升级为“LLM API 配置档案管理”。

设置页现在可以管理多个模型配置：

```text
供应商
API Key 是否已配置
模型
是否启用
操作：启用 / 编辑 / 删除
```

并支持点击“新增 API”打开弹窗创建新的模型配置。当前启用的 profile 会作为 `/chat`、`/rag/ask`、`/agent/ask` 的底层 LLM 配置来源。

## 2. 改动文件

```text
app/runtime_settings.py
app/main.py
web/index.html
web/app.js
web/styles.css
tests/test_main_api.py
tests/test_runtime_settings.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

## 3. 接口变化

`GET /settings` 新增：

```text
active_llm_profile_id
llm_profiles
```

新增接口：

```text
POST /settings/llm-profiles
PUT /settings/llm-profiles/{profile_id}
DELETE /settings/llm-profiles/{profile_id}
POST /settings/llm-profiles/{profile_id}/activate
```

真实 API Key 只允许提交保存，不会在响应里返回。

## 4. Web UI 变化

设置页新增：

```text
模型 API 配置表格
新增 API 按钮
新增 / 编辑弹窗
启用按钮
删除按钮
API Key 掩码显示
```

主设置页仍保留：

```text
Timeout
RAG System Prompt
RAG Answer Instructions
```

这样模型配置和 prompt 配置分层更清楚。

## 5. 验证结果

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py tests\test_runtime_settings.py
```

结果：

```text
21 passed
```

提交前还需要执行全量验证：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
git diff --check
```

## 6. 后续影响

这一步让项目的模型配置更接近真实项目：

```text
可以预置多个供应商
可以快速切换当前底层 LLM
可以保留多个模型版本
可以让其他使用者按自己的 API 配置接入
```

下一步建议执行：

```text
docs/goal/39-project-demo-and-resume-polish-goal.md
```
