# 企业级改造总路线：Local Knowledge RAG Agent -> Enterprise RAG Platform

## 1. 当前起点

当前项目已经具备个人项目级 RAG Agent 能力：

```text
多格式文档入库
本地 embedding
Qdrant local 检索
RAG 问答
Agent 路由
检索评估
Web UI
LLM 多供应商配置
Docker / 一键启动
```

但当前仍然是本地单机工具，关键限制包括：

```text
没有登录鉴权
没有多用户隔离
没有组织 / 租户模型
运行数据主要依赖本地 JSON
Qdrant 使用 local 模式
入库任务是同步请求
没有审计日志
没有统一可观测性
没有密钥治理
没有正式部署拓扑
```

---

## 2. 企业级目标

企业级分支目标是把项目升级为：

```text
支持团队使用、权限隔离、可审计、可部署、可评估的 RAG 平台雏形。
```

更具体地说：

```text
1. 用户可以登录
2. 文档和知识库按用户 / 组织隔离
3. 文档 metadata 和配置进入数据库
4. 大文件入库走后台任务
5. Qdrant 从 local 模式升级为服务化模式
6. API 有权限校验和审计记录
7. 关键链路有日志、指标和错误追踪
8. RAG 效果有评估历史和质量治理
9. 部署时不暴露 API Key
```

---

## 3. 总体架构目标

目标架构：

```text
Web UI
-> FastAPI Gateway
-> Auth / Tenant Context
-> Document Service
-> Indexing Job Worker
-> Embedding Service
-> Qdrant Service
-> LLM Provider Layer
-> Evaluation Service
-> Audit / Observability
```

数据存储建议：

```text
PostgreSQL: 用户、组织、知识库、文档 metadata、任务状态、审计日志
Qdrant Server: 向量数据
Object Storage: 原始文件和抽取中间产物
Redis: 任务队列、缓存、限流
```

本项目可以先以本地 Docker Compose 模拟企业部署。

---

## 4. 阶段规划

### 阶段 A：企业骨架

```text
登录鉴权
用户模型
数据库持久化
组织 / 租户字段
权限校验中间件
```

### 阶段 B：数据和任务治理

```text
文档 metadata 入库
运行时配置入库
异步入库任务
任务状态和失败重试
服务化 Qdrant
```

### 阶段 C：安全和可观测

```text
审计日志
请求日志
错误追踪
LLM 调用记录
API Key 加密存储
限流和文件大小限制
```

### 阶段 D：质量和产品化

```text
评估历史
回答质量评估
用户反馈
知识库版本
发布说明和演示材料
```

---

## 5. 不做什么

企业级分支前期不做：

```text
多地域部署
Kubernetes 生产级编排
复杂计费系统
完整 OAuth 企业 SSO
大规模分布式检索优化
商业 SaaS 多套餐系统
```

先完成企业级基础骨架，再逐步增强。

---

## 6. 执行原则

```text
1. 每一步都要保持 Swagger Docs 可测试
2. 每一步都要有权限和数据隔离意识
3. 不读取、不提交 .env 和真实 API Key
4. 新增表结构必须有迁移方案
5. 不一次性替换整个系统
6. 保留本地开发体验
7. 一步一提交，方便回滚
```
