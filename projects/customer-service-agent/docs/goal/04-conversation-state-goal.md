# 第 04 步执行目标：多轮会话和上下文状态

## 1. 背景

客服对话常常不是一次问答。

典型多轮场景：

```text
用户：我的订单什么时候到？
客服：请提供订单号。
用户：CS1001
客服：识别上一轮意图，继续查物流。
```

本步让 Agent 具备最小会话记忆。

## 2. 本次目标

新增能力：

```text
conversation_id
消息历史
最近用户意图
最近订单号
多轮追问续接
```

新增接口：

```text
POST /conversations
GET /conversations/{conversation_id}
POST /conversations/{conversation_id}/messages
```

`POST /agent/ask` 可选接收：

```text
conversation_id
```

## 3. 不做什么

本次不做：

```text
长期记忆
用户画像
复杂状态机
向量化对话记忆
跨用户会话隔离
```

## 4. 预计改动文件

```text
app/conversation_store.py
app/agent.py
app/main.py
tests/test_conversation_store.py
tests/test_agent.py
docs/summary/04-conversation-state-summary.md
```

## 5. 数据结构建议

```json
{
  "conversation_id": "conv_...",
  "messages": [],
  "last_intent": "shipping_lookup",
  "last_order_id": "CS1001",
  "created_at": "...",
  "updated_at": "..."
}
```

## 6. 验收标准

```text
可以创建 conversation
同一 conversation 能保存消息历史
用户补充订单号后能续接上一轮意图
不同 conversation 互不影响
pytest 覆盖多轮追问
```

## 7. 测试方式

```powershell
python -m compileall app tests
python -m pytest tests/test_conversation_store.py tests/test_agent.py
```

