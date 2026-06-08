# 第 05 步执行目标：工单创建和人工转接

## 1. 背景

真实客服系统不能要求 Agent 解决所有问题。

当出现以下情况时，应创建工单或建议人工转接：

```text
资料不足但用户需要继续处理
退款争议
投诉或强烈负面情绪
订单异常
超出政策范围
用户明确要求人工客服
```

## 2. 本次目标

新增能力：

```text
工单数据模型
创建工单工具
人工转接判断
工单列表和详情接口
Agent 回复中展示 handoff_reason
```

新增接口：

```text
POST /tickets
GET /tickets
GET /tickets/{ticket_id}
```

## 3. 不做什么

本次不做：

```text
坐席分配
客服后台回复
工单 SLA
通知系统
复杂情绪识别模型
```

## 4. 预计改动文件

```text
app/ticket_store.py
app/agent.py
app/tools.py
app/main.py
tests/test_ticket_store.py
tests/test_agent.py
docs/summary/05-ticket-and-human-handoff-summary.md
```

## 5. 工单字段建议

```json
{
  "ticket_id": "ticket_...",
  "conversation_id": "conv_...",
  "status": "open",
  "priority": "normal",
  "reason": "refund_dispute",
  "summary": "...",
  "created_at": "..."
}
```

## 6. 验收标准

```text
用户要求人工时创建工单
退款争议时创建工单
工单包含 conversation 上下文摘要
Agent 响应包含 handoff_reason
pytest 覆盖创建工单和转人工判断
```

## 7. 测试方式

```powershell
python -m compileall app tests
python -m pytest tests/test_ticket_store.py tests/test_agent.py
```

