# Local Knowledge RAG Agent

当前目标：把本地多格式知识库 RAG 闭环，逐步升级成可管理、可评估、可交互的个人项目级 RAG Agent 工具。

> 企业级改造分支说明：如果当前分支是 `enterprise-rag-platform`，企业级改造执行目标从 [enterprise-goal 企业级规划](docs/enterprise-goal/README.md) 开始阅读。

## 项目速览

这是一个本地知识库 RAG Agent 学习项目，核心目标是自己打通：

```text
多格式文档入库 -> 文本切分 -> 本地 embedding -> Qdrant 向量检索 -> LLM 基于 sources 回答 -> Web UI / Swagger 测试
```

它适合用于：

```text
学习 RAG 和 Agent 工程链路
搭建个人本地知识库问答工具
展示 FastAPI + 向量数据库 + LLM 接入能力
作为简历中的 AI 工程化个人项目
```

当前主线是个人项目级 RAG Agent；在 `enterprise-rag-platform` 分支上已经开始企业级改造，并完成登录鉴权、用户注册与管理员开通、Web UI 账号与成员管理、数据库持久化、多租户知识库隔离、知识库成员共享、异步索引、审计观测、质量治理、LLM-as-a-judge 回答质量评估、PDF 表格抽取治理、PDF 内嵌图片 OCR 治理、HTML 网页正文入库治理、安全单 URL 网页入库治理、部署密钥治理、运行安全边界、源文件存储治理、知识库版本快照和快照差异比较。

## 技术栈

| 模块 | 技术 |
|---|---|
| Web 服务 | FastAPI / Pydantic / Uvicorn |
| 鉴权 | 本地用户存储 / 密码哈希 / Bearer token |
| 数据库 | SQLAlchemy / SQLite 默认 / PostgreSQL 可配置 |
| 前端 | 原生 HTML / CSS / JavaScript |
| 文档解析 | PDF / PDF 表格 / PDF 图片 OCR / OCR / Markdown / txt / html / docx / csv / xlsx |
| Embedding | fastembed，本地向量化 |
| 向量库 | Qdrant local / Qdrant server |
| LLM | DeepSeek 默认，支持 Qwen、Doubao、OpenAI、Claude compatible、Ollama、MiniMax、自定义 OpenAI-compatible API |
| 测试 | pytest / Playwright 基础页面验证 |
| 启动 | PowerShell 脚本 / Docker |

## 项目架构

```mermaid
flowchart LR
  User[用户 / 同事] --> WebUI[Web UI]
  User --> Docs[Swagger Docs]
  WebUI --> API[FastAPI API]
  Docs --> API
  API --> Loader[Document Loaders]
  Loader --> Splitter[Text Splitter]
  Splitter --> Embed[fastembed]
  Embed --> Qdrant[(Qdrant Local / Server)]
  API --> Search[Vector Search]
  Search --> Qdrant
  API --> LLM[Active LLM Profile]
  LLM --> Answer[RAG / Agent Answer]
  API --> Store[(SQLite / PostgreSQL)]
```

## RAG 链路

```mermaid
flowchart TD
  A[上传 PDF / Markdown / txt / html / URL / docx / 表格] --> B[解析文本、网页正文、表格和 OCR 内容]
  B --> C[按 chunk_size / overlap 切分]
  C --> D[fastembed 生成向量]
  D --> E[写入 Qdrant local / server]
  F[用户问题] --> G[问题向量化]
  G --> H[Qdrant top_k 检索]
  H --> I[构造 sources 和 RAG prompt]
  I --> J[当前启用的 LLM profile]
  J --> K[答案 / 依据 / 资料不足之处]
```

## Web UI 预览

知识问答页：

![知识问答页](docs/assets/web-ui-knowledge-qa.png)

模型配置页：

![模型配置页](docs/assets/web-ui-settings-profiles.png)

## 核心能力

| 能力 | 说明 |
|---|---|
| 多格式入库 | 支持 PDF、PDF 表格抽取、PDF 内嵌图片 OCR、扫描型 PDF OCR、Markdown、txt、html/htm 网页正文、安全单 URL HTML 网页、docx、docx 图片 OCR、csv、xlsx |
| 登录鉴权 | 企业级分支支持初始化管理员、登录、当前用户和 Bearer token 保护核心接口 |
| 用户开通 | 企业级分支支持可配置自助注册普通用户，以及管理员查看和创建用户 |
| Web UI 账号管理 | 企业级分支已在登录面板和 Settings 中接入注册、管理员创建用户和知识库成员管理 |
| 数据库持久化 | 企业级分支已将 users、documents、runtime_settings、llm_profiles 迁入数据库 |
| 多租户隔离 | 企业级分支已支持 Organization / Workspace / KnowledgeBase / Membership，文档和检索按知识库隔离 |
| 知识库共享 | 企业级分支支持 owner/admin 查看、添加和移除知识库成员 |
| 异步索引任务 | 企业级分支支持上传后创建 index job、后台入库、状态查询、失败原因和手动重试 |
| 知识库版本快照 | 企业级分支支持手动创建知识库快照，记录文档清单、索引 chunk 数、稳定 content_hash 和文档级快照差异 |
| 文档管理 | 支持列表、筛选、详情、批量删除、指定文档重建索引 |
| 去重策略 | 使用 content_hash 避免重复入库，支持 reindex 重建 |
| RAG 问答 | 返回稳定三段式回答，并提供 sources |
| Agent 路由 | 支持 chat / rag / insufficient_context，并返回 route_reason、tools_used |
| 检索评估 | 支持本地评估问题集、命中率、页码命中、关键词命中 |
| 回答质量 Judge | 企业级分支支持 LLM-as-a-judge 单次回答质量评分、入库和审计 |
| 模型配置 | 支持多个 LLM API 配置档案和一键启用 |
| 本地部署 | 默认 8000 端口，可本机或可信局域网访问 |

