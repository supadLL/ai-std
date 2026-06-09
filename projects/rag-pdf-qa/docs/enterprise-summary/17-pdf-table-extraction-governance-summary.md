# 企业级第 17 步完成总结：PDF 表格抽取治理

## 完成内容

本步骤把 PDF 表格作为独立来源类型接入现有 RAG 链路：

- `extract_text_from_pdf_bytes` 新增 `extract_tables` 可选参数。
- 使用 `pdfplumber.extract_tables()` 抽取页面表格。
- 将表格行转换为稳定文本，例如 `pdf table 1 page 2 row 3: 项目=企业版; 价格=999`。
- PDF 页面正文继续保留 `text` / `pdf_ocr` 来源。
- PDF 表格内容会生成独立 chunk，并标记 `extraction_method=pdf_table`。
- `/documents/extract` 返回整份 PDF 和每页的 `table_count`，并返回表格预览。
- `/documents/chunk` 返回 `pdf_table` chunk。
- `/documents/index`、`/documents/index-jobs` 和 `/documents/{document_id}/reindex` 支持 `extract_tables`。
- 异步任务 `index_jobs` 持久化 `extract_tables`，后台执行和失败重试时保留该选项。
- 新增迁移 `009_index_job_extract_tables.py`，并补了 SQLite 本地兼容升级逻辑。

## 涉及文件

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
docs/enterprise-goal/17-pdf-table-extraction-governance-goal.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_pdf_extractor.py tests\test_text_splitter.py tests\test_main_api.py tests\test_index_jobs.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤只处理文本型 PDF 中能被 `pdfplumber` 识别出的表格。

暂时不做跨页表格合并、单元格坐标返回、扫描型表格结构 OCR、图片/图表理解或 Web UI 表格预览。
