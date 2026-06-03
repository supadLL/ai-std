# 第 8 步进阶路线：从最小 RAG 到个人项目级 RAG Agent

这份文档的目标是：

> 把当前最小本地 RAG 检索工具，逐步升级成一个可以作为个人项目展示的 RAG Agent 工具。

当前项目已经完成：

```text
PDF 上传
-> 文本提取
-> chunk 切分
-> fastembed 向量化
-> Qdrant 本地索引
-> Qdrant 语义检索
-> DeepSeek 基于检索资料回答
```

但它现在还只是最小 RAG 闭环。

还没有达到“个人项目级 RAG Agent”的标准。

---

## 1. 当前项目处于什么阶段

当前阶段可以定义为：

```text
最小本地 RAG MVP
```

它证明了核心链路能跑通：

```text
问题 -> 检索 -> 拼上下文 -> LLM 回答 -> 返回 sources
```

这一步的价值是学习底层链路。

但如果要作为个人项目展示，还需要继续补：

- 检索质量评估
- RAG prompt 调优
- chunk 参数调优
- 错误处理和降级
- sources 可解释性
- 多文档管理
- 简单 Agent 工具调用
- 测试和项目文档
- 可演示的使用体验

---

## 2. 最小 RAG 和 RAG Agent 的区别

### 当前最小 RAG

当前链路是固定的：

```text
用户问题
-> 一定去 Qdrant 检索
-> 一定把结果交给 DeepSeek
-> 返回回答
```

它更像：

```text
RAG 问答接口
```

### 个人项目级 RAG Agent

Agent 会多一层“决策能力”：

```text
用户问题
-> 判断是否需要检索
-> 选择工具
-> 执行工具
-> 观察工具结果
-> 决定是否继续检索或回答
-> 返回最终答案
```

它更像：

```text
会使用知识库工具的问答助手
```

注意：

> 不要现在就急着实现复杂 Agent。
> 先把 RAG 检索质量做好，再进入 Agent。

---

## 3. 推荐优化总链路

建议按这个顺序优化：

```text
阶段 1：检索质量评估
阶段 2：chunk 参数调优
阶段 3：RAG prompt 调优
阶段 4：回答质量和 sources 可解释性
阶段 5：异常处理和降级
阶段 6：多文档和元数据管理
阶段 7：多格式文档解析能力
阶段 8：UI 交互页面
阶段 9：简单 Agent 工具调用
阶段 10：测试、文档、演示和项目总结
```

顺序很重要。

不要先做 Agent。

因为 Agent 只是外层调度，底层检索质量不稳定时，Agent 只会把问题包装得更复杂。

---

## 4. 阶段 1：检索质量评估

目标：

```text
先确认 Qdrant 检索出来的 chunks 是否真的相关。
```

当前可用接口：

```text
POST /documents/search
```

要做的事情：

1. 准备 10-20 个测试问题。
2. 每个问题提前标注期望命中的 PDF 页码。
3. 调用 `/documents/search`。
4. 记录 top_k 结果里是否出现正确页码。
5. 计算命中率。

建议建立一个表：

| 问题 | 期望页码 | top_k | 是否命中 | 命中的 chunk_id | 备注 |
|---|---:|---:|---|---:|---|
| GUI Agent 的核心流程是什么？ | 3 | 5 | 是 | 7 | 命中第一页相关描述 |

核心指标：

```text
命中率 = 命中的问题数 / 测试问题总数
```

这一阶段先不要看 LLM 回答。

只看检索。

---

## 5. 阶段 2：chunk 参数调优

目标：

```text
找到更适合当前 PDF 类型的 chunk_size 和 overlap。
```

当前默认参数：

```text
chunk_size = 800
overlap = 100
```

可以测试：

```text
chunk_size = 500, overlap = 80
chunk_size = 800, overlap = 100
chunk_size = 1000, overlap = 150
chunk_size = 1200, overlap = 200
```

