# 第 24 步执行目标：UI 分页与运行时模型设置

这一步的目标是：

> 把 Web UI 从单页堆叠界面调整为功能分页，并允许在页面中配置第三方 LLM、API Key 和 RAG prompt。

---

## 1. 背景

当前项目已经实现：

```text
多格式文档入库
本地 Qdrant 检索
DeepSeek RAG 回答
Web UI 初版
聊天式问答反馈
```

但 UI 功能开始变多，继续堆在同一屏会导致：

```text
文件导入、问答、sources、设置混在一起
prompt 仍然需要改源码才能调整
API Key / base_url / model 不方便在新环境里快速切换
```

所以需要把 UI 拆成清晰的功能页，并新增一个本地运行时设置入口。

---

## 2. 本次目标

本次完成：

```text
1. Web UI 增加 Tab 页面
2. 文件导入单独放到“文件导入”页
3. RAG 提问单独放到“知识问答”页
4. 保留知识问答页右侧 sources / debug 展示
5. 新增“设置”页
6. 设置页支持配置 DeepSeek API Base URL
7. 设置页支持配置 LLM model
8. 设置页支持填写或清除运行时 API Key
9. 设置页支持修改 RAG system prompt
10. 设置页支持修改 RAG answer instructions
11. 后端新增 settings 接口，并且不返回真实 API Key
12. 运行时设置落盘到本地忽略文件，避免提交密钥
```

---

## 3. 不做什么

本次不做：

- 多用户配置
- 登录鉴权
- 云端 secret manager
- 流式 token 输出
- Agent 模式 UI 切换
- 大型前端工程化改造

当前设置能力只服务于本地学习和快速调参。

---

## 4. 需要修改的文件

预计修改：

```text
app/main.py
web/index.html
web/styles.css
web/app.js
tests/test_main_api.py
.gitignore
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
docs/summary/project-demo-checklist.md
```

预计新增：

```text
app/runtime_settings.py
docs/summary/24-ui-tabs-runtime-settings-summary.md
```

---

## 5. 接口变化

新增接口：

```text
GET /settings
PUT /settings
```

`GET /settings` 用于读取当前有效配置：

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

注意：

```text
GET /settings 不允许返回真实 API Key。
```

`PUT /settings` 用于保存运行时配置：

```text
deepseek_api_key
clear_api_key
deepseek_base_url
deepseek_model
request_timeout_seconds
rag_system_prompt
rag_answer_instructions
```

运行时配置保存到：

```text
data/runtime_settings.json
```

该文件必须加入 `.gitignore`。

---

## 6. 验收标准

完成后应满足：

```text
1. /app 打开后能看到“文件导入 / 知识问答 / 设置”三个页签
2. 文件导入页可以继续上传和刷新文档
3. 知识问答页可以继续提问，并保留右侧 sources 展示
4. 设置页可以读取 /settings 并显示当前 base_url、model、prompt
5. 设置页保存后会调用 PUT /settings
6. /settings 不返回真实 API Key
7. data/runtime_settings.json 不会被 git 跟踪
8. /chat、/rag/ask、/agent/ask 使用运行时 LLM 设置
9. RAG prompt 可以通过运行时设置覆盖
10. pytest 通过
11. README 和 00 号续接文档同步更新
```

---

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

接口测试：

```text
GET /settings
PUT /settings
GET /openapi.json
```

页面测试：

```text
打开 http://127.0.0.1:8000/app
切换三个 Tab
确认设置页 prompt 可编辑
确认知识问答页 sources 面板仍然存在
```

安全检查：

```text
确认 data/runtime_settings.json 被 .gitignore 忽略
确认 git diff 中没有真实 API Key
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/24-ui-tabs-runtime-settings-summary.md
```

