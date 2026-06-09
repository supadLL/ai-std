# enterprise-goal 企业级改造执行文档规范

这个目录用于存放 `enterprise-rag-platform` 分支上的企业级改造 goal。

它和原来的 `docs/goal/` 不同：

```text
docs/goal/            学习型本地 RAG Agent 主线
docs/enterprise-goal/ 企业级 RAG 平台改造主线
```

---

## 1. 为什么单独建目录

当前 `main` 主线已经形成一个本地个人项目级 RAG Agent。

企业级改造会引入新的工程问题：

```text
登录鉴权
多用户 / 多租户
数据库持久化
权限隔离
异步任务
对象存储
服务化向量库
审计日志
可观测性
部署和密钥治理
```

这些不适合继续塞进原来的学习步骤编号里，所以单独放在 `docs/enterprise-goal/`。

---

## 2. 执行顺序

企业级改造仍然遵守项目原来的节奏：

```text
先读 enterprise goal
-> 写代码
-> 跑测试
-> 写 enterprise summary 或普通 summary
-> 更新 README / 00 号文档
-> 一步一提交
```

每次只执行一个 goal，避免同时改动认证、数据库、UI、部署等多个大模块。

---

## 3. 当前企业级路线

| 步骤 | goal 文档 | 目标 |
|---:|---|---|
| 00 | [00-enterprise-roadmap.md](00-enterprise-roadmap.md) | 企业级总路线和范围边界 |
| 01 | [01-auth-and-user-system-goal.md](01-auth-and-user-system-goal.md) | 登录鉴权与用户体系 |
| 02 | [02-database-persistence-goal.md](02-database-persistence-goal.md) | 数据库持久化替代本地 JSON |
| 03 | [03-tenant-and-permission-isolation-goal.md](03-tenant-and-permission-isolation-goal.md) | 多租户和权限隔离 |
| 04 | [04-async-indexing-job-goal.md](04-async-indexing-job-goal.md) | 大文件异步入库任务 |
| 05 | [05-enterprise-vector-store-goal.md](05-enterprise-vector-store-goal.md) | 服务化 Qdrant 和索引治理 |
| 06 | [06-audit-and-observability-goal.md](06-audit-and-observability-goal.md) | 审计日志、指标和可观测性 |
| 07 | [07-evaluation-and-quality-governance-goal.md](07-evaluation-and-quality-governance-goal.md) | 企业级评估和质量治理 |
| 08 | [08-deployment-and-secret-governance-goal.md](08-deployment-and-secret-governance-goal.md) | 部署、环境和密钥治理 |

---

## 4. 企业级改造边界

本分支目标是把项目从：

```text
个人本地 RAG Agent
```

升级为：

```text
可面向团队使用的企业级 RAG 平台雏形
```

但仍然要避免夸大：

```text
不是完整商业 SaaS
不是成熟权限中台
不是高并发生产系统
不是大规模分布式检索平台
```

目标是形成企业级工程骨架和关键能力闭环。

---

## 5. 命名规范

```text
NN-topic-goal.md
```

例如：

```text
01-auth-and-user-system-goal.md
02-database-persistence-goal.md
```

企业级 summary 后续建议放到：

```text
docs/enterprise-summary/
```

如果只是少量补充说明，也可以暂时放入：

```text
docs/summary/
```

Additional enterprise goal:

```text
09-runtime-safety-and-limits-goal.md
10-source-file-storage-governance-goal.md
11-knowledge-base-versioning-goal.md
12-knowledge-base-snapshot-diff-goal.md
13-user-registration-and-provisioning-goal.md
14-knowledge-base-member-management-goal.md
15-web-ui-account-and-member-management-goal.md
16-llm-answer-quality-judge-goal.md
17-pdf-table-extraction-governance-goal.md
18-pdf-embedded-image-ocr-goal.md
19-html-web-page-body-loader-goal.md
20-safe-url-web-page-ingestion-goal.md
```
