# AI Study 🚀

这是一个用于系统学习 AI Agent、RAG 和大模型工程化的实践仓库。

仓库目标不是只看课程或做零散 demo，而是通过一个个可运行、可测试、可复盘的小项目，把后端工程能力逐步迁移到 AI 应用开发中。

---

## 这个仓库在做什么 🧭

当前主线：

```text
后端基础
-> FastAPI 服务
-> LLM API 接入
-> Embedding / 向量数据库
-> RAG 检索问答
-> 多文档知识库
-> UI 交互页面
-> 最小 AI Agent 工具路由
```

学习重点：

- 🧠 理解 AI Agent 和 RAG 的底层链路
- 🛠️ 用真实代码实现可运行项目
- 📚 为每一步补充 goal / summary 文档
- 🧪 用测试和评估记录项目质量
- 🔐 保护 API Key，不把真实密钥推送到仓库

---

## 当前重点项目 📌

### `projects/rag-pdf-qa`

本地多格式知识库 RAG Agent 项目。

技术栈：

```text
FastAPI
DeepSeek API
fastembed
Qdrant local
pytest
```

当前已经实现：

- ✅ DeepSeek `/chat` 最小调用
- ✅ PDF 文本提取
- ✅ chunk 文本切分
- ✅ fastembed 本地向量化
- ✅ Qdrant 本地向量索引与语义检索
- ✅ `/rag/ask` 最小 RAG 问答
- ✅ `score_threshold` 低分过滤
- ✅ sources 返回结构优化
- ✅ RAG 回答固定为“答案 / 依据 / 资料不足之处”
- ✅ 最小 pytest 回归测试
- ✅ 15 条 RAG 评估问题和 baseline 检索记录
- ✅ chunk/top_k 参数评估，当前推荐 `800/100/top_k=5`
- ✅ 最小知识库文档管理：列表、详情、删除、`document_id`
- ✅ `content_hash` 去重与 `reindex=true` 重建索引策略
- ✅ Markdown 和 txt 文档入库
- ✅ docx、csv、xlsx 文档入库
- ✅ 本地 Web UI 初版
- ✅ Web UI 分页：文件导入、知识问答、设置
- ✅ 最小 RAG Agent 工具路由
- ✅ 运行时 LLM 设置和 RAG prompt 调整
- ✅ `docs/goal` 和 `docs/summary` 文档工作流

下一步：

```text
当前 rag-pdf-qa 主线已收口为本地 RAG Agent 初版
```

入口文档：

- [rag-pdf-qa README](projects/rag-pdf-qa/README.md)
- [项目续接规范](projects/rag-pdf-qa/docs/00-project-continuation-guide.md)
- [goal 执行文档](projects/rag-pdf-qa/docs/goal/README.md)
- [summary 总结文档](projects/rag-pdf-qa/docs/summary/README.md)

---

## 如何启动当前 RAG 项目 🖥️

进入项目目录：

```powershell
cd projects/rag-pdf-qa
```

如果是第一次使用：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

然后在 `.env` 中写入自己的 DeepSeek API Key：

```text
DEEPSEEK_API_KEY=你的真实 DeepSeek API Key
```

如果本机已经配置过环境，只是重新唤醒本地 RAG：

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

常用入口：

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

完整启动、换电脑恢复、端口占用处理见：

- [rag-pdf-qa 启动说明](projects/rag-pdf-qa/README.md)

---

## 目录结构 🗂️

```text
ai-std/
├── README.md
├── 01-ai-agent-learning-roadmap.md
├── projects/
│   ├── rag-pdf-qa/
│   └── customer-service-agent/
├── interview/
└── notes/
```

说明：

- `projects/`：项目代码和项目文档
- `interview/`：面试准备材料
- `notes/`：学习笔记
- `01-ai-agent-learning-roadmap.md`：AI Agent 学习阶段路线

---

## 项目推进方式 🧩

重要项目统一使用下面的节奏：

```text
先写 goal
-> 再写代码
-> 跑测试和验证
-> 最后写 summary
-> 更新 README / 续接文档
```

这样做是为了减少新对话、新窗口、新阶段接手项目时的上下文损耗。

---

## 安全约定 🔐

不要提交真实 API Key。

本仓库会提交：

```text
.env.example
```

不会提交：

```text
.env
.venv/
.qdrant/
data/runtime_settings.json
.pytest_cache/
__pycache__/
```

真实配置只放在本地 `.env` 或被忽略的本地运行时设置文件中。

---

## 一句话总结 ✨

这个仓库记录的是：

> 从后端工程师视角，一步一步把 LLM、RAG、向量数据库、测试、文档和 Agent 工程化串起来的学习实践。
