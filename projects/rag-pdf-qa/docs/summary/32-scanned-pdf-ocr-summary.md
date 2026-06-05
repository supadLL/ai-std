# 第 32 步完成总结：扫描型 PDF OCR 支持

本 summary 记录第 32 步实际完成内容。

对应 goal：

```text
docs/goal/32-scanned-pdf-ocr-goal.md
```

---

## 1. 本次完成了什么

本次为 PDF 入库链路新增了可选 OCR 能力：

```text
1. 文本型 PDF 继续使用原来的 pdfplumber 文本提取
2. enable_ocr=true 时，对无文本页面执行 OCR
3. OCR 文本进入原有 chunk / embedding / Qdrant 链路
4. chunk 和 sources 增加 extraction_method
5. /documents/extract、/documents/chunk、/documents/index 支持 enable_ocr 和 ocr_language
6. 返回 extraction_mode 和 ocr_page_count
7. 未安装 OCR 依赖或 Tesseract 时返回清晰错误
```

---

## 2. 改动文件

新增：

```text
app/ocr_extractor.py
tests/test_ocr_extractor.py
```

修改：

```text
app/pdf_extractor.py
app/text_splitter.py
app/vector_store.py
app/main.py
requirements.txt
.env.example
tests/test_main_api.py
tests/test_text_splitter.py
tests/test_vector_store.py
README.md
docs/00-project-continuation-guide.md
docs/summary/README.md
```

---

## 3. 接口变化

以下接口新增可选表单参数：

```text
POST /documents/extract
POST /documents/chunk
POST /documents/index
```

新增参数：

```text
enable_ocr: bool = false
ocr_language: str = "chi_sim+eng"
```

PDF 相关响应新增：

```text
extraction_mode: "text" | "ocr" | "mixed"
ocr_page_count: number
extraction_method: "text" | "pdf_ocr"
```

`/documents/search` 和 `/rag/ask` 的 sources 也会返回：

```text
extraction_method
```

---

## 4. 关键实现

OCR 只作为可选路径启用：

```text
enable_ocr=false
-> 保持原来的文本 PDF 解析

enable_ocr=true
-> 找出无文本页面
-> 使用 PyMuPDF 渲染页面图片
-> 使用 pytesseract 调用 Tesseract OCR
-> 把 OCR 文本写回 ExtractedPage
-> 继续走 split_pdf_text
```

这样不会影响普通文本型 PDF 的速度和稳定性。

---

## 5. OCR 依赖

Python 依赖：

```text
PyMuPDF
pytesseract
Pillow
```

系统依赖：

```text
Tesseract OCR
```

Windows 如果 `tesseract.exe` 不在 PATH，可以在 `.env` 里配置：

```text
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## 6. 验证结果

代码检查：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
```

结果：

```text
通过
```

自动化测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
33 passed
```

依赖安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

结果：

```text
PyMuPDF 和 pytesseract 已安装到当前 .venv。
```

系统 OCR 程序检查：

```powershell
tesseract --version
```

结果：

```text
当前机器 PATH 中没有 tesseract 命令。
真实扫描 PDF OCR 需要先安装 Tesseract，或在 .env 中配置 TESSERACT_CMD。
```

OpenAPI 验证：

```text
/documents/index requestBody 包含：
file, chunk_size, overlap, reindex, enable_ocr, ocr_language

/documents/index response schema 包含：
extraction_mode, ocr_page_count
```

本次测试没有强制真实执行 Tesseract OCR，原因是：

```text
OCR 系统依赖和语言包依赖本地机器安装状态。
自动化测试重点验证 OCR 选项传递、chunk 来源标记、payload 保存和接口结构。
```

---

## 7. 后续影响

第 32 步之后，项目可以开始支持扫描型 PDF 的最小入库。

当前还没有做：

```text
PDF 表格结构 OCR
图片/图表语义理解
高精度版面还原
OCR 质量评分
```

这些可以继续放到后续 PDF 增强阶段。
