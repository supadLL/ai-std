# RAG PDF QA

当前目标：把最小本地 PDF RAG 闭环，逐步升级成可管理、可评估、可交互的个人项目级 RAG Agent 工具。

如果你还不熟悉 FastAPI 和这一步的基本概念，先读：

- [项目续接规范：新对话 / 新开发者先读](docs/00-project-continuation-guide.md)
- [goal 执行文档规范：开工前先读](docs/goal/README.md)
- [summary 总结文档规范：完成后记录](docs/summary/README.md)
- [下一步 goal：第 20 步现代风 RAG Web UI](docs/goal/20-modern-web-ui-goal.md)
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

## 1. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. 配置 API Key

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`：

```text
DEEPSEEK_API_KEY=你的真实 DeepSeek API Key
```

## 3. 启动 / 唤醒本地 RAG 服务

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

服务地址：

```text
http://127.0.0.1:8000
```

Swagger 测试页面：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

如果只是换了一个新终端，项目依赖和 `.env` 已经配置过，只需要：

```powershell
cd ai-std/projects/rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

如果 8000 端口被旧服务占用，先关闭旧终端，或在 PowerShell 中查看占用进程：

```powershell
Get-NetTCPConnection -LocalPort 8000
```

## 4. 其他人 clone 后如何启用

别人从 GitHub 拉取项目后，不会带有你的本地运行数据：

```text
.env
.qdrant/
data/documents.json
```

所以首次使用必须重新做三件事：

```text
1. 创建 .venv 并安装 requirements.txt
2. 创建 .env 并写入自己的 DEEPSEEK_API_KEY
3. 通过 POST /documents/index 上传 PDF，重新建立本地知识库
```

本项目使用的是 Qdrant local 模式，不需要单独启动 Qdrant Docker。

如果想让同一局域网的其他电脑访问，可以改成：

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

然后在其他电脑访问：

```text
http://你的电脑IP:8000/docs
```

注意：当前项目还没有登录鉴权，只建议本机或可信内网学习使用。

## 5. 测试接口

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{ message = "用一句话解释什么是 RAG" } | ConvertTo-Json)
```

## 当前已经实现

- `GET /health`：健康检查
- `POST /chat`：调用 DeepSeek Chat Completions
- `POST /documents/extract`：上传 PDF 并提取文本
- `POST /documents/chunk`：上传 PDF 并切分文本块
- `POST /embeddings/text`：把文本转换成 embedding 向量
- `POST /documents/index`：上传 PDF / Markdown / txt / docx / csv / xlsx，切分并写入本地 Qdrant，支持 `content_hash` 去重和 `reindex`
- `GET /documents`：查看本地知识库文档列表
- `GET /documents/{document_id}`：查看单个文档 metadata
- `DELETE /documents/{document_id}`：删除某个文档在 Qdrant 中的 chunks 和 metadata
- `POST /documents/search`：用问题检索本地 Qdrant 里的相关 chunk
- `POST /rag/ask`：检索本地 Qdrant，并把相关 chunk 交给 DeepSeek 生成 RAG 回答
- `/rag/ask` 支持 `score_threshold` 低分过滤
- `/rag/ask` 的 `sources` 已优化为 `source_id` + `preview` 结构
- `/rag/ask` 的 `reply` 已通过 prompt 约束为“答案 / 依据 / 资料不足之处”三段式格式
- 已建立 15 条 RAG 评估问题和 baseline 检索记录
- 已完成 chunk/top_k 参数评估，当前推荐 `chunk_size=800`、`overlap=100`、`top_k=5`
- 已新增最小知识库文档管理能力，支持 `document_id`、列表、详情和删除
- 已新增 `content_hash` 去重和 `reindex=true` 重建索引策略
- 已支持 Markdown 和 txt 文档入库
- 已支持 docx、csv、xlsx 文档入库
- 已建立最小 pytest 回归测试骨架
- `.env` 配置读取
- 请求超时控制
- DeepSeek 异常转换
- 返回 token usage，方便后续做成本统计

## 6. 测试最小 RAG 问答

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

## 下一步

下一步从 [第 20 步：实现现代风 RAG Web UI](docs/goal/20-modern-web-ui-goal.md) 开始。

执行顺序保持：

```text
先读 goal
再写代码
最后写 summary
同步更新 README 和 00 号文档
```

当前仍然先不要急着做复杂 Agent。先把现代 Web UI 做出来，让知识库上传、检索、问答和 sources 展示可视化。