## 核心接口

| 接口 | 作用 |
|---|---|
| `GET /health` | 健康检查 |
| `POST /auth/bootstrap-admin` | 首次初始化管理员 |
| `POST /auth/register` | 自助注册普通用户，受 `USER_REGISTRATION_ENABLED` 控制 |
| `POST /auth/login` | 登录并获取 Bearer token |
| `GET /auth/me` | 查看当前登录用户 |
| `POST /auth/logout` | 退出登录，前端清除 token |
| `GET /admin/users` | 管理员查看用户列表 |
| `POST /admin/users` | 管理员创建普通用户 |
| `GET /knowledge-bases` | 查看当前用户可访问的知识库 |
| `POST /knowledge-bases` | 新建知识库并自动成为 owner |
| `GET /knowledge-bases/{knowledge_base_id}/members` | 查看知识库成员 |
| `POST /knowledge-bases/{knowledge_base_id}/members` | 添加已注册用户为知识库成员 |
| `DELETE /knowledge-bases/{knowledge_base_id}/members/{user_id}` | 移除知识库成员 |
| `GET /knowledge-bases/{knowledge_base_id}/documents` | 查看指定知识库文档列表 |
| `POST /knowledge-bases/{knowledge_base_id}/documents/index` | 上传并索引到指定知识库 |
| `POST /knowledge-bases/{knowledge_base_id}/web-pages/index` | 抓取单个安全 HTML URL 并索引到指定知识库 |
| `POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs` | 上传并创建指定知识库的异步索引任务 |
| `GET /knowledge-bases/{knowledge_base_id}/documents/index-jobs` | 查看指定知识库索引任务列表 |
| `POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs/{job_id}/retry` | 重试失败索引任务 |
| `POST /knowledge-bases/{knowledge_base_id}/snapshots` | 手动创建指定知识库版本快照 |
| `GET /knowledge-bases/{knowledge_base_id}/snapshots` | 查看指定知识库快照列表 |
| `GET /knowledge-bases/{knowledge_base_id}/snapshots/{snapshot_id}` | 查看指定知识库快照详情和文档摘要 |
| `GET /knowledge-bases/{knowledge_base_id}/snapshots/{base_snapshot_id}/diff/{target_snapshot_id}` | 比较两个知识库快照的文档级差异 |
| `POST /documents/index` | 上传并索引文档 |
| `POST /web-pages/index` | 抓取单个安全 HTML URL 并索引到默认知识库 |
| `POST /documents/index-jobs` | 上传并创建默认知识库异步索引任务 |
| `GET /documents` | 查看知识库文档列表 |
| `POST /documents/search` | 只做语义检索 |
| `POST /knowledge-bases/{knowledge_base_id}/rag/ask` | 在指定知识库中执行 RAG 问答 |
| `POST /rag/ask` | 检索后调用 LLM 生成 RAG 回答 |
| `POST /knowledge-bases/{knowledge_base_id}/agent/ask` | 在指定知识库中执行 Agent 问答 |
| `POST /agent/ask` | 可解释 Agent 路由问答 |
| `GET /evaluation/latest` | 查看最近检索评估结果 |
| `POST /evaluation/run` | 运行本地检索评估 |
| `GET /evaluation/runs` | 查看评估历史 run |
| `GET /evaluation/runs/{run_id}` | 查看单次评估完整结果 |
| `POST /evaluation/judge-answer` | 使用当前 LLM profile 对单次回答做结构化质量评分 |
| `POST /feedback/answers` | 提交用户对回答的 up/down 反馈 |
| `GET /settings` | 查看模型、prompt 和运行时设置 |
| `POST /settings/llm-profiles` | 新增 LLM API 配置档案 |

## 简历描述模板

可以这样写：

```text
本地知识库 RAG Agent：基于 FastAPI、fastembed、Qdrant local 和 OpenAI-compatible LLM API 实现多格式文档入库、向量检索、RAG 问答、可解释 Agent 路由和 Web UI 管理。支持 PDF/PDF 表格/PDF 图片 OCR/OCR/Markdown/html/docx/表格等内容解析，提供 sources 可追溯回答、检索评估面板、LLM 多供应商配置和本地 Docker/脚本启动。
```

简历要点可以拆成：

```text
1. 自研 RAG 基础链路：文档解析、chunk、embedding、Qdrant 检索、prompt 组装。
2. 支持多格式知识库：PDF、PDF 表格抽取、PDF 内嵌图片 OCR、扫描型 PDF OCR、Markdown、txt、html/htm、docx、csv、xlsx。
3. 实现可解释 Agent 路由：区分普通聊天、知识库检索、资料不足，并返回调试信息。
4. 增加检索评估能力：维护评估问题集，统计 hit_rate、page_hit_rate、keyword_hit_rate。
5. 构建本地 Web UI：支持文件导入、知识问答、评估面板、知识库管理和模型配置。
```

