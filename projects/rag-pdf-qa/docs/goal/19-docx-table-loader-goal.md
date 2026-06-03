# 第 19 步执行目标：支持 docx 与表格类文档的最小解析

这一步的目标是：

> 在 Markdown/txt 之后，继续扩展 Word 和表格文件的知识库输入能力。

---

## 1. 背景

真实个人知识库常见文件还包括：

```text
Word 文档
csv 表格
xlsx 表格
```

它们和普通文本不同：

```text
docx 有标题、段落、表格
表格文件有行列结构
```

所以需要在不破坏已有 RAG 链路的前提下，加入最小解析策略。

---

## 2. 本次目标

支持最小版本：

```text
.docx：提取段落和表格文本
.csv：按行或分组转成文本 chunk
.xlsx：至少读取第一个工作表或所有工作表文本
```

建议每个 chunk 保留：

```text
filename
file_type
section_title
sheet_name
row_range
chunk_id
```

---

## 3. 不做什么

本次不做：

- Word 样式完整还原
- 复杂表格问答引擎
- SQL 化表格查询
- 图片 OCR
- 多工作簿复杂关系解析
- 前端 UI
- Agent 工具查询表格

---

## 4. 预计修改文件

可能新增：

```text
app/loaders/docx_loader.py
app/loaders/csv_loader.py
app/loaders/xlsx_loader.py
```

可能修改：

```text
requirements.txt
app/document_loaders.py
app/main.py
app/document_store.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/19-docx-table-loader-step.md
docs/summary/19-docx-table-loader-summary.md
```

---

## 5. 接口变化

继续复用：

```text
POST /documents/index
```

需要支持上传：

```text
.docx
.csv
.xlsx
```

响应中应能看到：

```text
file_type
chunk_count
document_id
```

---

## 6. 验收标准

完成后应满足：

```text
1. docx 段落能被索引和检索
2. docx 表格内容能被索引和检索
3. csv 内容能被索引和检索
4. xlsx 内容能被索引和检索
5. sources 能体现文件类型和必要元数据
6. PDF、md、txt 原有流程不被破坏
```

---

## 7. 测试方式

建议准备：

```text
一个 docx 测试文件，包含段落和表格
一个 csv 测试文件
一个 xlsx 测试文件
```

测试顺序：

```text
1. 分别上传并索引 docx/csv/xlsx
2. 用 /documents/search 查找文件中的明确内容
3. 用 /rag/ask 提问需要表格内容回答的问题
4. 检查 sources 的 filename、file_type、sheet_name 或 row_range
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/19-docx-table-loader-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
```

