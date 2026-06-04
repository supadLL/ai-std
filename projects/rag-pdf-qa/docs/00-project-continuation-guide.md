# 项目续接规范：Local Knowledge RAG Agent

这份文档用于：

> 让任何新的对话、新的开发者、后续的自己，都能快速理解本项目当前状态，并按统一规范继续学习、调优和编写代码。

如果你是在一个新的 Codex / AI 对话窗口里继续这个项目，建议先让它阅读：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
docs/summary/08-rag-agent-advanced-roadmap.md
app/main.py
app/deepseek_client.py
app/vector_store.py
app/runtime_settings.py
```

---

## 1. 项目当前定位

当前项目名称：

```text
Local Knowledge RAG Agent
```

当前目标：

```text
学习并实现一个本地多格式知识库 RAG Agent 工具。
```

当前已经完成：

```text
FastAPI 服务
DeepSeek /chat 调用
PDF 文本提取
PDF chunk 切分
fastembed 本地 embedding
Qdrant 本地向量索引
Qdrant 语义检索
DeepSeek RAG 问答最小实现
RAG score_threshold 低分过滤
RAG sources 返回结构优化
RAG reply 固定三段式输出格式
RAG 评估问题集和 baseline 检索记录
chunk/top_k 参数评估，推荐 800/100/top_k=5
知识库文档管理：列表、详情、删除、document_id
content_hash 去重与 reindex 重建索引策略
Markdown / txt 文档入库
docx / csv / xlsx 文档入库
现代风本地 Web UI 初版
最小 RAG Agent 工具路由：/agent/ask
名称、问答交互和回答质量优化
Web UI 分页：文件导入 / 知识问答 / 设置
Web UI Tab 布局混排修复
Web UI 回答轻量 Markdown 渲染
Web UI 中文 / English 切换和系统色偏好
Web UI 背景颜色偏好
Web UI 科技感项目图标和浏览器 Tab 标题优化
Web UI 背景色覆盖整体 UI 面板
运行时 LLM 设置：base_url、model、timeout、API Key 和 RAG prompt
最小 pytest 回归测试骨架
```

当前阶段：

```text
本地 RAG Agent 初版
```

当前主线已经完成一次项目级收口。

后续优化路线见：

```text
docs/goal/README.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

---

## 2. 重要原则

### 先读项目，再写代码

任何新对话或新开发者继续本项目时，都应该先读：

```text
README.md
docs/
app/main.py
app/config.py
app/deepseek_client.py
app/embedding_client.py
app/vector_store.py
app/text_splitter.py
app/pdf_extractor.py
```

不要只根据一句需求直接改代码。

### 保持学习型项目节奏

本项目不是只追求“能跑”，还要追求：

```text
每一步为什么做
做了什么
怎么测试
有什么限制
下一步是什么
```

所以每次完成一个阶段，都要补对应 docs。

### 先 goal，再代码，最后 summary

后续新增重要步骤时，必须按这个顺序：

```text
1. 先在 docs/goal/ 写执行目标文档
2. 再根据 goal 修改代码
3. 最后在 docs/summary/ 写完成总结
4. 同步更新 README 和 00 号续接规范
```

不要再只采用“先写代码，后补说明”的方式。

### 不要过早引入复杂框架

当前阶段暂时不要主动引入：

- LangChain 大封装
- LlamaIndex 大封装
- 多 Agent 框架
- Graph 工作流
- 复杂前端
- 云端部署

除非路线文档明确进入对应阶段，或者用户明确要求。

当前优先级是：

```text
RAG 检索质量
chunk 调参
prompt 调优
sources 可解释性
异常处理
多文档管理
最小 Agent 工具调用
```

---

## 3. 服务运行规范

本项目默认使用：

```text
http://127.0.0.1:8000
```

后续不要随意改到 8001、8002。

如果服务已经在 8000 运行，但代码更新后 `/docs` 看不到新接口，说明旧服务没有重启。

正确做法：

```text
停止旧 uvicorn
重新在 8000 启动服务
```

启动命令：

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