## 面试讲解要点

讲项目时建议按这个顺序：

```text
1. 先说明为什么不用大框架：为了学习底层 RAG 链路，先自己实现关键步骤。
2. 再讲数据怎么进来：多格式 loader -> ParsedDocument -> chunk -> embedding -> Qdrant。
3. 再讲问题怎么回答：query embedding -> top_k search -> sources -> RAG prompt -> LLM。
4. 再讲如何避免“看起来能答但不可控”：sources 返回、固定输出格式、score_threshold、检索评估。
5. 最后讲工程化扩展：Web UI、LLM profile、Docker、一键启动、后续可接权限和评估历史。
```

如果你还不熟悉 FastAPI 和这一步的基本概念，先读：

- [项目续接规范：新对话 / 新开发者先读](docs/00-project-continuation-guide.md)
- [goal 执行文档规范：开工前先读](docs/goal/README.md)
- [enterprise-goal 企业级改造规划](docs/enterprise-goal/README.md)
- [summary 总结文档规范：完成后记录](docs/summary/README.md)
- [项目演示检查清单](docs/summary/project-demo-checklist.md)
- [项目演示脚本](docs/summary/project-demo-script.md)
- [第 1 步学习笔记：跑通 FastAPI + DeepSeek `/chat`](docs/summary/01-fastapi-chat-step.md)
- [第 2 步学习笔记：配置 API Key 并测试 `/chat`](docs/summary/02-api-key-and-chat-test.md)
- [第 3 步学习笔记：PDF 解析与文件上传接口](docs/summary/03-pdf-extraction-step.md)
- [第 4 步学习笔记：文档切分 chunk](docs/summary/04-document-chunking-step.md)
- [第 5 步学习笔记：Embedding 文本向量化](docs/summary/05-embedding-step.md)
- [第 6 步学习笔记：Qdrant 本地向量存储与检索](docs/summary/06-qdrant-local-index-step.md)
- [第 7 步学习笔记：DeepSeek RAG 问答最小实现](docs/summary/07-rag-answer-step.md)
- [第 8 步进阶路线：从最小 RAG 到个人项目级 RAG Agent](docs/summary/08-rag-agent-advanced-roadmap.md)
- [第 9 步测试规范：RAG 检索与问答质量评估](docs/summary/09-rag-test-spec.md)
- [第 10 步测试结果：最小 RAG 检索与问答基线](docs/summary/10-rag-test-result.md)
- [第 11 步学习笔记：RAG score_threshold 低分过滤](docs/summary/11-rag-score-threshold-step.md)
- [第 12 步学习笔记：RAG sources 返回结构优化](docs/summary/12-rag-sources-response-step.md)
- [第 11/12 步完成总结：score_threshold 与 sources 结构优化](docs/summary/11-12-score-threshold-sources-summary.md)
- [第 13 步学习笔记：固定 RAG 输出格式](docs/summary/13-rag-output-format-step.md)
- [第 13 步完成总结：固定 RAG 输出格式与最小回归测试](docs/summary/13-rag-output-format-summary.md)
- [第 14 步完成总结：建立 RAG 评估问题集](docs/summary/14-rag-evaluation-dataset-summary.md)
- [第 15 步完成总结：chunk 参数和 top_k 评估](docs/summary/15-chunk-topk-parameter-evaluation-summary.md)
- [第 16 步完成总结：知识库文档管理](docs/summary/16-document-management-summary.md)
- [第 17 步完成总结：content_hash 去重与重建索引策略](docs/summary/17-document-dedup-content-hash-summary.md)
- [第 18 步完成总结：Markdown 和 txt 文档入库](docs/summary/18-markdown-txt-loader-summary.md)
- [第 19 步完成总结：docx 与表格类文档解析](docs/summary/19-docx-table-loader-summary.md)
- [第 20 步完成总结：现代风 RAG Web UI 初版](docs/summary/20-modern-web-ui-summary.md)
- [第 21 步完成总结：最小 RAG Agent 工具路由](docs/summary/21-rag-agent-tool-routing-summary.md)
- [第 22 步完成总结：项目测试、收口和最终总结](docs/summary/22-tests-and-project-final-summary.md)
- [第 23 步完成总结：名称、问答交互和回答质量优化](docs/summary/23-ui-answer-quality-refinement-summary.md)
- [第 24 步完成总结：UI 分页与运行时模型设置](docs/summary/24-ui-tabs-runtime-settings-summary.md)
- [第 25 步完成总结：修复 UI Tab 布局混排](docs/summary/25-ui-tab-layout-fix-summary.md)
- [第 26 步完成总结：优化回答 Markdown 展示](docs/summary/26-ui-markdown-answer-rendering-summary.md)
- [第 27 步完成总结：UI 语言和系统色偏好](docs/summary/27-ui-language-theme-preferences-summary.md)
- [第 28 步完成总结：UI 背景颜色偏好](docs/summary/28-ui-background-color-preference-summary.md)
- [第 29 步完成总结：网页标题与项目图标](docs/summary/29-web-title-favicon-summary.md)
- [第 30 步完成总结：背景色作用到整体 UI 面板](docs/summary/30-ui-background-surface-color-summary.md)
- [第 31 步完成总结：一键启动与 Docker 化](docs/summary/31-one-click-start-and-docker-summary.md)
- [第 32 步完成总结：扫描型 PDF OCR 支持](docs/summary/32-scanned-pdf-ocr-summary.md)
- [第 33 步完成总结：多格式文档图片内容抽取与 OCR 统一链路](docs/summary/33-multiformat-image-ocr-loader-summary.md)
- [第 34 步完成总结：RAG 评估脚本与评估面板](docs/summary/34-rag-evaluation-panel-summary.md)
- [第 35 步完成总结：Agent 工具路由增强](docs/summary/35-agent-routing-enhancement-summary.md)
- [第 36 步完成总结：知识库管理能力增强](docs/summary/36-knowledge-base-management-enhancement-summary.md)
- [第 37 步完成总结：多模型供应商与自定义 API 配置](docs/summary/37-multi-provider-llm-config-summary.md)
- [第 38 步完成总结：LLM API 配置档案管理](docs/summary/38-llm-profile-management-summary.md)
- [第 39 步完成总结：中文模式技术标签可读性优化](docs/summary/39-zh-technical-labels-summary.md)
- [第 40 步完成总结：项目演示与简历呈现优化](docs/summary/40-project-demo-and-resume-polish-summary.md)
- [企业级第 01 步完成总结：登录鉴权与用户体系](docs/enterprise-summary/01-auth-and-user-system-summary.md)
- [企业级第 02 步完成总结：数据库持久化替代本地 JSON](docs/enterprise-summary/02-database-persistence-summary.md)
- [企业级第 03 步完成总结：多租户和权限隔离](docs/enterprise-summary/03-tenant-and-permission-isolation-summary.md)
- [企业级第 04 步完成总结：异步索引任务](docs/enterprise-summary/04-async-indexing-job-summary.md)
- [企业级第 05 步完成总结：服务化 Qdrant 和索引状态检查](docs/enterprise-summary/05-enterprise-vector-store-summary.md)
- [企业级第 06 步完成总结：审计日志与基础观测](docs/enterprise-summary/06-audit-and-observability-summary.md)
- [企业级第 07 步完成总结：评估历史和质量治理](docs/enterprise-summary/07-evaluation-and-quality-governance-summary.md)
- [企业级第 08 步完成总结：部署、环境和密钥治理](docs/enterprise-summary/08-deployment-and-secret-governance-summary.md)
- [企业级第 09 步完成总结：运行安全边界和限流](docs/enterprise-summary/09-runtime-safety-and-limits-summary.md)
- [企业级第 10 步完成总结：原始文件存储治理](docs/enterprise-summary/10-source-file-storage-governance-summary.md)
- [企业级第 11 步完成总结：知识库版本快照](docs/enterprise-summary/11-knowledge-base-versioning-summary.md)
- [企业级第 12 步完成总结：知识库快照差异比较](docs/enterprise-summary/12-knowledge-base-snapshot-diff-summary.md)
- [企业级第 13 步完成总结：用户注册与管理员开通](docs/enterprise-summary/13-user-registration-and-provisioning-summary.md)
- [企业级第 14 步完成总结：知识库成员共享管理](docs/enterprise-summary/14-knowledge-base-member-management-summary.md)
- [企业级第 15 步完成总结：Web UI 账号和成员管理](docs/enterprise-summary/15-web-ui-account-and-member-management-summary.md)
- [企业级第 16 步完成总结：LLM-as-a-judge 回答质量评估](docs/enterprise-summary/16-llm-answer-quality-judge-summary.md)
- [企业级第 17 步完成总结：PDF 表格抽取治理](docs/enterprise-summary/17-pdf-table-extraction-governance-summary.md)
- [企业级第 18 步完成总结：PDF 内嵌图片 OCR 治理](docs/enterprise-summary/18-pdf-embedded-image-ocr-summary.md)
- [企业级第 19 步完成总结：HTML 网页正文入库治理](docs/enterprise-summary/19-html-web-page-body-loader-summary.md)
- [企业级第 20 步完成总结：安全单 URL 网页入库](docs/enterprise-summary/20-safe-url-web-page-ingestion-summary.md)

