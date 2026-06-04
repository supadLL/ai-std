# 项目演示检查清单：Local Knowledge RAG Agent

这份清单用于演示、换电脑复现、或新对话接手前快速确认项目是否处于可用状态。

---

## 1. 启动前检查

确认本地存在：

```text
.venv/
.env
requirements.txt
```

`.env` 至少需要：

```text
DEEPSEEK_API_KEY=你的真实 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
QDRANT_LOCAL_PATH=.qdrant
QDRANT_COLLECTION=rag_chunks
```

注意：

```text
.env 不提交到 GitHub
.qdrant/ 不提交到 GitHub
data/documents.json 不提交到 GitHub
data/runtime_settings.json 不提交到 GitHub
```

---

## 2. 启动服务

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

开发时需要自动重载：

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 3. 打开入口

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

必须确认：

```text
/health 返回 {"status": "ok"}
/docs 能打开 Swagger
/app 能打开 Web UI
```

---

## 4. 推荐演示路径

### 4.1 上传并索引文档

入口：

```text
Web UI 左侧上传区
或 Swagger Docs -> POST /documents/index
```

推荐参数：

```text
chunk_size = 800
overlap = 100
reindex = false
```

支持文件：

```text
.pdf
.md
.markdown
.txt
.docx
.csv
.xlsx
```

### 4.2 查看知识库

入口：

```text
Web UI 左侧文档列表
或 Swagger Docs -> GET /documents
```

需要看到：

```text
document_id
filename
file_type
chunk_count
content_hash_prefix
```

### 4.3 只做检索

入口：

```text
Swagger Docs -> POST /documents/search
```

请求示例：

```json
{
  "query": "GUI Agent 的核心流程是什么？",
  "limit": 5
}
```

检查：

```text
results 不为空
score 有值
filename / page_number / chunk_id / text 可读
```

### 4.4 RAG 问答

入口：

```text
Web UI -> 知识问答
或 Swagger Docs -> POST /rag/ask
```

请求示例：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

检查：

```text
reply 使用“答案 / 依据 / 资料不足之处”
sources 包含 source_id、score、filename、page_number、chunk_id、preview
usage 返回 token 使用信息
```

### 4.5 调整模型和 Prompt

入口：

```text
Web UI -> 设置
或 Swagger Docs -> GET /settings / PUT /settings
```

检查：

```text
可以看到 base_url、model、timeout
可以编辑 RAG system prompt 和 answer instructions
API Key 输入框加载后为空
GET /settings 不返回真实 API Key
保存后 data/runtime_settings.json 仍然不被 git 跟踪
```

### 4.6 Agent 问答

入口：

```text
Swagger Docs -> POST /agent/ask
```

知识库问题：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

预期：

```text
route = rag
sources 不为空
```

普通聊天：

```json
{
  "question": "你好"
}
```

预期：

```text
route = chat
sources = []
```

资料不足：

```json
{
  "question": "请根据知识库回答 FireDragon-404 是什么？",
  "limit": 5
}
```

预期：

```text
route = insufficient_context
reply 明确提示资料不足
```

---

## 5. 自动化验证

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

当前基线：

```text
pytest 28 passed
```

测试覆盖：

```text
文档解析
文本切分
Qdrant collection 维度处理
知识库 metadata store
documents/search
rag/ask prompt 格式
Web UI 路由
agent/ask 三条 route
OpenAPI / Swagger Docs
运行时 settings 接口
```

---

## 6. 评估基线

当前已有：

```text
data/eval/rag_eval_cases.json
data/eval/rag_eval_result-baseline.json
data/eval/chunk_topk_eval_result.json
data/eval/chunk_topk_eval_result.md
```

当前推荐参数：

```text
chunk_size = 800
overlap = 100
top_k = 5
```

baseline 指标：

```text
case_count = 15
scored_case_count = 14
hit_rate = 1.0000
page_hit_rate = 0.8571
keyword_hit_rate = 1.0000
```

说明：

```text
评估主要验证检索命中，不代表最终回答质量已经完美。
```

---

## 7. 当前限制

```text
扫描型 PDF OCR 尚未实现
PDF 图片/图表理解尚未实现
PDF 表格精细抽取尚未实现
网页正文抓取尚未实现
Agent 路由仍是启发式规则
Web UI 尚未接入 Agent 模式切换
运行时设置目前是本地单机 JSON 文件
没有登录鉴权和多用户隔离
没有云端部署
```

---

## 8. 演示时的一句话

```text
这是一个基于 FastAPI、DeepSeek、fastembed 和本地 Qdrant 的个人 RAG Agent 项目，支持多格式文档入库、向量检索、基于 sources 的回答、Web UI 操作和最小 Agent 工具路由。
```
