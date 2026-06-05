# Local Knowledge RAG Agent

当前目标：把本地多格式知识库 RAG 闭环，逐步升级成可管理、可评估、可交互的个人项目级 RAG Agent 工具。

如果你还不熟悉 FastAPI 和这一步的基本概念，先读：

- [项目续接规范：新对话 / 新开发者先读](docs/00-project-continuation-guide.md)
- [goal 执行文档规范：开工前先读](docs/goal/README.md)
- [summary 总结文档规范：完成后记录](docs/summary/README.md)
- [项目演示检查清单](docs/summary/project-demo-checklist.md)
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
- [第 38 步执行目标：项目演示与简历呈现优化](docs/goal/38-project-demo-and-resume-polish-goal.md)

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
LLM_PROVIDER=deepseek
LLM_API_KEY=你的真实模型 API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

旧的 `DEEPSEEK_*` 变量仍然兼容，但后续建议新环境统一使用 `LLM_*`。

不要把真实 API Key 写进 README、docs、测试文件或提交到 GitHub。

### 3. 启动本地 RAG 服务

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

或者使用一键启动脚本：

```powershell
.\scripts\start.ps1
```

本项目使用的是 Qdrant local 模式，不需要单独启动 Qdrant Docker。首次索引文档时会在本地生成 `.qdrant/` 数据目录。

### Docker 启动

如果本机已经安装 Docker，也可以在项目根目录执行：

```powershell
docker build -t local-rag-agent .
docker run --rm -p 8000:8000 --env-file .env local-rag-agent
```

Docker 构建不会打包 `.env`、`.qdrant/`、`data/documents.json` 或 `data/runtime_settings.json`。

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
data/documents.json
data/runtime_settings.json
```

所以换电脑或别人首次使用时，需要重新上传文档建立知识库。

可以在 Web UI 上传，也可以在 Swagger Docs 里调用：

```text
POST /documents/index
```

当前支持入库的文件类型：

```text
PDF / 扫描型 PDF OCR / Markdown / txt / docx / docx 图片 OCR / csv / xlsx
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

注意：当前项目还没有登录鉴权，只建议本机或可信内网学习使用。

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
- `POST /documents/extract`：上传 PDF 并提取文本，支持 `enable_ocr=true` 对扫描型 PDF 做 OCR
- `POST /documents/chunk`：上传 PDF 并切分文本块，支持 OCR 页面来源标记
- `POST /embeddings/text`：把文本转换成 embedding 向量
- `POST /documents/index`：上传 PDF / 扫描型 PDF OCR / Markdown / txt / docx / csv / xlsx，切分并写入本地 Qdrant，支持 `content_hash` 去重和 `reindex`
- `GET /documents`：查看本地知识库文档列表
- `GET /documents/{document_id}`：查看单个文档 metadata
- `DELETE /documents/{document_id}`：删除某个文档在 Qdrant 中的 chunks 和 metadata
- `DELETE /documents/batch`：批量删除多个文档的 Qdrant chunks 和 metadata
- `POST /documents/{document_id}/reindex`：为指定 document_id 上传替换文件并重新索引
- `POST /documents/search`：用问题检索本地 Qdrant 里的相关 chunk，支持 `document_id` / `file_type` 过滤
- `POST /rag/ask`：检索本地 Qdrant，并把相关 chunk 交给当前 LLM Provider 生成 RAG 回答，支持限定 `document_id`
- `GET /` / `GET /app`：打开本地 RAG Web UI
- `GET /settings`：读取本地运行时 LLM 设置，不返回真实 API Key
- `PUT /settings`：保存本地运行时 LLM、API Key 和 RAG prompt 设置
- `POST /agent/ask`：可解释 Agent 工具路由，自动选择 `chat` / `rag` / `insufficient_context`，支持限定 `document_id`，返回 `route_reason`、`tools_used`、`routing_debug`
- `GET /evaluation/questions`：读取本地 RAG 评估问题集
- `POST /evaluation/run`：运行本地检索评估并保存最近结果，不调用 LLM
- `GET /evaluation/latest`：读取最近一次 RAG 检索评估结果
- `/rag/ask` 支持 `score_threshold` 低分过滤
- `/rag/ask` 的 `sources` 已优化为 `source_id` + `preview` 结构
- `/rag/ask` 的 `reply` 已通过 prompt 约束为“答案 / 依据 / 资料不足之处”三段式格式
- 已建立 15 条 RAG 评估问题和 baseline 检索记录
- 已完成 chunk/top_k 参数评估，当前推荐 `chunk_size=800`、`overlap=100`、`top_k=5`
- 已增强知识库文档管理能力，支持 `document_id`、列表、详情、删除、批量删除和指定文档重建索引
- 已新增 `content_hash` 去重和 `reindex=true` 重建索引策略
- 已支持 Markdown 和 txt 文档入库
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
- Web UI 已支持背景颜色偏好设置
- Web UI 背景颜色已覆盖左侧导航、主面板、表单、卡片和回答区域
- Web UI 已新增科技感项目图标和浏览器 Tab 标题优化
- 已新增 `scripts/check_environment.ps1` 和 `scripts/start.ps1`，支持本地环境检查和一键启动
- 已新增 Dockerfile 和 `.dockerignore`，支持最小 Docker 启动且不打包本地密钥和运行数据
- PDF 入库已支持可选 OCR：`enable_ocr=true`、`ocr_language=chi_sim+eng`
- docx 入库已支持可选图片 OCR：`enable_image_ocr=true`
- RAG sources 已返回 `extraction_method`，可区分 `text`、`table`、`pdf_ocr`、`image_ocr`
- 已支持在设置页选择 DeepSeek、Qwen、Doubao、OpenAI、Claude compatible、Ollama、MiniMax 或自定义 OpenAI-compatible API
- 已支持在设置页调整当前 LLM Provider 的 base_url、model、timeout、API Key 和 RAG prompt
- 已新增运行时设置文件 `data/runtime_settings.json`，该文件不提交 GitHub
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

执行顺序保持：

```text
先读 goal
再写代码
最后写 summary
同步更新 README 和 00 号文档
```

后续如果继续扩展，不要直接堆复杂多 Agent。当前建议从第 38 步“项目演示与简历呈现优化”继续推进。