后续实现必须先读对应 goal，再写代码，完成后写 summary。

后续 goal 执行路线：

- [第 13 步执行目标：固定 RAG 输出格式](docs/goal/13-rag-output-format-goal.md)
- [第 14 步执行目标：建立 RAG 评估问题集](docs/goal/14-rag-evaluation-dataset-goal.md)
- [第 15 步执行目标：评估 chunk 参数和 top_k](docs/goal/15-chunk-topk-parameter-evaluation-goal.md)
- [第 16 步执行目标：新增知识库文档管理能力](docs/goal/16-document-management-goal.md)
- [第 17 步执行目标：增加 content_hash 去重与重建索引策略](docs/goal/17-document-dedup-content-hash-goal.md)
- [第 18 步执行目标：支持 Markdown 和 txt 文档入库](docs/goal/18-markdown-txt-loader-goal.md)
- [第 19 步执行目标：支持 docx 与表格类文档的最小解析](docs/goal/19-docx-table-loader-goal.md)
- [第 20 步执行目标：实现现代风 RAG Web UI](docs/goal/20-modern-web-ui-goal.md)
- [第 21 步执行目标：实现最小 RAG Agent 工具路由](docs/goal/21-rag-agent-tool-routing-goal.md)
- [第 22 步执行目标：项目测试、收口和最终总结](docs/goal/22-tests-and-project-final-summary-goal.md)
- [第 23 步执行目标：名称、问答交互和回答质量优化](docs/goal/23-ui-answer-quality-refinement-goal.md)
- [第 24 步执行目标：UI 分页与运行时模型设置](docs/goal/24-ui-tabs-runtime-settings-goal.md)
- [第 25 步执行目标：修复 UI Tab 布局混排](docs/goal/25-ui-tab-layout-fix-goal.md)
- [第 26 步执行目标：优化回答 Markdown 展示](docs/goal/26-ui-markdown-answer-rendering-goal.md)
- [第 27 步执行目标：UI 语言和系统色偏好](docs/goal/27-ui-language-theme-preferences-goal.md)
- [第 28 步执行目标：UI 背景颜色偏好](docs/goal/28-ui-background-color-preference-goal.md)
- [第 29 步执行目标：网页标题与项目图标](docs/goal/29-web-title-favicon-goal.md)
- [第 30 步执行目标：背景色作用到整体 UI 面板](docs/goal/30-ui-background-surface-color-goal.md)
- [第 31 步执行目标：一键启动与 Docker 化](docs/goal/31-one-click-start-and-docker-goal.md)
- [第 32 步执行目标：扫描型 PDF OCR 支持](docs/goal/32-scanned-pdf-ocr-goal.md)
- [第 33 步执行目标：多格式文档图片内容抽取与 OCR 统一链路](docs/goal/33-multiformat-image-ocr-loader-goal.md)
- [第 34 步执行目标：RAG 评估脚本与评估面板](docs/goal/34-rag-evaluation-panel-goal.md)
- [第 35 步执行目标：Agent 工具路由增强](docs/goal/35-agent-routing-enhancement-goal.md)
- [第 36 步执行目标：知识库管理能力增强](docs/goal/36-knowledge-base-management-enhancement-goal.md)
- [第 37 步执行目标：多模型供应商与自定义 API 配置](docs/goal/37-multi-provider-llm-config-goal.md)
- [第 38 步执行目标：LLM API 配置档案管理](docs/goal/38-llm-profile-management-goal.md)
- [第 39 步执行目标：中文模式技术标签可读性优化](docs/goal/39-zh-technical-labels-goal.md)
- [第 40 步执行目标：项目演示与简历呈现优化](docs/goal/40-project-demo-and-resume-polish-goal.md)

