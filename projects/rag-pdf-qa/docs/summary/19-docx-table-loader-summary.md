# 第 19 步完成总结：docx 与表格类文档解析

本 summary 记录第 19 步实际完成内容。

对应 goal：

```text
docs/goal/19-docx-table-loader-goal.md
```

---

## 1. 本次完成了什么

完成内容：

```text
1. 支持 .docx 文档入库
2. 支持 .csv 表格入库
3. 支持 .xlsx 表格入库
4. docx 提取段落和表格文本
5. csv/xlsx 将行列内容转成可检索文本
6. 复用 /documents/index、content_hash、reindex 和 Qdrant 链路
7. search / rag sources 继续通过 file_type 区分来源
```

---

## 2. 改动文件

代码：

```text
app/document_loaders.py
app/main.py
requirements.txt
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
docs/goal/19-docx-table-loader-goal.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

---

## 3. 新增依赖

```text
python-docx
openpyxl
```

用途：

```text
python-docx：读取 docx 段落和表格
openpyxl：读取 xlsx 工作表内容
```

csv 使用 Python 标准库。

---

## 4. 接口变化

继续复用：

```text
POST /documents/index
```

现在支持：

```text
.pdf
.md
.markdown
.txt
.docx
.csv
.xlsx
```

响应中的 `file_type` 可能为：

```text
pdf
markdown
text
docx
csv
xlsx
```

---

## 5. 解析策略

docx：

```text
提取段落文本
提取表格每一行
合并为一个 ParsedDocument section
```

csv：

```text
读取 UTF-8 文本
首行作为表头
每一行转成 key=value 文本
```

xlsx：

```text
读取工作簿
每个 sheet 转成一个 section
首行作为表头
每一行转成 key=value 文本
```

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
pytest 18 passed
```

真实接口链路也已验证：

```text
使用临时 Qdrant 和临时 metadata 启动隔离服务
上传 docx：file_type = docx, indexed_count = 1
上传 csv：file_type = csv, indexed_count = 1
上传 xlsx：file_type = xlsx, indexed_count = 1
/documents/search 可以检索到 DocxFalcon
/documents/search 可以检索到 CsvRocket
/documents/search 可以检索到 XlsxComet
```

本次没有自动调用真实 DeepSeek API，避免消耗 token。

---

## 7. 当前限制

本次没有做：

```text
Word 样式完整还原
复杂表格问答引擎
SQL 化表格查询
多 sheet 关系理解
图片 OCR
```

---

## 8. 下一步建议

进入第 20 步：

```text
实现现代风 RAG Web UI
```

对应 goal：

```text
docs/goal/20-modern-web-ui-goal.md
```