观察指标：

| 参数 | 检索命中率 | 噪声情况 | 回答质量 | 备注 |
|---|---:|---|---|---|
| 500 / 80 | 70% | 少 | 信息可能断裂 | chunk 偏小 |
| 800 / 100 | 85% | 中 | 较稳定 | 当前默认 |
| 1200 / 200 | 80% | 多 | 回答偏泛 | chunk 偏大 |

经验判断：

```text
chunk 太小：上下文不完整
chunk 太大：检索粒度太粗
overlap 太小：段落容易断
overlap 太大：重复内容多
```

这一阶段的产出：

```text
确定一组当前项目推荐参数
```

---

## 6. 阶段 3：RAG prompt 调优

目标：

```text
让 DeepSeek 更稳定地只基于 sources 回答。
```

当前 prompt 在：

```text
app/main.py
_build_rag_messages()
```

可以优化的方向：

### 约束模型不编造

prompt 中要明确：

```text
只能根据检索资料回答。
资料不足时，直接说明资料不足。
不要使用资料外知识补全事实。
```

### 要求引用来源

让模型在关键结论后标注：

```text
[Source 1]
[Source 2]
```

这样可以判断回答是否真的来自检索结果。

### 固定输出格式

可以让模型按格式回答：

```text
答案：
...

依据：
- [Source 1] ...
- [Source 3] ...

资料不足之处：
...
```

好处：

```text
更容易调试
更容易给前端展示
更容易做质量评估
```

这一阶段的产出：

```text
一版稳定的 RAG prompt 模板
```

---

## 7. 阶段 4：回答质量和 sources 可解释性

目标：

```text
不仅要回答，还要让用户知道答案来自哪里。
```

当前 `/rag/ask` 已经返回：

```json
{
  "reply": "...",
  "sources": [...],
  "usage": {...}
}
```

后续可以优化：

- sources 已在第 12 步改为返回摘要 preview，不再直接返回完整长文本
- 每个 source 已在第 12 步增加 `source_id`
- 返回 `answer_confidence`
- 返回 `used_sources`
- 对低分 chunk 做过滤
- 在回答里强制引用 source id

可以新增字段：

```json
{
  "reply": "...",
  "used_sources": [1, 3],
  "sources": [
    {
      "source_id": 1,
      "filename": "GUIagent.pdf",
      "page_number": 3,
      "chunk_id": 7,
      "score": 0.82,
      "preview": "..."
    }
  ]
}
```

这一阶段的产出：

```text
回答可追溯，sources 可展示
```

---

## 8. 阶段 5：异常处理和降级

目标：

```text
让系统在失败时仍然给出清晰反馈。
```

当前需要继续补的异常场景：

| 场景 | 当前风险 | 建议处理 |
|---|---|---|
| 没有索引文档 | 用户不知道下一步做什么 | 返回“请先上传并索引 PDF” |
| 检索结果为空 | DeepSeek 没有资料可用 | 不调用 LLM，直接提示资料不足 |
| 检索结果低分 | 可能答非所问 | 增加 score_threshold |
| DeepSeek 超时 | 接口 502 | 返回清晰错误和重试提示 |
| Qdrant collection 维度不匹配 | 换 embedding 模型后失败 | docs 中说明删除或重建 `.qdrant` |
| PDF 是扫描件 | 提取不到文本 | 提示需要 OCR |

可以增加：

```text
score_threshold
min_sources
error_code
debug_info
```

这一阶段的产出：

```text
用户知道为什么失败，以及下一步该做什么
```

---

## 9. 阶段 6：多文档和元数据管理

目标：

```text
从“上传一个 PDF 后问答”，升级为“管理多个文档的知识库”。
```

当前 Qdrant payload 已经有：

```text
filename
page_number
chunk_id
char_count
text
```

第 16 步已经增加：

```text
document_id
collection_name
chunk_size
overlap
embedding_model
```