## 快速唤醒本地 RAG

如果这台电脑已经配置过 `.venv` 和 `.env`，只是换了一个终端、重启了电脑、或者隔了一段时间要继续使用，直接执行：

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后访问：

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

说明：

- `Web UI` 用来做文件上传、知识库列表、RAG 提问和 sources 查看。
- `Swagger Docs` 用来直接测试 API，后续所有接口仍然必须保证能在 `/docs` 页面测试。
- 项目默认端口固定使用 `8000`，后续不要随意改成 `8001`、`8002`。

如果改了代码，希望服务自动重载，可以用：

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

也可以使用项目脚本检查环境并启动：

```powershell
.\scripts\check_environment.ps1
.\scripts\start.ps1
```

开发时需要自动重载：

```powershell
.\scripts\start.ps1 -Reload
```

## 首次部署 / 换电脑后恢复

如果是别人 clone 项目，或者你换了一台新电脑，需要从仓库根目录进入本项目：

```powershell
cd ai-std/projects/rag-pdf-qa
```

### 1. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 配置 API Key

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`。新版本优先使用通用 `LLM_*` 配置：

```text
APP_ENV=development
APP_SECRET_KEY=change-this-local-development-secret
SECRET_ENCRYPTION_KEY=replace-with-random-secret-before-deploy
USER_REGISTRATION_ENABLED=true
MAX_UPLOAD_BYTES=10485760
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
SOURCE_STORAGE_ENABLED=true
SOURCE_STORAGE_BACKEND=local
SOURCE_STORAGE_PATH=data/source_files
WEB_FETCH_ENABLED=true
WEB_FETCH_TIMEOUT_SECONDS=10
WEB_FETCH_MAX_BYTES=2097152
WEB_FETCH_ALLOW_PRIVATE_HOSTS=false
LLM_PROVIDER=deepseek
LLM_API_KEY=你的真实模型 API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
DATABASE_URL=sqlite:///data/app.db
REDIS_URL=redis://127.0.0.1:6379/0
INDEX_JOB_STORAGE_PATH=data/index_jobs
```

旧的 `DEEPSEEK_*` 变量仍然兼容，但后续建议新环境统一使用 `LLM_*`。

企业级分支默认使用 SQLite 保存用户、文档 metadata、运行时设置和 LLM profile。后续可以把 `DATABASE_URL` 切换为 PostgreSQL，例如：

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/rag
```

