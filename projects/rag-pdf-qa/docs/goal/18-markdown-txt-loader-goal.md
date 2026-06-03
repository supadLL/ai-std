# 第 18 步执行目标：支持 Markdown 和 txt 文档入库

这一步的目标是：

> 从只支持 PDF，扩展到支持 Markdown 和纯文本文件作为知识库内容。

---

## 1. 背景

很多个人知识库内容并不是 PDF，而是：

```text
Markdown 笔记
项目说明文档
纯文本资料
```

Markdown 和 txt 是最适合先接入的非 PDF 格式：

```text
解析难度低
不需要 OCR
适合学习 DocumentLoader 抽象
```

---

## 2. 本次目标

新增最小 loader 抽象：

```text
DocumentLoader
ParsedDocument
ParsedSection
```

支持：

```text
.md
.txt
```

让这些文件进入同一条链路：

```text
文件上传 -> loader 解析 -> chunk -> embedding -> Qdrant -> RAG
```

---

## 3. 不做什么

本次不做：

- docx
- xlsx/csv
- PDF OCR
- 图片理解
- Markdown AST 深度解析
- 多模态能力
- UI

---

## 4. 预计修改文件

可能新增：

```text
app/document_loaders.py
app/loaders/markdown_loader.py
app/loaders/text_loader.py
```

可能修改：

```text
app/main.py
app/text_splitter.py
app/document_store.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/18-markdown-txt-loader-step.md
docs/summary/18-markdown-txt-loader-summary.md
```

---

## 5. 接口变化

可以复用：

```text
POST /documents/index
```

但需要支持上传：

```text
.pdf
.md
.txt
```

响应中应包含：

```text
file_type
document_id
chunk_count
```

---

## 6. 验收标准

完成后应满足：

```text
1. .md 文件可以索引
2. .txt 文件可以索引
3. /documents/search 可以检索 md/txt 内容
4. /rag/ask 可以基于 md/txt 内容回答
5. sources 中 file_type 或 filename 能区分来源
6. PDF 原有流程不被破坏
7. Swagger Docs 页面仍可测试
```

---

## 7. 测试方式

建议准备：

```text
一个小型 Markdown 测试文件
一个小型 txt 测试文件
```

测试顺序：

```text
1. POST /documents/index 上传 .md
2. POST /documents/search 提问 md 中的内容
3. POST /rag/ask 提问 md 中的内容
4. POST /documents/index 上传 .txt
5. 重复 search 和 rag 测试
6. 再上传 PDF，确认原流程正常
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/18-markdown-txt-loader-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

