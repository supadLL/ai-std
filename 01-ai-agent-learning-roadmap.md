# AI Agent 学习路线

这份文档用于描述从后端工程能力过渡到 AI Agent / RAG 工程能力的学习阶段。

它不再按固定时间拆分，而是按“能力阶段”推进。每个阶段都应该有明确产出：代码、测试、文档、总结和可复盘的技术判断。

---

## 1. 路线定位

当前学习主线是：

```text
后端工程基础
-> LLM API 接入
-> RAG 本地知识库
-> 检索质量评估
-> 多格式文档解析
-> Web UI
-> 最小 Agent 工具路由
-> 项目总结和面试表达
```

这个路线的目标不是堆框架，而是把 AI 应用背后的关键链路自己走一遍。

---

## 2. 当前项目状态

当前重点项目：

```text
projects/rag-pdf-qa
```

它已经完成了纯文本 PDF 的本地 RAG MVP：

```text
PDF 文本提取
-> chunk 切分
-> fastembed 向量化
-> Qdrant 本地索引
-> Qdrant 语义检索
-> DeepSeek 基于 sources 回答
```

当前已经不是“准备实现 RAG”，而是进入：

```text
RAG 质量评估
参数调优
多文档管理
多格式知识库扩展
UI 和 Agent 化
```

---

## 3. 学习原则

### 项目优先

优先做能运行、能测试、能展示的项目。

不要只停留在：

```text
看教程
记概念
堆框架名词
```

每个阶段都要留下：

```text
代码
测试
文档
问题记录
下一步目标
```

### 先理解底层链路

当前不急着依赖 LangChain、LlamaIndex、Dify、Coze 这类大封装。

可以学习它们的设计，但项目早期更重要的是自己理解：

```text
请求如何进入系统
文档如何解析
文本如何切分
embedding 如何生成
向量如何存储和检索
LLM 如何基于 context 回答
sources 如何解释答案来源
失败时如何降级
```

### 文档和代码同等重要

后续重要阶段都采用：

```text
先写 goal
-> 再写代码
-> 跑测试
-> 写 summary
-> 更新 README / 续接文档
```

这能减少新对话、新窗口、新阶段接手项目时的上下文损耗。

---

## 4. 阶段一：LLM API 和后端服务基础

目标：

```text
能用 FastAPI 暴露接口，并稳定调用 DeepSeek API。
```

核心能力：

- FastAPI 路由
- Pydantic 请求和响应模型
- `.env` 配置读取
- DeepSeek Chat Completions 调用
- 超时和异常处理
- token usage 返回
- Swagger Docs 测试接口

当前对应产出：

```text
GET /health
POST /chat
```

项目状态：

```text
已完成
```

---

## 5. 阶段二：纯文本 PDF RAG 闭环

目标：

```text
完成纯文本 PDF 的本地知识库问答闭环。
```

核心链路：

```text
PDF
-> 文本提取
-> chunk 切分
-> embedding
-> Qdrant upsert
-> query embedding
-> Qdrant search
-> RAG prompt
-> DeepSeek answer
-> sources
```

当前对应接口：

```text
POST /documents/extract
POST /documents/chunk
POST /embeddings/text
POST /documents/index
POST /documents/search
POST /rag/ask
```

项目状态：

```text
已完成最小 MVP
```

后续不再把“实现 RAG”作为目标，而是把它当作基础能力继续调优。

---

## 6. 阶段三：RAG 质量评估和调优

目标：

```text
让 RAG 从“能回答”变成“可评估、可调优、可解释”。
```

核心任务：

- 建立 RAG 评估问题集
- 标注期望命中的页码、关键词或 source
- 记录 `top_k` 命中情况
- 对比 `chunk_size`、`overlap`、`top_k`
- 记录 `score_threshold` 的影响
- 固定 RAG 输出格式
- 区分“检索失败”和“模型回答失败”

关键指标：

```text
Hit@K
source_count
retrieved_count
score 分布
回答是否引用正确 source
资料不足时是否拒绝编造
```

当前已经完成：

```text
第 16 步：知识库文档管理
```

后续进入：

```text
第 17 步：content_hash 去重与重建索引策略
```

---

## 7. 阶段四：知识库管理能力

目标：

```text
从“上传文件后直接问答”升级为“可以管理本地知识库”。
```

核心能力：

- 文档列表
- 文档详情
- 删除文档
- 重建索引
- `document_id`
- `content_hash` 去重
- chunk 参数记录
- embedding 模型记录
- collection 元数据记录

推荐先保持简单：

```text
本地 JSON metadata store
```

不要过早引入复杂数据库。

