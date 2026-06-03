# 第 3 步学习笔记：PDF 解析与文件上传接口

这一步的目标是：

> 上传一个 PDF 文件，让后端提取文本，并返回页数、字符数、文本预览。

当前新增接口：

```text
POST /documents/extract
```

它不会调用 DeepSeek，也不会做 RAG。

它只解决 RAG 的第一个前置问题：

```text
PDF 里到底能不能提取出文本？
```

---

## 1. 为什么下一步是 PDF 解析

RAG 的完整链路大概是：

```text
PDF 文件
-> 提取文本
-> 文档切分 chunk
-> embedding 向量化
-> 存入 Qdrant
-> 用户提问时检索相关 chunk
-> 把 chunk + 问题发给 LLM
-> 返回答案
```

现在我们只做第二步：

```text
PDF 文件 -> 提取文本
```

如果这一步做不稳，后面的向量化、检索、回答都会被脏数据拖垮。

---

## 2. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|
| PDF 解析函数 | [`app/pdf_extractor.py`](../../app/pdf_extractor.py) |
| 文件上传接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/documents/extract")` |
| PDF 解析依赖 | [`requirements.txt`](../../requirements.txt) 里的 `pdfplumber` |
| 文件上传依赖 | [`requirements.txt`](../../requirements.txt) 里的 `python-multipart` |

新增接口：

```python
@app.post("/documents/extract", response_model=PdfExtractResponse)
async def extract_document(file: UploadFile = File(...)) -> PdfExtractResponse:
    ...
```

这行代码表示：

```text
定义一个 POST /documents/extract 接口
它接收一个上传文件 file
返回 PdfExtractResponse 结构
```

---

## 3. PDF 为什么不是普通文本文件

你不能把 PDF 简单理解成 `.txt`。

PDF 更像是：

```text
一份页面排版文件
```

它里面可能包含：

- 文字
- 图片
- 表格
- 坐标信息
- 字体信息
- 扫描图片
- 多栏排版

所以 PDF 解析不是简单地“读取文件内容”。

常见 PDF 类型：

| 类型 | 能否直接提取文字 | 说明 |
|---|---|---|
| 文本型 PDF | 通常可以 | PDF 里本来就有文字层 |
| 扫描型 PDF | 通常不可以 | PDF 里只有图片，需要 OCR |
| 表格/复杂排版 PDF | 可以但可能混乱 | 文字顺序可能和视觉顺序不一致 |

当前阶段只处理文本型 PDF。

扫描型 PDF 先识别出来，不做 OCR。

---

## 4. `pdfplumber` 是什么

`pdfplumber` 是一个 Python PDF 解析库，常用于：

- 提取文字
- 提取表格
- 处理复杂排版
- 按页读取 PDF

当前代码里核心逻辑是：

```python
with pdfplumber.open(BytesIO(content)) as pdf:
    for index, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
```

含义：

```text
打开 PDF 字节内容
-> 遍历每一页
-> 对每一页调用 extract_text()
-> 拿到这一页的文字
```

---

## 5. 什么是文件上传接口

普通 `/chat` 接口传的是 JSON：

```json
{
  "message": "你好"
}
```

但 PDF 是文件，不能直接当普通 JSON 传。

文件上传通常使用：

```text
multipart/form-data
```

你现在可以先这样理解：

```text
JSON 请求：适合传小段结构化文本
文件上传：适合传 PDF、图片、音频这类文件
```

FastAPI 里接收上传文件用：

```python
file: UploadFile = File(...)
```

| 概念 | 含义 |
|---|---|
| `UploadFile` | FastAPI 表示上传文件的对象 |
| `File(...)` | 告诉 FastAPI 这个参数来自文件上传 |
| `await file.read()` | 读取上传文件的字节内容 |

---

## 6. 为什么需要 `python-multipart`

FastAPI 自己负责定义接口，但解析文件上传的 `multipart/form-data` 需要额外依赖：

```text
python-multipart
```

所以 `requirements.txt` 里新增了：

```text
python-multipart>=0.0.20,<0.1
```

