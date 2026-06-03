# 第 18 步完成总结：Markdown 和 txt 文档入库

本 summary 记录第 18 步实际完成内容。

对应 goal：

```text
docs/goal/18-markdown-txt-loader-goal.md
```

---

## 1. 本次完成了什么

完成内容：

```text
1. 新增轻量 DocumentLoader 抽象
2. 新增 ParsedDocument / ParsedSection
3. 支持 .md / .markdown 文件解析
4. 支持 .txt 文件解析
5. /documents/index 支持 PDF、Markdown、txt 共用索引链路
6. Qdrant payload 增加 file_type
7. /documents/search 和 /rag/ask sources 返回 file_type
8. 保持 PDF 原有流程不破坏
```

---

## 2. 改动文件

代码：

```text
app/document_loaders.py
app/text_splitter.py
app/main.py
app/vector_store.py
```

测试：

```text
tests/test_document_loaders.py
tests/test_main_api.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/18-markdown-txt-loader-goal.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

---

## 3. 接口变化

复用原接口：

```text
POST /documents/index
```

现在支持：

```text
.pdf
.md
.markdown
.txt
```

响应中包含：

```text
file_type
document_id
chunk_count
content_hash
```

`POST /documents/search` 和 `POST /rag/ask` 的 source/result 中新增或保留：

```text
file_type
```

用于区分来源：

```text
pdf
markdown
text
```

---

## 4. Markdown 解析策略

当前是最小解析：

```text
按 Markdown 标题行拆分 section
标题行以 # 开头
不做 Markdown AST 深度解析
```

如果 Markdown 没有标题，则作为一个 section。

---

## 5. txt 解析策略

txt 文件当前作为一个 section。

要求：

```text
UTF-8 / UTF-8 BOM
```

暂不支持其他编码自动探测。

---

## 6. 验证结果

已运行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
compileall 通过
pytest 14 passed
```

新增测试覆盖：

```text
Markdown 按标题拆分 section
txt 作为单 section
非 UTF-8 文本报错
/documents/index 可以上传 txt
PDF 原有测试仍通过
```

真实接口链路也已验证：

```text
使用临时 Qdrant 和临时 metadata 启动隔离服务
上传 Markdown：file_type = markdown, indexed_count = 2
上传 txt：file_type = text, indexed_count = 1
/documents/search 可以检索到 Markdown 中的 RedRiver
/documents/search 可以检索到 txt 中的 BlueWhale-42
```

本次没有自动调用真实 DeepSeek API。

原因：

```text
/rag/ask 会消耗真实 API token
该接口已经复用同一套 search 结果和 sources 结构
本次主要验证 md/txt 能进入检索链路
```

---

## 7. 当前限制

本次没有做：

```text
Markdown AST 深度解析
代码块特殊处理
表格结构化解析
docx / xlsx / csv
扫描 PDF OCR
```

---

## 8. 下一步建议

进入第 19 步：

```text
支持 docx 与表格类文档的最小解析
```

对应 goal：

```text
docs/goal/19-docx-table-loader-goal.md
```