验证：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/app
http://127.0.0.1:8000/docs
```

Swagger Docs 页面必须能测试接口。

---

## 4. 当前核心接口

| 接口 | 作用 |
|---|---|
| `GET /health` | 健康检查 |
| `POST /chat` | 直接调用 DeepSeek |
| `POST /documents/extract` | 上传 PDF 并提取文本 |
| `POST /documents/chunk` | 上传 PDF 并切分 chunk |
| `POST /embeddings/text` | 文本向量化 |
| `POST /documents/index` | PDF / Markdown / txt / docx / csv / xlsx 切分、向量化并写入 Qdrant，支持 content_hash 去重和 reindex |
| `GET /documents` | 查看本地知识库文档列表 |
| `GET /documents/{document_id}` | 查看单个文档 metadata |
| `DELETE /documents/{document_id}` | 删除某个文档的 Qdrant chunks 和 metadata |
| `POST /documents/search` | 只做语义检索，不调用 DeepSeek |
| `POST /rag/ask` | 检索 Qdrant，再调用 DeepSeek 生成 RAG 回答 |
| `POST /agent/ask` | 最小 Agent 工具路由，自动选择 chat / rag / insufficient_context |
| `GET /` / `GET /app` | 打开本地 RAG Web UI |
| `GET /settings` | 读取本地运行时 LLM 设置，不返回真实 API Key |
| `PUT /settings` | 保存本地运行时 LLM、API Key 和 RAG prompt 设置 |

测试顺序建议：

```text
1. GET /health
2. POST /documents/index
3. GET /documents
4. POST /documents/search
5. POST /rag/ask
```

调试 RAG 时，不要一上来只看 `/rag/ask`。

应该先看 `/documents/search` 是否命中正确 chunk。

---

## 5. 代码结构说明

```text
app/
  main.py              FastAPI 路由、请求响应模型、RAG 问答入口
  config.py            .env 配置读取
  deepseek_client.py   DeepSeek Chat Completions 调用封装
  embedding_client.py  fastembed 本地 embedding 封装
  document_loaders.py  Markdown / txt / docx / csv / xlsx 文档解析
  pdf_extractor.py     PDF 文本提取
  text_splitter.py     PDF 文本 chunk 切分
  vector_store.py      Qdrant 本地 collection、upsert、search
  runtime_settings.py  本地运行时 LLM 和 RAG prompt 设置
```

当前不使用 LangChain。

这是刻意的：

> 先理解底层 RAG 链路，再考虑是否引入框架。

---

## 6. 代码编写规范

### 优先沿用现有风格

本项目目前风格是：

```text
函数小而直接
模块职责清晰
FastAPI + Pydantic 定义接口结构
错误用自定义 Error 类转换为 HTTPException
耗时同步任务用 run_in_threadpool
```

新增功能时，优先放在对应已有模块。

不要为了小功能创建过多抽象。

### 命名规范

建议：

```text
请求模型：XxxRequest
响应模型：XxxResponse
错误类：XxxError
内部辅助函数：_xxx
```

例如：

```python
class RagAskRequest(BaseModel):
    ...

class RagAskResponse(BaseModel):
    ...

def _build_rag_messages(...):
    ...
```

### 异常处理规范

底层模块抛自己的错误：

```text
PdfExtractionError
TextSplitError
EmbeddingError
VectorStoreError
DeepSeekClientError
```

FastAPI 路由层负责转成：

```text
HTTPException
```

不要在底层模块直接依赖 FastAPI。

### 不要泄露敏感信息

不要把这些内容写进 docs 或日志：

```text
DEEPSEEK_API_KEY
完整 .env
data/runtime_settings.json
真实 token
私有文件内容
```

---

## 7. 文档编写规范

本项目 docs 是学习笔记风格，不是单纯 API 文档。

每一步文档建议包含：

```text
标题
这一步的目标
当前新增接口或能力
为什么需要这一步
这一步新增了哪些代码
接口怎么测试
返回结果怎么看
常见错误
当前还没做什么
下一步建议
```

推荐结构：

````markdown
# 第 N 步学习笔记：标题

这一步的目标是：

> ...

当前新增：

```text
POST /xxx
```

---

## 1. 为什么需要这一步

...

## 2. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|

## 3. 如何在 Swagger Docs 测试

...

## 4. 常见错误

...

## 5. 下一步

...
````

写 docs 时要注意：

- 尽量用中文解释概念
- 保留关键英文术语，例如 RAG、chunk、embedding、top_k
- 每个接口都要说明怎么在 `/docs` 页面测试
- 不要只写结论，要解释为什么
- 不要写太多和当前阶段无关的高级概念

---

## 8. 新增阶段文档规范

如果新增一个阶段，例如第 9 步，应创建：

```text
docs/summary/09-xxx-step.md
```

如果这个阶段需要写代码，还应先创建：

```text
docs/goal/09-xxx-goal.md
```

完成后再创建：

```text
docs/summary/09-xxx-summary.md
```

然后更新：

```text
README.md
```

在 README 的学习笔记列表里加入：

```markdown
- 第 9 步学习笔记：xxx -> docs/summary/09-xxx-step.md
```

如果是路线图、规范、评估报告，不一定叫 step。

可以使用：

```text
00-project-continuation-guide.md
08-rag-agent-advanced-roadmap.md
09-rag-test-spec.md
10-rag-test-result.md
goal/13-rag-output-format-goal.md
summary/11-12-score-threshold-sources-summary.md
```

---

## 9. 每次改代码后的验证规范

每次改完代码，至少执行：

```powershell
python -m compileall app
```

如果服务相关代码变化，还要验证：

```text
GET /health
GET /openapi.json
GET /docs
```

如果新增接口，要确认：

```text
新接口出现在 /docs 页面
```

如果接口会调用 DeepSeek：

```text
不要随便自动调用，避免消耗 token
除非用户明确要求测试真实调用
```

---

## 10. RAG 调优规范

调 RAG 时按顺序来：

```text
1. 先看 /documents/search
2. 再看 /rag/ask
3. 先调 chunk_size / overlap / top_k
4. 再调 RAG prompt
5. 最后考虑 Agent
```

不要一上来就改 prompt。

因为如果检索结果错了，prompt 很难救回来。

建议每次调优都记录：

```text
问题
期望页码
top_k
命中的 chunk_id
score
RAG 回答是否正确
使用的参数
```

当前测试规范和测试结果写到：

```text
docs/summary/09-rag-test-spec.md
docs/summary/10-rag-test-result.md
```

---

## 11. Agent 实现规范

当前已经实现最小 Agent 工具路由：

```text
POST /agent/ask
```

当前不要直接上复杂多 Agent。

当前最小工具选择：

```text
用户问题
-> 判断是否需要检索
-> 如果需要，调用 search_documents
-> 基于 sources 回答
-> 如果不需要，走普通 chat
```

最小工具可以是：

```text
search_documents(query, limit)
answer_with_context(question, sources)
direct_chat(question)
```

当前 route 可能是：

```text
chat
rag
insufficient_context
```

后续继续扩展 Agent 前，仍然先补文档，再写代码。

---

## 12. 新对话续接提示词

如果后续新开一个 AI 对话，可以直接复制下面这段：

```text
请先阅读这个项目：
D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa

重点阅读：
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
app/main.py
app/deepseek_client.py
app/vector_store.py

这是一个学习型本地 RAG 项目，技术栈是 FastAPI + DeepSeek API + fastembed + 本地 Qdrant。

当前已经实现最小 RAG：
PDF 提取 -> chunk 切分 -> embedding -> Qdrant 索引/检索 -> DeepSeek 基于 sources 回答。

后续规划已经纳入：
PDF OCR / 表格抽取 / 图片处理、网页正文等更多知识库输入，以及 Web UI Agent 模式切换和更完整回答质量评估。

当前已经支持：
PDF、Markdown、txt、docx、csv、xlsx 入库，并提供 http://127.0.0.1:8000/app Web UI、/agent/ask 最小 Agent 路由、/settings 运行时 LLM 和 prompt 设置。

请注意：
1. 服务默认使用 8000，不要随便换端口。
2. 每次新增阶段都要补 docs，并更新 README。
3. Swagger Docs 页面必须能测试接口。
4. 不要过早引入 LangChain、多 Agent、Graph 工作流。
5. 每次项目阶段变化，都要同步更新 docs/00-project-continuation-guide.md。
6. 后续重要步骤必须先写 docs/goal/*.md，再写代码，完成后写 docs/summary/*.md。
7. 后续优化先按 docs/goal/README.md 和当前 goal 文件执行，再参考 docs/summary/08-rag-agent-advanced-roadmap.md。

在修改代码前，请先说明你读到了当前哪些模块和当前项目处于什么阶段。
```

---

## 13. 当前优先级

当前 `rag-pdf-qa` 主线已经收口。后续如果继续扩展，必须先创建新的 goal 文档。

当前可优先从这些方向选择：

```text
扫描型 PDF OCR
PDF 表格和图片信息抽取
Web UI Agent 模式切换
Agent route_reason 和更稳定的工具选择
回答质量评估集
Docker 化或一键启动脚本
```

完整后续执行路线：

| 步骤 | goal 文档 | 目标 |
|---:|---|---|
| 13 | `docs/goal/13-rag-output-format-goal.md` | 固定 RAG 输出格式 |
| 14 | `docs/goal/14-rag-evaluation-dataset-goal.md` | 建立 RAG 评估问题集 |
| 15 | `docs/goal/15-chunk-topk-parameter-evaluation-goal.md` | 评估 chunk 参数和 top_k |
| 16 | `docs/goal/16-document-management-goal.md` | 新增知识库文档管理能力 |
| 17 | `docs/goal/17-document-dedup-content-hash-goal.md` | 增加 content_hash 去重与重建索引策略 |
| 18 | `docs/goal/18-markdown-txt-loader-goal.md` | 支持 Markdown 和 txt 文档入库 |
| 19 | `docs/goal/19-docx-table-loader-goal.md` | 支持 docx 与表格类文档的最小解析 |
| 20 | `docs/goal/20-modern-web-ui-goal.md` | 实现现代风 RAG Web UI |
| 21 | `docs/goal/21-rag-agent-tool-routing-goal.md` | 实现最小 RAG Agent 工具路由 |
| 22 | `docs/goal/22-tests-and-project-final-summary-goal.md` | 项目测试、收口和最终总结 |
| 23 | `docs/goal/23-ui-answer-quality-refinement-goal.md` | 名称、问答交互和回答质量优化 |
| 24 | `docs/goal/24-ui-tabs-runtime-settings-goal.md` | UI 分页与运行时模型设置 |
| 25 | `docs/goal/25-ui-tab-layout-fix-goal.md` | 修复 UI Tab 布局混排 |
| 26 | `docs/goal/26-ui-markdown-answer-rendering-goal.md` | 优化回答 Markdown 展示 |
| 27 | `docs/goal/27-ui-language-theme-preferences-goal.md` | UI 语言和系统色偏好 |
| 28 | `docs/goal/28-ui-background-color-preference-goal.md` | UI 背景颜色偏好 |
| 29 | `docs/goal/29-web-title-favicon-goal.md` | 网页标题与项目图标 |
| 30 | `docs/goal/30-ui-background-surface-color-goal.md` | 背景色作用到整体 UI 面板 |

执行节奏保持：

```text
读当前 goal
-> 写代码或测试
-> 写 summary
-> 更新 README 和 00 号文档
```

不要偏离主线。

本项目的主线是：

```text
通过自己实现 RAG 链路，理解 AI Agent 工程化的底层能力。
```

---

## 14. 当前支持范围和未来扩展

当前已经支持：

```text
PDF 文本型文档
Markdown / txt 文本文档
docx 文档
csv / xlsx 表格文件
RAG score_threshold 低分过滤
RAG sources 返回 source_id、score、filename、page_number、chunk_id、preview
Web UI 初版
/agent/ask 最小 Agent 工具路由
Web UI 分页
Web UI Tab 页面隔离和垂直导航
Web UI 回答 Markdown 展示
Web UI 语言和系统色偏好
Web UI 背景颜色偏好
Web UI 项目图标和 Tab 标题
Web UI 背景色覆盖左侧导航、主面板、表单、卡片和回答区域
/settings 运行时设置
```

当前还没有支持：

```text
扫描型 PDF OCR
PDF 表格抽取
PDF 图片/图表理解
网页正文
```

这些都已经纳入后续规划。

后续扩展方向见：

```text
docs/summary/03-pdf-extraction-step.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

建议后续统一抽象：

```text
DocumentLoader
ParsedDocument
ParsedSection
TextChunk
```

目标是让不同输入格式都能进入同一条 RAG 链路：

```text
文件输入
-> loader 解析
-> 统一 ParsedDocument
-> chunk
-> embedding
-> Qdrant
-> RAG/Agent
```

---

## 15. UI 方向规划

当前主要入口：

```text
http://127.0.0.1:8000/app
http://127.0.0.1:8000/docs
```

其中 `/app` 是本地 Web UI，`/docs` 是 Swagger 接口测试页面。

当前已经有 Web UI，并拆分为：

```text
文件导入
知识问答
设置
```

`设置`页已经支持配置 LLM 接入参数和 RAG prompt。

UI 目标：

```text
现代风
玻璃质感
圆角风格
桌面端优先
网页端可访问
```

当前 UI 已经实现：

```text
文件上传
知识库文件列表
聊天式问题输入和 RAG 回答展示
sources 展示
top_k / score_threshold 参数调节
token usage 展示
运行时 base_url / model / timeout / API Key 设置
RAG system prompt / answer instructions 编辑
```

当前布局：

```text
左侧：主功能页签
文件导入页：上传与文档列表
知识问答页：聊天区 + sources / debug
设置页：LLM 参数与 prompt
```

UI 是后续展示项目的重要方向，但不要早于 RAG 检索质量评估。

---

## 16. 00 号文档同步规范

每当项目进入新阶段，都要同步更新本文件。

需要更新的情况：

```text
新增核心接口
新增文档类型支持
新增 UI 能力
新增 Agent 能力
修改默认端口或启动方式
修改项目当前阶段判断
调整后续优先级
```

更新时至少检查：

```text
项目当前定位是否准确
当前已完成能力是否准确
当前还没做的能力是否准确
后续优先级是否准确
新对话续接提示词是否需要更新
```

这个文件的作用是减少新窗口和新对话的上下文损耗。

所以它必须始终保持最新。