不要把真实 API Key 写进 README、docs、测试文件或提交到 GitHub。
如果要给局域网其他人访问，请把 `APP_ENV` 改为 `production`，并替换 `APP_SECRET_KEY`、`SECRET_ENCRYPTION_KEY` 和数据库密码。

### 3. 启动本地 RAG 服务

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

或者使用一键启动脚本：

```powershell
.\scripts\start.ps1
```

默认使用 Qdrant local 模式，不需要单独启动 Qdrant Docker。首次索引文档时会在本地生成 `.qdrant/` 数据目录。

如果要把向量库切到服务化 Qdrant，可以先启动 Compose 中的 Qdrant：

```powershell
docker compose up -d qdrant
```

然后在 `.env` 中设置：

```text
QDRANT_MODE=server
QDRANT_URL=http://127.0.0.1:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_PREFIX=rag
QDRANT_COLLECTION=rag_chunks
```

`QDRANT_COLLECTION` 仍然兼容旧配置；如果不显式设置，会按 `QDRANT_COLLECTION_PREFIX` 生成默认 collection，例如 `rag_chunks`。向量 payload 会写入 `tenant_id`、`workspace_id`、`knowledge_base_id` 和 `document_id`，检索与删除都会带租户/知识库过滤。

### Docker 启动

如果本机已经安装 Docker，也可以在项目根目录用 Compose 启动 API、PostgreSQL、Qdrant 和 Redis：

```powershell
docker compose up --build
```

后台运行：

```powershell
docker compose up --build -d
```

完整部署说明见 [docs/deployment.md](docs/deployment.md)。Docker 构建不会打包 `.env`、`.qdrant/`、本地数据库、`data/index_jobs/` 或其他运行数据。

### 4. 打开使用入口

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

### 5. 重新建立本地知识库

GitHub 仓库不会提交你的本地运行数据：

```text
.env
.qdrant/
data/app.db
data/index_jobs/
data/source_files/
data/*.db
data/runtime_settings.json  # legacy
data/documents.json         # legacy
```

所以换电脑或别人首次使用时，需要重新上传文档建立知识库。

可以在 Web UI 上传，也可以在 Swagger Docs 里调用：

```text
POST /documents/index-jobs  # 推荐，异步任务
POST /documents/index       # 兼容旧同步接口
POST /web-pages/index       # 单 URL HTML 网页入库
```

当前支持入库的文件类型：

```text
PDF / PDF 表格 / PDF 图片 OCR / 扫描型 PDF OCR / Markdown / txt / html / htm / 单 URL HTML 网页 / docx / docx 图片 OCR / csv / xlsx
```

推荐索引参数：

```text
chunk_size = 800
overlap = 100
top_k = 5
```

## 常见启动问题

### 8000 端口被占用

如果启动时提示 8000 端口被占用，先确认是不是旧的 uvicorn 服务还在运行：

```powershell
Get-NetTCPConnection -LocalPort 8000
```

也可以查看对应进程：

```powershell
Get-Process -Id <PID>
```

通常处理方式：

```text
1. 先关闭旧的 uvicorn 终端
2. 再重新执行 uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### `/docs` 看不到新接口

这通常说明旧服务没有重启。

处理方式：

```text
停止旧 uvicorn
重新启动 8000 服务
刷新 http://127.0.0.1:8000/docs
```

### `/rag/ask` 没有命中资料

先不要直接改 prompt，建议按顺序检查：

```text
1. GET /documents 是否能看到文档
2. POST /documents/search 是否能检索到相关 chunk
3. top_k 是否太小
4. score_threshold 是否太高
5. 文档是否真的已经重新入库
```

## 局域网访问

如果想让同一局域网的其他电脑访问，可以改成：

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

然后在其他电脑访问：

```text
http://你的电脑IP:8000/docs
```

注意：企业级分支已经有登录鉴权、用户注册/管理员开通、数据库持久化、知识库级隔离、审计观测、部署密钥治理和基础安全边界；但还没有复杂 RBAC、企业 SSO、Kubernetes 生产编排和完整运维工作流，仍建议先在本机或可信内网使用。

## 测试接口

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{ message = "用一句话解释什么是 RAG" } | ConvertTo-Json)
```

## 当前已经实现

