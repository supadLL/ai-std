# Customer Service Agent

当前目标：把 `rag-pdf-qa` 中已经打通的 RAG 能力，升级为一个更贴近业务流程的客服 Agent 项目。

这个项目暂时不追求完整商业客服系统，而是先做一个可运行、可演示、可评估的客服 Agent 雏形：

```text
用户咨询
-> 意图识别
-> FAQ / 政策知识库检索
-> 订单 / 物流 / 退款等业务工具调用
-> Agent 生成可解释回复
-> 必要时创建工单或转人工
```

## 项目定位

`rag-pdf-qa` 更偏底层 RAG 链路学习；`customer-service-agent` 更偏 Agent 如何进入真实业务流程。

本项目重点训练：

```text
客服场景建模
业务工具设计
Agent 路由决策
多轮上下文管理
工单和人工转接
客服质检与评估
Web UI 演示表达
```

## 推荐技术栈

| 模块 | 建议 |
|---|---|
| Web 服务 | FastAPI / Pydantic / Uvicorn |
| LLM 接入 | OpenAI-compatible Chat Completions |
| 知识库 | Markdown / JSON FAQ + 本地向量检索 |
| Embedding | fastembed |
| 向量库 | Qdrant local 起步，后续可服务化 |
| 数据库 | SQLite 起步，后续可迁移 PostgreSQL |
| 前端 | 原生 HTML / CSS / JavaScript 起步 |
| 测试 | pytest |

## 当前阶段

当前仅完成执行文档规划，还没有开始写代码。

后续开发保持：

```text
先写 goal
-> 再写代码
-> 跑测试和手动验证
-> 最后写 summary
-> 必要时更新 README
```

## 执行文档入口

- [goal 执行文档规范](docs/goal/README.md)
- [第 00 步：项目路线图](docs/goal/00-customer-service-agent-roadmap.md)
- [summary 总结文档规范](docs/summary/README.md)

## 初版执行路线

| 步骤 | 目标 |
|---:|---|
| 00 | 明确项目定位、范围和路线图 |
| 01 | 建立 FastAPI 项目骨架和客服 Chat 基线 |
| 02 | 建立 FAQ / 政策知识库 RAG |
| 03 | 增加订单、物流、退款、工单等业务工具路由 |
| 04 | 增加多轮会话和上下文状态 |
| 05 | 增加工单创建和人工转接 |
| 06 | 建立客服聊天 Web UI 和管理视图 |
| 07 | 增加客服评估、质检和回归测试集 |
| 08 | 项目演示、README 和简历呈现收口 |

## 不做什么

初期不做：

```text
完整 CRM
真实支付 / 真实订单系统接入
复杂权限中台
多渠道客服接入
坐席排班
生产级多租户 SaaS
```

先完成能展示核心 Agent 工程能力的闭环，再逐步增强。