没有这个库，启动或调用文件上传接口时会报错。

---

## 7. 当前接口返回什么

调用：

```text
POST /documents/extract
```

返回结构：

```json
{
  "filename": "example.pdf",
  "page_count": 10,
  "char_count": 5234,
  "preview": "整份 PDF 的前 500 个字符...",
  "scanned_like": false,
  "pages": [
    {
      "page_number": 1,
      "char_count": 800,
      "preview": "第 1 页前 500 个字符..."
    }
  ]
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `filename` | 上传的文件名 |
| `page_count` | PDF 页数 |
| `char_count` | 提取出的总字符数 |
| `preview` | 整份文档的文本预览 |
| `scanned_like` | 是否像扫描件，`true` 表示没有提取到文字 |
| `pages` | 每一页的提取结果 |

---

## 8. 为什么要限制文件大小

当前接口限制 PDF 最大 10 MB：

```python
max_size = 10 * 1024 * 1024
```

原因：

- 防止用户上传超大文件拖垮服务
- 防止一次读取太多内容占用内存
- 初学阶段先控制变量

后面真正做生产系统时，会考虑：

- 流式读取
- 后台任务
- 对象存储
- 异步解析
- 队列处理

但现在不用展开。

---

## 9. 为什么要判断 `.pdf` 后缀

当前代码只允许文件名以 `.pdf` 结尾：

```python
if not filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Only PDF files are supported")
```

这是一层基础校验。

它不能 100% 保证文件一定是真 PDF，但能先挡掉明显错误：

- `.txt`
- `.docx`
- `.png`
- 空文件名

后面可以再加更严格的 MIME 类型和文件头校验。

---

## 10. 如何在 `/docs` 页面测试

打开：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /documents/extract
```

操作步骤：

1. 点 `Try it out`
2. 在 `file` 那里选择一个 PDF
3. 点 `Execute`
4. 查看返回结果

如果 `char_count > 0`，说明提取到了文字。

如果 `scanned_like = true`，说明这个 PDF 可能是扫描件，当前阶段暂时不处理。

---

## 11. 如何用 PowerShell 测试

示例：

```powershell
$pdf = "D:\ll-work\ai-play\dive-into-llms\documents\chapter1\dive-into-llm.pdf"

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/documents/extract" `
  -Method Post `
  -Form @{ file = Get-Item $pdf }
```

如果你的 PowerShell 版本不支持 `-Form`，就先用 `/docs` 页面测试。

---

## 12. 当前验证结果

已经用仓库里的样本 PDF 测过：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

接口返回：

```text
POST /documents/extract -> 200 OK
```

提取摘要：

```json
{
  "filename": "GUIagent.pdf",
  "page_count": 43,
  "char_count": 9511,
  "scanned_like": false
}
```

说明：

```text
这个 PDF 是文本型 PDF，能正常提取文字。
```