后续第 17 步继续增加：

```text
content_hash
```

第 16 步已经新增接口：

```text
GET /documents
GET /documents/{document_id}
DELETE /documents/{document_id}
```

后续第 17 步再考虑：

```text
POST /documents/reindex
```

需要注意：

```text
同一个 PDF 重复上传时，应该避免重复索引。
```

可以用：

```text
content_hash = PDF bytes 的 hash
```

判断文档是否已经存在。

这一阶段的产出：

```text
本地知识库有基本文档管理能力
```

---

## 10. 阶段 7-9：进入 Agent 前后的补强阶段

在进入 Agent 之前，还可以先补两个更贴近个人项目展示的能力：

```text
多格式文档解析
UI 交互页面
```

这两个能力不是 Agent 本身，但会明显提升项目完整度。

---

## 10.1 阶段 7：多格式文档解析能力

目标：

```text
从“只能上传 PDF”升级为“可以把多种文件作为知识库内容”。
```

当前只支持：

```text
PDF
```

后续可扩展：

| 类型 | 后缀 | 说明 |
|---|---|---|
| PDF | `.pdf` | 当前已支持基础文本提取，后续补 OCR、表格、图片 |
| Word | `.docx` | 提取段落、标题、表格 |
| Markdown | `.md` | 按标题层级切分，适合技术文档 |
| 纯文本 | `.txt` | 最容易接入 |
| 表格 | `.xlsx`、`.csv` | 转成结构化 chunk 或表格摘要 |

推荐抽象：

```text
DocumentLoader
ParsedDocument
ParsedSection
TextChunk
```

统一流程：

```text
不同文件类型
-> loader 解析
-> ParsedDocument
-> chunk 切分
-> embedding
-> Qdrant
```

先不要一次性支持所有格式。

推荐顺序：

```text
1. Markdown
2. txt
3. docx
4. csv/xlsx
5. PDF OCR
```

这一阶段的产出：

```text
本地知识库不再局限于 PDF
```

---

## 10.2 阶段 8：UI 交互页面

目标：

```text
从“只能在 Swagger Docs 里测试”升级为“有自己的桌面端/网页端交互体验”。
```

当前项目主要靠：

```text
http://127.0.0.1:8000/docs
```

这适合学习接口，但不适合作为最终个人项目展示。

后续可以做一个轻量 Web UI：

```text
上传文件
查看索引状态
输入问题
查看回答
查看 sources
查看检索分数
查看 token usage
```

视觉方向：

```text
现代风
玻璃质感
圆角卡片
桌面端优先
网页端可访问
信息清晰，不做花哨 landing page
```

页面结构建议：

```text
左侧：知识库文件列表
中间：问答对话区
右侧：sources / 检索结果 / 参数面板
顶部：当前 collection、embedding 模型、DeepSeek 模型
底部：输入框、top_k、score_threshold
```

第一版 UI 不需要复杂：

```text
1. 上传 PDF
2. 调用 /documents/index
3. 输入问题
4. 调用 /rag/ask
5. 展示 reply 和 sources
```

这一阶段的产出：

```text
项目从“接口工具”升级成“可交互 RAG 应用”
```

---

## 10.3 阶段 9：简单 RAG Agent 工具调用

目标：

```text
让模型不只是被固定调用，而是能选择是否使用检索工具。
```

先做最小 Agent，不要一开始就做复杂框架。

可以定义两个工具：

```text
search_documents(query, limit)
answer_with_context(question, sources)
```

Agent 流程：

```text
用户问题
-> DeepSeek 判断是否需要查资料
-> 如果需要，调用 search_documents
-> 观察搜索结果
-> 再回答
```

最小工具路由可以先自己写，不依赖 LangChain。

伪流程：

```text
if question looks like document question:
    sources = search_documents(question)
    answer = answer_with_context(question, sources)
else:
    answer = normal_chat(question)
```

