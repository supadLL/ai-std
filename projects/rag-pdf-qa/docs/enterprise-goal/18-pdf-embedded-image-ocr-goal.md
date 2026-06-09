# 企业级第 18 步执行目标：PDF 内嵌图片 OCR 治理

## 1. 背景

第 17 步已经把文本型 PDF 的表格抽取为 `pdf_table` chunk。

企业知识库里的 PDF 还经常包含截图、流程图、架构图、扫描签章、图表标题和图片中的关键说明。当前系统已经支持扫描型 PDF 页面 OCR 和 docx 内嵌图片 OCR，但文本型 PDF 页面里的内嵌图片还不会作为独立来源入库。

第 18 步目标是先把 PDF 内嵌图片中的文字纳入 RAG 链路，形成可配置、可审计、可回归测试的最小能力。

## 2. 本次目标

```text
1. PDF 提取链路复用 enable_image_ocr 参数
2. 使用 PyMuPDF 枚举 PDF 页面内嵌图片
3. 对图片字节调用现有 OCR 工具
4. OCR 文本进入 PDF 页面 images 列表
5. split_pdf_text 生成 extraction_method=pdf_image_ocr 的 chunk
6. /documents/extract 和 /documents/chunk 返回 image_ocr_count 与图片 OCR 预览
7. /documents/index、/documents/index-jobs 和 reindex 保持现有 enable_image_ocr 参数语义，PDF 和 docx 都可使用
8. OpenAPI、单元测试和文档更新
```

## 3. 不做什么

本步骤不做：

```text
多模态图片语义 caption
图表数据点识别
流程图结构化解析
PDF 图片裁剪坐标和 bbox 返回
图片去重
图片单独对象存储
Web UI 图片预览面板
```

## 4. 预期行为

当用户上传 PDF 并传入：

```text
enable_image_ocr=true
```

系统应当：

```text
PDF 页面正文 -> extraction_method=text 或 pdf_ocr
PDF 页面表格 -> extraction_method=pdf_table
PDF 内嵌图片 OCR -> extraction_method=pdf_image_ocr
```

这样 RAG sources 可以清楚区分答案来自正文、表格、扫描页 OCR 还是页面内嵌图片 OCR。

## 5. 预期修改文件

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
docs/enterprise-summary/18-pdf-embedded-image-ocr-summary.md
```

## 6. 验收标准

```text
1. enable_image_ocr=false 时，原有 PDF 解析行为不变
2. enable_image_ocr=true 时，PDF 内嵌图片 OCR 文本会生成 pdf_image_ocr chunk
3. /documents/extract 返回 image_ocr_count 和页面 image_ocr_count
4. /documents/chunk 返回 extraction_method=pdf_image_ocr 的 chunk
5. /documents/index 响应 image_ocr_count 统计 PDF 图片 OCR chunk
6. 已有扫描 PDF OCR、PDF 表格、docx 图片 OCR 不回退
7. pytest tests/test_pdf_extractor.py tests/test_text_splitter.py tests/test_main_api.py 通过
8. pytest 全量通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_pdf_extractor.py tests\test_text_splitter.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
