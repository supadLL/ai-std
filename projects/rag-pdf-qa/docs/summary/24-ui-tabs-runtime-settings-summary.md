# 第 24 步完成总结：UI 分页与运行时模型设置

本 summary 记录第 24 步实际完成内容。

对应 goal：

```text
docs/goal/24-ui-tabs-runtime-settings-goal.md
```

---

## 1. 本次完成了什么

完成内容：

```text
1. Web UI 调整为 Tab 页面结构
2. 新增“文件导入”页，保留上传、chunk、overlap、reindex 和文档列表
3. 新增“知识问答”页，保留聊天式问答、top_k、score_threshold、右侧 sources 和 debug 信息
4. 新增“设置”页
5. 设置页支持配置 API Base URL、LLM model、timeout
6. 设置页支持填写或清除运行时 API Key
7. 设置页支持展示和编辑 RAG system prompt
8. 设置页支持展示和编辑 RAG answer instructions
9. 后端新增 /settings 读取和保存运行时设置
10. /settings 不返回真实 API Key，只返回是否已配置和来源
11. /chat、/rag/ask、/agent/ask 使用运行时 LLM 设置
12. RAG prompt 支持运行时覆盖，不再只能改源码
13. data/runtime_settings.json 已加入 .gitignore，避免提交本地密钥
```

---

## 2. 改动文件

代码：

```text
app/main.py
app/runtime_settings.py
web/index.html
web/styles.css
web/app.js
```

测试：

```text
tests/test_main_api.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/goal/24-ui-tabs-runtime-settings-goal.md
docs/summary/README.md
docs/summary/24-ui-tabs-runtime-settings-summary.md
docs/summary/project-demo-checklist.md
```

配置：

```text
.gitignore
```

---

## 3. 接口变化

新增：

```text
GET /settings
PUT /settings
```

`GET /settings` 返回：

```text
deepseek_base_url
deepseek_model
request_timeout_seconds
api_key_configured
api_key_source
embedding_model
qdrant_collection
rag_system_prompt
rag_answer_instructions
```

说明：

```text
api_key_configured 只表示是否已配置
api_key_source 只表示来源：runtime / env / none
不会返回真实 API Key
```

`PUT /settings` 支持保存：

```text
deepseek_api_key
clear_api_key
deepseek_base_url
deepseek_model
request_timeout_seconds
rag_system_prompt
rag_answer_instructions
```

保存位置：

```text
data/runtime_settings.json
```

该文件是本地运行数据，不提交 GitHub。

---

## 4. UI 变化

当前 `/app` 分为三个页签：

```text
文件导入
知识问答
设置
```

文件导入页用于：

```text
上传 PDF / Markdown / txt / docx / csv / xlsx
设置 chunk_size、overlap、reindex
查看文档列表
```

知识问答页用于：

```text
输入问题
设置 top_k 和 score_threshold
查看聊天式回答
查看右侧 sources 和 debug 信息
```

设置页用于：

```text
调整 LLM 接入参数
调整 RAG prompt
查看 API Key 是否已配置
保存本地运行时设置
```

---

## 5. 安全处理

本次重点避免 API Key 泄露：

```text
1. GET /settings 不返回真实 API Key
2. 设置页加载后 API Key 输入框保持空
3. 保存后 API Key 输入框会清空
4. data/runtime_settings.json 加入 .gitignore
5. 测试和文档不写入真实 API Key
```

后续如果需要把项目给别人使用，应继续保持：

```text
.env 不提交
data/runtime_settings.json 不提交
真实 API Key 不写进 README / docs / tests
```

---

## 6. 验证结果

已验证：

```text
/app 包含文件导入、知识问答、设置三个页签
/settings 已出现在 OpenAPI
GET /settings 不返回真实 API Key
设置页保存会调用 PUT /settings
RAG prompt 可通过 runtime settings 覆盖
```

浏览器级验证：

```text
使用 Node Playwright 打开 http://127.0.0.1:8000/app
mock /settings，避免写入 fake API Key
确认 import / ask / settings 三个 tab 均可切换
确认知识问答页右侧 sourceList 仍存在
确认设置页能加载 system prompt
确认保存设置时 payload 包含 base_url、model、timeout、API Key 和两个 prompt 字段
确认测试后未生成 data/runtime_settings.json
```

自动化测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

当前测试基线：

```text
pytest 28 passed
```

---

## 7. 当前限制

本次没有实现：

```text
流式 token 输出
Web UI Agent 模式切换
多轮对话记忆
多套 prompt profile
登录鉴权
云端部署
```

运行时设置目前是单机本地 JSON 文件，适合学习和本地使用。

---

## 8. 后续建议

后续可以继续做：

```text
1. Web UI 接入 /agent/ask，并增加普通问答 / RAG / Agent 模式切换
2. 增加回答详细程度参数，例如 concise / balanced / detailed
3. 增加 prompt profile 保存和恢复
4. 增加流式输出，让回答生成过程更像真实聊天
5. 增加一键启动脚本或 Docker 化部署
```
