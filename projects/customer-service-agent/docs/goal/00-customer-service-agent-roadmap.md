# 第 00 步执行目标：Customer Service Agent 项目路线图

## 1. 背景

`rag-pdf-qa` 已经完成本地 RAG Agent 主线，并在企业级分支开始做登录、数据库、多租户和异步索引。

`customer-service-agent` 的目标不是重复做一个知识库问答，而是把 RAG 放进更具体的客服业务流程里：

```text
用户咨询
-> 识别问题类型
-> 查知识库或调用业务工具
-> 生成客服回复
-> 必要时创建工单或转人工
-> 记录过程并用于质检
```

## 2. 项目目标

做一个可运行、可演示、可评估的客服 Agent 项目。

目标能力：

```text
客服 FAQ / 政策问答
订单状态查询
物流信息查询
退款资格判断
多轮追问
工单创建
人工转接判断
客服回答质检
Web UI 演示
```

## 3. 推荐业务场景

初版建议选择电商售后客服，因为它天然包含：

```text
商品咨询
订单查询
物流查询
退款退货
优惠券和发票
投诉与人工转接
```

初期全部使用 mock 数据，不接真实系统。

## 4. 总体架构

```text
Web UI
-> FastAPI API
-> Conversation Manager
-> Agent Router
-> FAQ / Policy Retriever
-> Business Tools
   -> Order Tool
   -> Shipping Tool
   -> Refund Tool
   -> Ticket Tool
-> LLM Provider
-> Evaluation / QA
```

## 5. 分阶段路线

### 阶段 A：最小客服 Agent

```text
01 项目骨架和客服 Chat
02 FAQ / 政策知识库 RAG
03 业务工具调用和 Agent 路由
```

目标是让 Agent 能回答基础客服问题，并解释自己为什么查知识库或调用工具。

### 阶段 B：业务流程闭环

```text
04 多轮会话状态
05 工单创建和人工转接
```

目标是让 Agent 不只是回答问题，还能处理“查订单、判断退款、创建工单”这样的流程。

### 阶段 C：产品化演示

```text
06 Web UI
07 评估和质检
08 演示与简历呈现
```

目标是让项目能被清楚演示，也能进入简历和面试讲解。

## 6. 不做什么

初版不做：

```text
真实订单系统接入
真实支付 / 退款执行
复杂坐席系统
多渠道客服接入
企业微信 / 飞书 / Slack 集成
完整权限中台
生产级部署
```

## 7. 验收标准

路线图阶段完成后，应具备：

```text
README 中能说明项目定位
docs/goal 中有完整执行计划
每一步都有明确验收标准
项目边界清楚，不和 rag-pdf-qa 重复
```

## 8. 下一步

进入：

```text
01-project-bootstrap-and-chat-goal.md
```

建立项目骨架、最小 FastAPI 服务和客服 Chat 基线。

