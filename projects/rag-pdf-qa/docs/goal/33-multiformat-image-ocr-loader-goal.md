# 第 33 步执行目标：多格式文档图片内容抽取与 OCR 统一链路

这一步的目标是：

> 把第 32 步只面向扫描型 PDF 的 OCR 能力，扩展成面向多格式文档的“文本 + 表格 + 图片 OCR”统一解析思路。

---

## 1. 背景

第 32 步已经实现：

```text
PDF 文本优先
无文本页面启用 OCR 兜底
OCR chunk 进入同一条 RAG 链路
sources 返回 extraction_method
```

但实际知识库文件不只 PDF 会混合图片和文本。

常见情况包括：

```text
docx：正文 + 表格 + 截图
xlsx：单元格文本 + 内嵌图片
markdown：正文 + 本地图片引用
html / 网页：正文 + 图片 / 图表
pptx：文本框 + 截图 + 流程图
```

如果后续只继续围绕 PDF OCR 做增强，会让文档解析链路变窄。

所以这一阶段要先把“多格式文档中的图片内容”纳入统一规划，并实现一个可落地的最小链路。

---

## 2. 本次目标

本次完成：

```text
1. 抽象 ParsedBlock 或类似结构，区分 text / table / image_ocr
2. 保持现有 ParsedDocument / TextChunk 向后兼容
3. 支持至少一种非 PDF 文件的图片 OCR 最小解析
4. 推荐优先选择 docx 内嵌图片 OCR，范围清晰且容易测试
5. OCR block 能进入当前 chunk / embedding / Qdrant 链路
6. sources 能区分 text、table、image_ocr、pdf_ocr 等来源
7. README 和 00 号文档说明当前支持范围和限制
```

推荐最小实现路径：

```text
docx 文本和表格保持原有逻辑
-> 识别 docx 内嵌图片
-> 对图片执行 OCR
-> 把 OCR 文本追加为独立 section 或 block
-> split_parsed_document 继续切分
-> extraction_method 标记为 image_ocr
```

---

## 3. 不做什么

本次不做：

- 所有格式一次性完整支持
- 图片语义理解
- 图表结构理解
- 多模态大模型识图
- pptx 完整解析
- 网页抓取
- 图片 caption 自动生成
- 高精度版面还原

---

## 4. 需要修改的文件

预计修改：

```text
app/document_loaders.py
app/text_splitter.py
app/vector_store.py
app/main.py
requirements.txt
README.md
docs/00-project-continuation-guide.md
docs/summary/README.md
```

可能新增：

```text
app/image_ocr.py
tests/test_multiformat_image_ocr.py
```

完成后新增：

```text
docs/summary/33-multiformat-image-ocr-loader-summary.md
```

---

## 5. 接口变化

优先复用：

```text
POST /documents/index
```

可能新增表单参数：

```text
enable_image_ocr: bool = false
ocr_language: str = "chi_sim+eng"
```

返回中可扩展：

```text
image_ocr_count: number
extraction_methods: string[]
```

sources 中继续使用：

```text
extraction_method
```

推荐值：

```text
text
table
pdf_ocr
image_ocr
```

---

## 6. 验收标准

完成后应满足：

```text
1. 原有 PDF / Markdown / txt / docx / csv / xlsx 入库不回退
2. 至少 docx 内嵌图片 OCR 可以入库
3. 图片 OCR 文本可以被 chunk、embedding 和检索
4. sources 能看出该内容来自 image_ocr
5. 未安装 Tesseract 或图片 OCR 依赖时错误提示清晰
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
上传包含内嵌图片的 docx
enable_image_ocr = true
ocr_language = chi_sim+eng
```

检索验证：

```text
POST /documents/search
确认能命中图片 OCR 出来的文字
确认 source extraction_method = image_ocr
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/33-multiformat-image-ocr-loader-summary.md
```
