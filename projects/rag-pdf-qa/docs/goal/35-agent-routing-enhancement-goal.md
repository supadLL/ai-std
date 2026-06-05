# 第 35 步执行目标：Agent 工具路由增强

这一步的目标是：

> 在当前最小 `/agent/ask` 基础上，增强工具选择理由、失败回退和前端可解释性，让它更像一个可观察的 RAG Agent。

---

## 1. 背景

当前已经有最小 Agent 工具路由：

```text
chat
rag
insufficient_context
```

但对于学习和展示来说，还需要知道：

```text
为什么选择 RAG？
为什么没有检索？
检索失败时怎么回退？
本次用了哪些工具？
```

---

## 2. 本次目标

本次完成：

```text
1. 为 /agent/ask 增加 route_reason
2. 返回 tools_used 列表
3. 返回 routing_debug 调试信息
4. 对检索无命中场景做清晰回退
5. Web UI 增加 Agent 模式切换
6. Web UI 展示本次选择的工具和理由
```

---

## 3. 不做什么

本次不做：

- 多 Agent 协作
- Graph 工作流
- LangChain Agent
- 外部工具调用
- 文件系统读写 Agent
- 自动联网搜索

---

## 4. 需要修改的文件

预计修改：

```text
app/main.py
web/index.html
web/app.js
web/styles.css
README.md
docs/00-project-continuation-guide.md
```

测试：

```text
tests/test_agent.py
tests/test_main_api.py
```

完成后新增：

```text
docs/summary/35-agent-routing-enhancement-summary.md
```

---

## 5. 接口变化

扩展：

```text
POST /agent/ask
```

响应增加：

```text
route_reason: string
tools_used: string[]
routing_debug: object
```

保持已有字段向后兼容。

---

## 6. 验收标准

完成后应满足：

```text
1. 普通问题可走 chat
2. 知识库问题可走 rag
3. 无资料问题可返回 insufficient_context
4. 每次响应包含 route_reason
5. Web UI 能展示 route 和 tools_used
6. Swagger Docs 可测试 /agent/ask
7. pytest 通过
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
POST /agent/ask
问题 1：普通闲聊
问题 2：知识库相关问题
问题 3：明显资料不足的问题
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
切换 Agent 模式
查看工具路由理由
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/35-agent-routing-enhancement-summary.md
```
