# 企业级第 17 步执行目标：PDF 表格抽取治理

## 1. 背景

当前项目已经支持 PDF 文本、扫描型 PDF OCR、Markdown、txt、docx、docx 图片 OCR、csv 和 xlsx 入库。

但很多企业知识库 PDF 会包含价格表、配置表、指标表、验收表和项目排期表。普通 `extract_text()` 往往会把表格内容抽成顺序混乱的文本，导致检索命中后回答缺少行列关系。

第 17 步的目标是把 PDF 表格作为一种可治理的来源类型纳入 RAG 链路。

## 2. 本次目标

```text
1. 为 PDF 提取链路新增可选 extract_tables 参数
2. 使用 pdfplumber 抽取 PDF 页面表格
3. 将表格行转换成适合 embedding 和检索的稳定文本
4. PDF 表格内容进入 chunk，并标记 extraction_method=pdf_table
5. /documents/extract、/documents/chunk、/documents/index、/documents/index-jobs 和 reindex 保持参数一致
6. 异步索引任务持久化 extract_tables，失败重试时保留该选项
7. OpenAPI、单元测试和文档更新
```

## 3. 不做什么

本步骤不做：

```text
复杂跨页表格合并
表格坐标和单元格 bbox 返回
扫描型 PDF 表格结构 OCR
图表语义理解
多模态图片 caption
PDF 去页眉页脚和版面重排
Web UI 表格预览面板
```

## 4. 预期行为

当用户上传 PDF 并传入：

```text
extract_tables=true
```

系统应当：

```text
PDF 页面正文 -> extraction_method=text 或 pdf_ocr
PDF 页面表格 -> extraction_method=pdf_table
```

表格行会被转换为类似：

```text
pdf table 1 page 2 row 3: 项目=企业版; 价格=999; 负责人=Alice
```

这样后续检索、RAG sources、Agent sources 和评估结果都能看出内容来自 PDF 表格。

## 5. 预期修改文件

```text
app/pdf_extractor.py
app/text_splitter.py
app/main.py
app/index_jobs.py
app/models.py
app/db.py
migrations/versions/009_index_job_extract_tables.py
tests/test_pdf_extractor.py
tests/test_text_splitter.py
tests/test_main_api.py
tests/test_index_jobs.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/17-pdf-table-extraction-governance-summary.md
```

## 6. 验收标准

```text
1. extract_tables=false 时，原有 PDF 文本解析行为不变
2. extract_tables=true 时，PDF 表格会生成 pdf_table chunk
3. /documents/extract 返回 table_count 和页面 table_count
4. /documents/chunk 返回 extraction_method=pdf_table 的 chunk
5. /documents/index 响应 extraction_methods 包含 pdf_table
6. /documents/index-jobs 能保存 extract_tables 并在后台任务中传递
7. 已有 OCR、docx image OCR、多格式入库不回退
8. pytest tests/test_pdf_extractor.py tests/test_text_splitter.py tests/test_main_api.py tests/test_index_jobs.py 通过
9. pytest 全量通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_pdf_extractor.py tests\test_text_splitter.py tests\test_main_api.py tests\test_index_jobs.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
