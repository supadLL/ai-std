# 企业级第 19 步执行目标：HTML 网页正文入库治理

## 1. 背景

当前系统已经支持 PDF、PDF 表格、PDF 内嵌图片 OCR、扫描型 PDF OCR、Markdown、txt、docx、csv 和 xlsx 入库。

企业知识库中还会出现大量网页内容，例如产品文档、内部 wiki 导出页、公告页面和保存下来的 HTML 文档。之前系统不能把网页正文作为知识库来源，用户只能手工复制成 txt 或 Markdown。

第 19 步目标是支持上传 `.html` / `.htm` 文件，并把网页正文清理后接入现有 RAG 入库链路。

## 2. 本次目标

```text
1. 新增 HTML / htm 文档 loader
2. 解析 HTML title、heading、paragraph、list、table 等正文内容
3. 跳过 script、style、noscript、svg、canvas、nav、header、footer、form 等噪声节点
4. HTML 正文进入 ParsedDocument，file_type=html
5. HTML 表格行标记为 extraction_method=table
6. /documents/index、/documents/index-jobs 和 reindex 支持 .html/.htm
7. 检索和 RAG sources 可以显示 file_type=html
8. 单元测试和文档更新
```

## 3. 不做什么

本步骤不做：

```text
服务器主动抓取 URL
网页爬虫
登录态网页抓取
JavaScript 渲染页面解析
站点地图批量导入
图片 caption 或网页图片 OCR
CSS 选择器自定义抽取
```

先支持“已保存的网页 / HTML 文件上传”，避免引入 SSRF、内网探测和远程抓取安全问题。

## 4. 预期行为

用户上传：

```text
docs.html
wiki.htm
```

系统应当：

```text
HTML title / heading / paragraph / list -> extraction_method=text
HTML table rows -> extraction_method=table
```

然后复用现有链路：

```text
HTML 文件
-> ParsedDocument
-> split_parsed_document
-> embedding
-> Qdrant
-> RAG / Agent sources
```

## 5. 预期修改文件

```text
app/document_loaders.py
app/main.py
tests/test_document_loaders.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/19-html-web-page-body-loader-summary.md
```

## 6. 验收标准

```text
1. load_document_from_bytes 支持 .html 和 .htm
2. HTML loader 能提取 title、正文段落、列表和表格内容
3. HTML loader 会跳过 script/style/nav/header/footer 等噪声
4. HTML 表格内容以 extraction_method=table 进入 chunk
5. /documents/index 接受 .html 文件并返回 file_type=html
6. 已有 PDF、docx、csv、xlsx、Markdown、txt 流程不回退
7. pytest tests/test_document_loaders.py tests/test_main_api.py 通过
8. pytest 全量通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_document_loaders.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