- `GET /health`：健康检查
- `POST /chat`：调用当前配置的 LLM Provider Chat Completions
- `POST /documents/extract`：上传 PDF 并提取文本，支持 `enable_ocr=true` 对扫描型 PDF 做 OCR，支持 `extract_tables=true` 抽取 PDF 表格预览，支持 `enable_image_ocr=true` 抽取 PDF 内嵌图片文字
- `POST /documents/chunk`：上传 PDF 并切分文本块，支持 OCR 页面来源、`pdf_table` 表格来源和 `pdf_image_ocr` 图片 OCR 来源标记
- `POST /embeddings/text`：把文本转换成 embedding 向量
- `POST /documents/index`：上传 PDF / PDF 表格 / PDF 内嵌图片 OCR / 扫描型 PDF OCR / Markdown / txt / html / docx / csv / xlsx，切分并写入 Qdrant，支持 `content_hash` 去重、`reindex`、`extract_tables` 和 `enable_image_ocr`
- `POST /web-pages/index`：抓取单个安全 HTML URL，默认阻止 localhost、私网和非 HTML 响应，并复用 HTML loader 入库
- `GET /documents`：查看本地知识库文档列表
- `GET /documents/{document_id}`：查看单个文档 metadata
- `DELETE /documents/{document_id}`：删除某个文档在 Qdrant 中的 chunks 和 metadata
- `DELETE /documents/batch`：批量删除多个文档的 Qdrant chunks 和 metadata
- `POST /documents/{document_id}/reindex`：为指定 document_id 上传替换文件并重新索引
- `POST /documents/search`：用问题检索本地 Qdrant 里的相关 chunk，支持 `document_id` / `file_type` 过滤
- `POST /rag/ask`：检索本地 Qdrant，并把相关 chunk 交给当前 LLM Provider 生成 RAG 回答，支持限定 `document_id`
- `GET /` / `GET /app`：打开本地 RAG Web UI
- `GET /settings`：读取本地运行时 LLM 设置，不返回真实 API Key
- `GET /settings/vector-store/status`：读取 Qdrant 模式、collection、点数和 metadata 一致性状态，不返回真实 API Key
- `GET /audit-logs`：查看最近审计事件，包含 request_id、user_id、action、resource、duration 和 usage 摘要
- `GET /metrics`：查看文档数、索引任务状态、审计事件数和审计失败数等基础指标
- `PUT /settings`：保存本地运行时 LLM、API Key 和 RAG prompt 设置
- `POST /agent/ask`：可解释 Agent 工具路由，自动选择 `chat` / `rag` / `insufficient_context`，支持限定 `document_id`，返回 `route_reason`、`tools_used`、`routing_debug`
- `GET /evaluation/questions`：读取本地 RAG 评估问题集
- `POST /evaluation/run`：运行本地检索评估并保存最近结果，不调用 LLM
- `GET /evaluation/latest`：读取最近一次 RAG 检索评估结果
- `GET /evaluation/runs`：查看评估历史 run，可按知识库筛选
- `GET /evaluation/runs/{run_id}`：查看单次评估完整结果
- `POST /evaluation/judge-answer`：使用当前 LLM profile 对单次回答做 LLM-as-a-judge 结构化评分，并写入审计和数据库
- `POST /feedback/answers`：提交用户对回答的 up/down 反馈
- `/rag/ask` 支持 `score_threshold` 低分过滤
- `/rag/ask` 的 `sources` 已优化为 `source_id` + `preview` 结构
- `/rag/ask` 的 `reply` 已通过 prompt 约束为“答案 / 依据 / 资料不足之处”三段式格式
- 已建立 15 条 RAG 评估问题和 baseline 检索记录
- 已完成 chunk/top_k 参数评估，当前推荐 `chunk_size=800`、`overlap=100`、`top_k=5`
- 已增强知识库文档管理能力，支持 `document_id`、列表、详情、删除、批量删除和指定文档重建索引
- 已新增 `content_hash` 去重和 `reindex=true` 重建索引策略
- 已支持 Markdown 和 txt 文档入库
- 已支持 html/htm 网页正文文件入库，跳过 script/style/nav/header/footer 等噪声内容
- 已支持安全单 URL HTML 网页入库，默认限制私网地址、响应大小、超时和 content-type
- 已支持 docx、csv、xlsx 文档入库
- 已新增本地 Web UI 入口，用于上传文档、查看知识库、提问和查看 sources
- 已增强 RAG Agent 工具路由接口 `/agent/ask`，可返回路由理由、工具使用和调试信息
- 已新增 RAG 检索评估脚本、API 和 Web UI 评估面板
- Web UI 知识问答页已支持 RAG / Agent 模式切换，并展示 Agent 路由理由和工具使用情况
- Web UI 知识库管理区已支持文件名/类型筛选、详情查看、批量删除、单文档重新索引和提问限定文档
- Web UI 已拆分为“文件导入 / 知识问答 / 设置”三个页签
- Web UI 已修复 Tab 混排问题，当前左侧为明确的垂直功能导航
- Web UI 已支持轻量 Markdown 回答渲染，避免直接显示 `**` 和代码围栏
- Web UI 已支持中文 / English 切换和系统色偏好设置
- Web UI 中文模式已支持技术标签“中文含义 + 英文术语”展示
- Web UI 已支持背景颜色偏好设置
- Web UI 背景颜色已覆盖左侧导航、主面板、表单、卡片和回答区域
- Web UI 已新增科技感项目图标和浏览器 Tab 标题优化
- 已新增 `scripts/check_environment.ps1` 和 `scripts/start.ps1`，支持本地环境检查和一键启动
- 已新增 Dockerfile 和 `.dockerignore`，支持最小 Docker 启动且不打包本地密钥和运行数据
- PDF 入库已支持可选表格抽取：`extract_tables=true`，表格 chunk 标记为 `pdf_table`
- PDF 入库已支持可选内嵌图片 OCR：`enable_image_ocr=true`，图片 OCR chunk 标记为 `pdf_image_ocr`
- PDF 入库已支持可选 OCR：`enable_ocr=true`、`ocr_language=chi_sim+eng`
- docx 入库已支持可选图片 OCR：`enable_image_ocr=true`
- RAG sources 已返回 `extraction_method`，可区分 `text`、`table`、`pdf_table`、`pdf_ocr`、`pdf_image_ocr`、`image_ocr`
- 已支持在设置页选择 DeepSeek、Qwen、Doubao、OpenAI、Claude compatible、Ollama、MiniMax 或自定义 OpenAI-compatible API
- 已支持在设置页调整当前 LLM Provider 的 base_url、model、timeout、API Key 和 RAG prompt
- 已支持多个 LLM API 配置档案，支持新增、编辑、删除和一键启用
- 企业级分支已新增登录鉴权和用户开通：`/auth/bootstrap-admin`、`/auth/register`、`/auth/login`、`/auth/me`、`/auth/logout`、`/admin/users`，并用 Bearer token 保护文档、问答、评估和设置等核心接口
- 企业级分支已新增 SQLAlchemy 数据库持久化，`users`、`documents`、`runtime_settings`、`llm_profiles` 不再以本地 JSON 作为主存储
- 企业级分支已新增最小多租户隔离和成员共享：`knowledge_bases`、membership、成员管理 API、文档归属字段和 Qdrant `knowledge_base_id` payload 过滤
- 企业级分支已新增异步索引任务：`index_jobs`、后台入库、状态查询、失败原因和 retry
- 企业级分支已支持 Qdrant local/server 模式切换、collection prefix 配置、Qdrant Compose 服务和 `/settings/vector-store/status` 状态检查
- 企业级分支已新增审计与基础观测：`audit_logs`、`X-Request-ID`、结构化请求日志、`/audit-logs`、`/metrics`，并记录 RAG/Agent 检索耗时、LLM 耗时、provider/model 和 token usage
- 企业级分支已新增评估质量治理：`evaluation_runs`、`evaluation_cases` 知识库归属、评估历史 API、quality_gate、答案反馈 `/feedback/answers`、LLM-as-a-judge `/evaluation/judge-answer` 和 Web UI 评估历史
- 企业级分支已新增部署和密钥治理：Compose 编排 `api/db/qdrant/redis`、`/health` 启动检查、生产环境告警、数据库内 LLM API Key 加密存储和部署文档
- 企业级分支已新增运行安全边界：可配置 `MAX_UPLOAD_BYTES`、基础请求限流、429 `Retry-After` 和 `/health` 安全配置可见性
- 企业级分支已新增原始文件存储治理：本地 source storage、documents 源文件引用 metadata、Compose volume 持久化和迁移 `006_source_file_storage`
- 已建立最小 pytest 回归测试骨架
- `.env` 配置读取
- 请求超时控制
- LLM 客户端异常转换
- 返回 token usage，方便后续做成本统计