也测试了超过 10 MB 的 PDF：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter1\dive-into-llm.pdf
```

接口返回：

```text
POST /documents/extract -> 413
```

返回内容：

```json
{
  "detail": "PDF file is too large; max size is 10 MB"
}
```

说明：

```text
文件大小限制生效了。
```

也确认了 `/docs` 页面已经注册新接口：

```text
/documents/extract
```

---

## 13. 这一阶段你要掌握什么

现在你要能说清楚：

1. PDF 不是普通文本文件，而是页面排版文件。
2. 文本型 PDF 可以直接提取文字，扫描型 PDF 需要 OCR。
3. `pdfplumber` 可以按页提取 PDF 文本。
4. FastAPI 用 `UploadFile = File(...)` 接收上传文件。
5. 文件上传请求通常是 `multipart/form-data`。
6. `python-multipart` 是 FastAPI 解析文件上传需要的依赖。
7. 解析结果里要看 `page_count`、`char_count`、`preview`。
8. `scanned_like=true` 表示当前没有提取到文字，不代表 PDF 文件不存在。

---

## 14. 当前不要学什么

现在不要展开，不代表以后不学。

这些内容后续会分成两类：**RAG 主线必须做** 和 **后续增强再做**。

| 内容 | 后续是否加入 | 优先级 | 说明 |
|---|---|---|---|
| 文档 chunk 切分 | 会 | 主线必做 | 已进入第 4 步，用于把长文本切成可检索的小块 |
| embedding | 会 | 主线必做 | 下一阶段会做，把 chunk 转成向量 |
| Qdrant | 会 | 主线必做 | embedding 后接入，用来存储和检索向量 |
| RAG Prompt | 会 | 主线必做 | 检索到相关 chunk 后，再组织 prompt 给大模型回答 |
| OCR | 视情况加入 | 后续增强 | 用来处理扫描型 PDF，当前先识别 `scanned_like=true` |
| 表格抽取 | 视情况加入 | 后续增强 | 如果目标文档里表格很多，再专门处理 |
| PDF 图片抽取 | 视情况加入 | 后续增强 | 如果需要理解图片/图表，再接入多模态或图片处理 |

在第 3 步刚完成 PDF 解析时，先不要展开：

- OCR
- 表格抽取
- PDF 图片抽取
- 文档 chunk 切分
- embedding
- Qdrant
- RAG Prompt

下一步才是：

```text
把提取出来的文本切成 chunk
```

也就是文档切分。

---

## 15. 一句话总结

这一步完成的是：

```text
PDF 上传
-> pdfplumber 按页提取文字
-> 返回页数、字符数、预览
```

这是 RAG 项目的文档入口。只有先把 PDF 文本提取出来，后面才谈得上切分、检索和问答。

---

## 16. 后续文档解析能力扩展

当前第 3 步只实现了最小 PDF 文本提取：

```text
上传 PDF
-> pdfplumber 按页提取文本
-> 返回 page_count、char_count、preview、scanned_like
```

但真实知识库不会只有一种 PDF。

后续可以把“文档解析”升级成一个独立能力：

```text
不同文件类型
-> 统一解析成 Document
-> 统一切分 chunk
-> 统一写入 Qdrant
```

### PDF 后续增强方向

| 能力 | 说明 | 优先级 |
|---|---|---|
| OCR | 处理扫描型 PDF，解决 `scanned_like=true` 但没有文本的问题 | 中 |
| 表格抽取 | 处理 PDF 中的表格信息，避免表格内容被普通文本抽乱 | 中 |
| 图片抽取 | 处理图表、截图、流程图等视觉内容 | 低 |
| 页码和章节识别 | 让 sources 不只显示 page_number，还能显示章节标题 | 中 |
| PDF 大文件处理 | 当前限制 10 MB，后续可以做异步解析或后台任务 | 中 |
| PDF 去噪 | 清理页眉、页脚、页码、重复标题 | 中 |

### 非 PDF 文档扩展方向

后续知识库可以考虑支持：

| 文件类型 | 示例后缀 | 解析思路 |
|---|---|---|
| Word 文档 | `.docx` | 提取段落、标题、表格，保留结构 |
| Markdown 文档 | `.md` | 按标题层级切分，保留 heading path |
| 纯文本 | `.txt` | 直接读取文本并切分 |
| 表格文件 | `.xlsx`、`.csv` | 转成行记录、表格摘要或结构化 chunk |
| 网页文本 | `.html` 或 URL | 提取正文，清理导航和脚本 |

后续可以新增统一入口：

```text
POST /knowledge/index
```

或者按类型拆分：

```text
POST /documents/index/pdf
POST /documents/index/docx
POST /documents/index/markdown
POST /documents/index/table
```

更推荐先做统一抽象：

```text
DocumentLoader
ParsedDocument
ParsedSection
TextChunk
```

这样后续无论输入 PDF、Word、Markdown 还是表格，都能进入同一条 RAG 链路。

### 当前不要立刻实现

这些能力先纳入后续规划，不要在第 3 步直接展开。

当前主线仍然是：

```text
先把 PDF RAG 检索质量做好
再扩展多格式文档解析
最后再做 Agent 和 UI
```

