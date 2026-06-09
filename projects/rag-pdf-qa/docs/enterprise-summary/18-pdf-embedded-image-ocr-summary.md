# 企业级第 18 步完成总结：PDF 内嵌图片 OCR 治理

## 完成内容

本步骤把文本型 PDF 页面里的内嵌图片 OCR 接入现有 RAG 链路：

- PDF 提取链路复用 `enable_image_ocr` 参数。
- 使用 PyMuPDF 枚举 PDF 页面内嵌图片。
- 对图片字节调用现有 `extract_ocr_text_from_image_bytes`。
- OCR 结果进入 `ExtractedPage.images`。
- `split_pdf_text` 会把图片 OCR 文本切成独立 chunk。
- 图片 OCR chunk 标记为 `extraction_method=pdf_image_ocr`。
- `/documents/extract` 返回 `image_ocr_count` 和每页图片 OCR 预览。
- `/documents/chunk` 返回 `pdf_image_ocr` chunk。
- `/documents/index`、`/documents/index-jobs` 和 reindex 继续复用 `enable_image_ocr`，PDF 和 docx 都可使用。

## 涉及文件

```text
app/pdf_extractor.py
app/text_splitter.py
app/main.py
tests/test_pdf_extractor.py
tests/test_text_splitter.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-goal/18-pdf-embedded-image-ocr-goal.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_pdf_extractor.py tests\test_text_splitter.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤做的是 OCR，不是完整多模态理解。

它可以处理 PDF 图片中的文字，但暂时不理解图表趋势、坐标轴数据点、流程图拓扑关系或图片语义 caption。这些仍属于后续多模态增强方向。
