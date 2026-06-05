# 项目演示脚本：Local Knowledge RAG Agent

这份脚本用于面试、给同事演示、或新环境复现时快速讲清楚项目。

推荐演示时长：

```text
5 到 10 分钟
```

---

## 1. 开场介绍

可以这样说：

```text
这是一个本地知识库 RAG Agent 项目。
我没有一开始使用 LangChain 或 LlamaIndex，而是自己实现文档解析、chunk、embedding、Qdrant 检索、RAG prompt、sources 返回、Agent 路由和 Web UI。
目标是学习并掌握 AI Agent 工程链路中的关键底层能力。
```

强调边界：

```text
它是个人项目级工具，不是企业级平台。
当前没有登录鉴权、多用户隔离和云端权限系统。
```

---

## 2. 启动项目

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

给同事同网段访问时：

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 3. 展示 Web UI

先展示左侧导航：

```text
文件导入
知识问答
检索评估
设置
```

重点说明：

```text
Web UI 是本地调试和演示入口。
Swagger Docs 是 API 测试入口，所有接口仍然保持可测试。
```

---

## 4. 演示文档入库

在 `文件导入` 页上传一个文档。

推荐参数：

```text
分块大小 chunk = 800
重叠长度 overlap = 100
重新索引 reindex = false
```

解释：

```text
chunk 控制每段文本长度。
overlap 让相邻文本块保留上下文连续性。
reindex 用于替换已经入库的同一文档。
```

支持格式：

```text
PDF / 扫描型 PDF OCR / Markdown / txt / docx / docx 图片 OCR / csv / xlsx
```

---

## 5. 展示 RAG 问答

在 `知识问答` 页输入一个和文档有关的问题。

演示重点：

```text
1. 先检索 Qdrant，而不是直接问 LLM。
2. 检索结果会作为 sources 传给 LLM。
3. 回答固定为“答案 / 依据 / 资料不足之处”。
4. sources 可以追溯 filename、page_number、chunk_id、score、preview。
```

可以说：

```text
如果检索结果错了，prompt 很难救回来，所以我单独做了 /documents/search 和 evaluation 面板来观察检索质量。
```

---

## 6. 展示 Agent 模式

切换到 Agent 模式后说明：

```text
当前 Agent 不是复杂多 Agent 框架，而是最小可解释工具路由。
它会判断问题应该走普通 chat、RAG 检索，还是资料不足。
```

可解释字段：

```text
route
route_reason
tools_used
routing_debug
```

讲解重点：

```text
我更关注“为什么调用这个工具”，而不是只返回一个最终答案。
```

---

## 7. 展示检索评估

进入 `检索评估` 页。

说明：

```text
这里不调用 LLM，只评估 retrieval。
主要看 top_k 命中、页码命中、关键词命中和低分结果。
```

指标：

```text
hit_rate
page_hit_rate
keyword_hit_rate
low_score_count
```

可以说：

```text
这一步是为了避免 RAG 只靠主观感觉调参。
```

---

## 8. 展示模型配置

进入 `设置` 页。

说明：

```text
这里可以管理多个 LLM API 配置档案。
比如 DeepSeek、Qwen、Ollama、自定义 OpenAI-compatible API。
真实 API Key 不会在接口和页面中返回，只显示掩码。
```

重点：

```text
当前启用的 LLM profile 会作为 /chat、/rag/ask、/agent/ask 的底层模型配置。
```

---

## 9. 面试问答准备

### 为什么不直接用 LangChain？

```text
这个项目的目的不是最快搭出 demo，而是学习 RAG 底层链路。
所以我先自己实现 loader、splitter、embedding、vector store、prompt 和 API，再考虑是否引入框架。
```

### 怎么判断 RAG 回答可靠？

```text
我做了三层约束：
1. sources 返回，回答必须基于检索内容。
2. 固定输出格式，明确答案、依据和资料不足。
3. evaluation 面板评估检索命中，不只看最终回答。
```

### 如果要继续做成更完整的产品，你会怎么做？

```text
1. 增加登录鉴权和多用户知识库隔离。
2. 增加评估历史和回答质量 LLM-as-a-judge。
3. 增加网页正文、图片图表理解和更好的表格抽取。
4. 增加异步任务队列，处理大文件入库。
5. 增加部署脚本和可观测日志。
```

---

## 10. 一句话收尾

```text
这个项目体现的是我对 RAG 工程链路的完整理解：数据如何进入知识库、如何被检索、如何被 LLM 使用、如何解释和评估结果，以及如何做成本地可交互工具。
```
