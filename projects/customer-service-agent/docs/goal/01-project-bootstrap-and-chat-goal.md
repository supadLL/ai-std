# 第 01 步执行目标：项目骨架和客服 Chat 基线

## 1. 背景

本项目需要先建立最小可运行服务，再逐步加入 RAG、工具和工单能力。

第一步不做复杂 Agent，只做：

```text
FastAPI 服务
配置读取
LLM Chat 调用
客服人设 prompt
最小测试
```

## 2. 本次目标

新增项目骨架：

```text
app/
tests/
data/
web/
docs/
```

新增接口：

```text
GET /health
POST /chat
```

`POST /chat` 用于验证：

```text
LLM 配置可读取
客服语气和边界可控制
错误能转换为清晰响应
```

## 3. 不做什么

本次不做：

```text
知识库检索
订单工具
多轮会话持久化
工单系统
Web UI
登录鉴权
```

## 4. 预计改动文件

```text
README.md
.env.example
requirements.txt
app/__init__.py
app/config.py
app/llm_client.py
app/main.py
tests/test_main_api.py
tests/test_llm_client.py
docs/summary/01-project-bootstrap-and-chat-summary.md
```

## 5. 接口设计

请求：

```json
{
  "message": "我的订单什么时候发货？"
}
```

响应：

```json
{
  "reply": "我可以帮你查询发货情况。请提供订单号。",
  "usage": null
}
```

## 6. 验收标准

```text
GET /health 返回 ok
POST /chat 能调用当前 LLM Provider
没有 API Key 时返回清晰错误
pytest 覆盖 health、chat 请求模型和 LLM 异常
README 写清楚启动方式
```

## 7. 测试方式

```powershell
python -m compileall app tests
python -m pytest
uvicorn app.main:app --host 127.0.0.1 --port 8010
```

端口先建议使用 `8010`，避免和 `rag-pdf-qa` 默认 `8000` 冲突。