## 测试最小 RAG 问答

先索引 PDF：

```powershell
$pdf = "D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf"

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/documents/index" `
  -Method Post `
  -Form @{ file = Get-Item $pdf; chunk_size = 800; overlap = 100 }
```

如果当前 PowerShell 不支持 `-Form` 参数，可以用 `curl.exe`：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/index" `
  -F "file=@D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf" `
  -F "chunk_size=800" `
  -F "overlap=100"
```

如果是扫描型 PDF，可以打开 OCR：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/index" `
  -F "file=@D:\path\to\scanned.pdf" `
  -F "chunk_size=800" `
  -F "overlap=100" `
  -F "enable_ocr=true" `
  -F "ocr_language=chi_sim+eng"
```

Windows 如果 `tesseract.exe` 不在 PATH，可以在 `.env` 中设置：

```text
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

再基于本地知识库提问：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/rag/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    question = "GUI Agent 的核心流程是什么？"
    limit = 5
    score_threshold = 0.5
  } | ConvertTo-Json)
```

## 运行本地 RAG 检索评估

评估脚本只调用本地 embedding 和本地 Qdrant，不调用 LLM：

```powershell
.\.venv\Scripts\python.exe scripts\run_rag_evaluation.py
```

运行后会更新：

```text
data/eval/latest_rag_evaluation.json
data/eval/latest_rag_evaluation.md
```

也可以在 Web UI 左侧进入“检索评估”，或在 Swagger Docs 中测试：

```text
GET /evaluation/questions
POST /evaluation/run
GET /evaluation/latest
```

## 当前状态

当前主线已经收口为：

```text
本地 RAG Agent 初版
```

当前 `enterprise-rag-platform` 分支已经完成：

```text
企业级第 01 步：登录鉴权与用户体系
企业级第 02 步：数据库持久化替代本地 JSON
企业级第 03 步：多租户和权限隔离
企业级第 04 步：异步索引任务
企业级第 05-16 步：向量库治理、审计观测、质量治理、部署密钥治理、运行安全、源文件存储、知识库快照、快照差异比较、用户注册与管理员开通、知识库成员共享管理、Web UI 账号与成员管理、LLM-as-a-judge 回答质量评估
```

执行顺序保持：

```text
先读 goal
再写代码
最后写 summary
同步更新 README 和 00 号文档
```

企业级第 01-16 步已完成当前规划闭环的一部分。后续如果继续新增企业级目标，建议先补 `docs/enterprise-goal/NN-*.md`，再按 goal -> code -> tests -> summary 的节奏推进。

