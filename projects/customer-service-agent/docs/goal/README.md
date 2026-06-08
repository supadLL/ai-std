# goal 执行文档规范

这个目录用于存放 `customer-service-agent` 项目的开工前执行目标。

每一个重要阶段都应该先写 goal，再写代码。

## 执行节奏

```text
读当前 goal
-> 明确验收标准
-> 修改代码或文档
-> 运行验证
-> 写 summary
-> 更新 README
```

## 命名规范

```text
NN-topic-goal.md
```

例如：

```text
01-project-bootstrap-and-chat-goal.md
02-faq-knowledge-base-rag-goal.md
```

## 当前路线

| 步骤 | goal 文档 | 目标 |
|---:|---|---|
| 00 | [00-customer-service-agent-roadmap.md](00-customer-service-agent-roadmap.md) | 项目路线图和范围边界 |
| 01 | [01-project-bootstrap-and-chat-goal.md](01-project-bootstrap-and-chat-goal.md) | FastAPI 项目骨架和客服 Chat 基线 |
| 02 | [02-faq-knowledge-base-rag-goal.md](02-faq-knowledge-base-rag-goal.md) | FAQ / 政策知识库 RAG |
| 03 | [03-business-tool-routing-goal.md](03-business-tool-routing-goal.md) | 业务工具调用和 Agent 路由 |
| 04 | [04-conversation-state-goal.md](04-conversation-state-goal.md) | 多轮会话和上下文状态 |
| 05 | [05-ticket-and-human-handoff-goal.md](05-ticket-and-human-handoff-goal.md) | 工单创建和人工转接 |
| 06 | [06-web-ui-goal.md](06-web-ui-goal.md) | 客服聊天 Web UI 和管理视图 |
| 07 | [07-evaluation-and-quality-governance-goal.md](07-evaluation-and-quality-governance-goal.md) | 客服评估、质检和回归测试集 |
| 08 | [08-demo-and-resume-polish-goal.md](08-demo-and-resume-polish-goal.md) | 演示、README 和简历呈现收口 |

## 编写要求

每份 goal 至少包含：

```text
背景
本次目标
不做什么
预计改动文件
接口或数据结构变化
验收标准
测试方式
```

## 项目约束

当前项目优先保持轻量：

```text
不用复杂 Agent 框架
不急着接真实业务系统
不提前做完整 SaaS
先用 mock 数据和可解释路由打通业务闭环
```