后续再升级为更正式的 tool calling。

这一阶段的产出：

```text
一个能选择工具的最小 RAG Agent
```

---

## 11. 阶段 10：测试、文档和演示

目标：

```text
让项目可以被别人看懂、跑通、验证。
```

需要补：

### 接口测试

建议至少测试：

```text
GET /health
POST /documents/extract
POST /documents/chunk
POST /embeddings/text
POST /documents/index
POST /documents/search
POST /rag/ask
```

### RAG 评估文档

新增一份：

```text
docs/summary/09-rag-test-spec.md
docs/summary/10-rag-test-result.md
```

记录：

```text
测试问题
期望页码
top_k
是否命中
回答是否正确
调参前后对比
```

### 项目 README

README 最终要能回答：

```text
这个项目解决什么问题？
技术链路是什么？
怎么启动？
怎么上传 PDF？
怎么提问？
怎么评估效果？
有哪些限制？
下一步计划是什么？
```

### 演示路径

推荐演示顺序：

```text
1. 打开 /docs
2. /documents/index 上传 PDF
3. /documents/search 看检索结果
4. /rag/ask 看 RAG 回答
5. 展示 sources
6. 展示评估表
```

这一阶段的产出：

```text
项目可以作为学习作品展示
```

---

## 12. 推荐后续实现顺序

后续建议按这个顺序做：

```text
1. 固定 RAG 输出格式
2. 准备 10-20 个评估问题
3. 记录 chunk_size / overlap / top_k 调参结果
4. 增加文档列表和删除接口
5. 增加 content_hash，避免重复索引
6. 增加 Markdown / txt 文档解析
7. 增加 docx / csv / xlsx 解析规划或最小实现
8. 增加现代风 UI 交互页面
9. 增加最小 Agent 工具路由
10. 增加测试
11. 持续更新测试规范和测试结果
12. 写项目总结和评估报告
```

从第 13 步开始，执行方式调整为：

```text
先创建 docs/goal/*.md
再写代码
完成后创建 docs/summary/*.md
最后同步 README 和 00 号续接规范
```

当前下一步 goal：

```text
docs/goal/17-document-dedup-content-hash-goal.md
```

---

## 13. 暂时不要做的事情

现阶段先不要急着做：

- 复杂多 Agent 协作
- Graph 工作流
- LangChain 大量封装
- 云端部署
- 复杂权限系统
- 多模态 PDF 解析

UI 可以做，但第一版应该是轻量交互页面，不要先做复杂前端大系统。

这些不是不能做，而是现在做会分散主线。

当前主线应该是：

```text
把 RAG 检索质量和回答质量做扎实。
```

---

## 14. 最终个人项目可以怎么描述

等上述阶段完成后，可以把项目描述成：

> 基于 FastAPI、DeepSeek、fastembed 和 Qdrant 实现的本地 PDF RAG Agent。支持 PDF 上传、文本切分、向量索引、语义检索、基于 sources 的问答生成，并通过检索命中率评估和 chunk 参数调优提升回答质量。

技术点可以写：

- FastAPI 后端接口
- DeepSeek Chat Completions
- fastembed 本地 embedding
- Qdrant 本地向量数据库
- PDF 文本解析
- Word / Markdown / 表格文档解析
- chunk_size / overlap 调参
- top_k 检索评估
- RAG prompt 设计
- sources 可解释性
- 现代风 Web UI
- 最小 Agent 工具调用

---

## 15. 一句话路线

不要从“Agent”开始。

要从：

```text
检索命中率
-> chunk 调参
-> prompt 调优
-> sources 可解释
-> 异常降级
-> 多文档管理
-> 多格式文档解析
-> UI 交互页面
-> 最小 Agent 工具调用
```

一步一步往上做。

这条路更慢一点，但每一步都能解释清楚，也更适合真正学习 AI Agent 的工程链路。

