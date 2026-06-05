# 第 32 步执行目标：扫描型 PDF OCR 支持

这一步的目标是：

> 让当前只适合文本型 PDF 的 RAG 入库能力，扩展到扫描型 PDF 和图片型页面。

---

## 1. 背景

当前 PDF 解析主要依赖文本提取。

如果用户上传的是扫描件、截图型 PDF、图片型页面，可能出现：

```text
提取文本为空
chunk 数量为 0
无法写入知识库
RAG 检索不到内容
```

这会限制项目作为“本地知识库工具”的实际使用范围。

---

## 2. 本次目标

本次完成：

```text
1. 检测 PDF 页面是否缺少可提取文本
2. 为扫描型页面提供 OCR 解析路径
3. OCR 结果进入当前统一 chunk / embedding / Qdrant 链路
4. metadata 标记解析来源，例如 text / ocr
5. Web UI 和 /docs 能看到 OCR 相关结果
6. README 说明 OCR 依赖和限制
```

---

## 3. 不做什么

本次不做：

- 高精度版面还原
- 图片内容理解
- 图表语义理解
- 表格结构 OCR
- 云端 OCR 服务接入
- 对所有文件类型做 OCR

---

## 4. 需要修改的文件

预计修改：

```text
app/pdf_extractor.py
app/main.py
app/document_loaders.py
requirements.txt
README.md
docs/00-project-continuation-guide.md
```

可能新增：

```text
app/ocr_extractor.py
tests/test_ocr_extractor.py
```

完成后新增：

```text
docs/summary/32-scanned-pdf-ocr-summary.md
```

---

## 5. 接口变化

可能扩展：

```text
POST /documents/index
```

可选参数：

```text
enable_ocr: bool = false
ocr_language: str = "chi_sim+eng"
```

响应中可增加：

```text
extraction_mode: "text" | "ocr" | "mixed"
ocr_page_count: number
```

---

## 6. 验收标准

完成后应满足：

```text
1. 文本型 PDF 仍然保持原有解析路径
2. 扫描型 PDF 在 enable_ocr=true 时可以提取文本
3. OCR 文本可以正常 chunk、embedding、入库
4. sources 中可以看到 OCR 来源标记
5. 未安装 OCR 依赖时错误提示清晰
6. pytest 通过
```

---

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

接口测试：

```text
POST /documents/index
上传扫描型 PDF
enable_ocr = true
```

检索验证：

```text
POST /documents/search
确认能命中 OCR 提取出的文本内容
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/32-scanned-pdf-ocr-summary.md
```