---

## 8. 阶段五：多格式文档解析

目标：

```text
让知识库不再局限于纯文本 PDF。
```

建议扩展顺序：

```text
Markdown
txt
docx
csv / xlsx
扫描型 PDF OCR
PDF 表格
PDF 图片 / 图表
网页正文
```

统一抽象：

```text
DocumentLoader
ParsedDocument
ParsedSection
TextChunk
```

不同格式最终都进入同一条链路：

```text
loader 解析
-> 统一结构
-> chunk
-> embedding
-> Qdrant
-> RAG / Agent
```

### 非文本 PDF 的处理思路

扫描型 PDF：

```text
PDF page image
-> OCR
-> 文本清洗
-> chunk
-> embedding
```

PDF 表格：

```text
表格抽取
-> 行列结构保留
-> 转成文本摘要或结构化 chunk
```

PDF 图片 / 图表：

```text
图片提取
-> 图像描述或多模态理解
-> caption 入库
```

注意：

```text
非文本 PDF 不是直接向量化 PDF 文件本身。
必须先把可理解的信息抽取成文本、结构化数据或图像描述。
```

---

## 9. 阶段六：Web UI

目标：

```text
从 Swagger Docs 测试升级为可交互的本地 RAG 应用。
```

第一版 UI 建议包含：

- 文件上传
- 文档列表
- 问题输入
- RAG 回答展示
- sources 展示
- `top_k` 控制
- `score_threshold` 控制
- token usage 展示
- 检索调试信息

布局方向：

```text
左侧：知识库文档
中间：问答区
右侧：sources / debug panel
底部：输入框和参数控制
```

视觉方向：

```text
现代风
玻璃质感
圆角
桌面端优先
网页端可访问
```

---

## 10. 阶段七：最小 RAG Agent

目标：

```text
让系统具备最小工具路由能力，而不是每个问题都固定走 RAG。
```

最小 Agent 流程：

```text
用户问题
-> 判断是否需要知识库
-> 需要：调用 search_documents
-> 基于 sources 回答
-> 不需要：走普通 chat
```

建议工具：

```text
search_documents(query, limit, score_threshold)
answer_with_context(question, sources)
direct_chat(question)
```

先不要做复杂多 Agent。

当前更重要的是让一个 Agent 能把工具选择这件事讲清楚、测清楚。

---

## 11. 阶段八：工程化质量

目标：

```text
让项目可以被别人理解、运行、测试和继续开发。
```

需要持续补：

- pytest
- API 测试
- RAG 评估记录
- README
- goal 文档
- summary 文档
- 错误处理
- 安全说明
- API Key 保护
- 本地数据忽略规则

每次改完代码至少验证：

```powershell
python -m compileall app tests
python -m pytest
```

涉及接口时还要验证：

```text
GET /health
GET /openapi.json
GET /docs
```

---

## 12. 阶段九：项目表达和面试准备

目标：

```text
能把项目讲清楚，而不是只说“我做了一个 RAG”。
```

需要能回答：

- 为什么选 FastAPI？
- 为什么先不用 LangChain？
- chunk_size 怎么选？
- overlap 有什么作用？
- top_k 怎么调？
- score_threshold 有什么影响？
- 检索失败怎么判断？
- LLM 幻觉怎么减少？
- sources 怎么设计？
- Qdrant collection 维度冲突怎么处理？
- 扫描型 PDF 为什么需要 OCR？
- 多格式文档如何统一进一条 RAG 链路？
- Agent 和固定 RAG 流程有什么区别？

项目表达模板：

```text
这个项目基于 FastAPI、DeepSeek、fastembed 和 Qdrant，
实现了本地文档知识库的 RAG 问答链路。
当前已支持纯文本 PDF 的解析、切分、向量化、索引、检索和基于 sources 的回答生成。
后续扩展方向包括 RAG 评估、多格式文档解析、OCR、文档管理、Web UI 和最小 Agent 工具路由。
```

---

## 13. 当前优先级

当前已经完成：

```text
纯文本 PDF 本地 RAG MVP
RAG 评估问题集和 baseline 检索记录
chunk/top_k 参数评估
知识库文档管理
```

当前最应该继续做：

```text
1. 增加 content_hash 去重与重建索引策略
2. 支持 Markdown / txt
3. 支持 docx / csv / xlsx
4. 规划扫描型 PDF OCR
5. 建立 Web UI
6. 实现最小 RAG Agent 工具路由
```

不要回到“从零学 RAG”的状态。

现在的主线是：

```text
把已经跑通的 RAG MVP 打磨成个人项目级 RAG Agent 工具。
```
