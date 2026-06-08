# 第 03 步执行目标：业务工具调用和 Agent 路由

## 1. 背景

客服 Agent 和普通 RAG 问答的关键差别是：它要能处理业务动作。

例如：

```text
查订单状态
查物流
判断退款资格
创建工单
```

本步先用 mock 数据实现工具调用，不接真实外部系统。

## 2. 本次目标

新增 Agent Router：

```text
用户问题
-> 判断 route
-> chat / rag / tool / handoff_candidate
-> 执行对应工具
-> 生成可解释回复
```

新增工具：

```text
get_order_status(order_id)
get_shipping_info(order_id)
check_refund_eligibility(order_id)
create_support_ticket(reason, context)
```

新增接口：

```text
POST /agent/ask
```

## 3. 不做什么

本次不做：

```text
真实订单系统
真实退款操作
复杂 function calling 框架
多 Agent 协作
人工坐席后台
```

## 4. 预计改动文件

```text
app/agent.py
app/tools.py
app/mock_data.py
app/main.py
data/mock/orders.json
tests/test_agent.py
tests/test_tools.py
docs/summary/03-business-tool-routing-summary.md
```

## 5. 路由设计

建议 route：

```text
chat
rag
order_lookup
shipping_lookup
refund_check
ticket_create
insufficient_context
```

响应中必须返回：

```text
route
route_reason
tools_used
sources
reply
```

## 6. 验收标准

```text
订单问题会调用订单工具
物流问题会调用物流工具
退款问题会结合订单状态和退款规则
普通政策问题走 RAG
信息不足时会追问订单号
响应包含 route_reason 和 tools_used
pytest 覆盖各 route
```

## 7. 测试方式

```powershell
python -m compileall app tests
python -m pytest tests/test_agent.py tests/test_tools.py
```

手动验证：

```text
问题：订单 CS1001 到哪了？
期望：调用订单或物流工具，并返回可解释结果。
```

