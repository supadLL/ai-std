# 企业级第 19 步完成总结：HTML 网页正文入库治理

## 完成内容

本步骤把保存后的网页 HTML 文件接入现有 RAG 入库链路：

- `load_document_from_bytes` 支持 `.html` 和 `.htm`。
- 新增 HTML 正文解析器，基于 Python 标准库 `HTMLParser`。
- 提取 `title`、heading、paragraph、list 等正文内容。
- 跳过 `script`、`style`、`noscript`、`svg`、`canvas`、`nav`、`header`、`footer`、`form`、`button` 等噪声内容。
- HTML 正文进入 `ParsedDocument(file_type="html")`。
- HTML 正文 section 标记 `extraction_method=text`。
- HTML 表格行单独转换为可检索文本，并标记 `extraction_method=table`。
- `/documents/index`、`/documents/index-jobs` 和 reindex 支持 `.html/.htm`。
- 检索、RAG 和 Agent sources 可以显示 `file_type=html`。

## 涉及文件

```text
app/document_loaders.py
app/main.py
tests/test_document_loaders.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-goal/19-html-web-page-body-loader-goal.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_document_loaders.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤支持的是“用户上传保存好的 HTML / HTM 文件”。

暂时不做服务器主动抓取 URL、网页爬虫、登录态网页抓取、JavaScript 渲染页面解析、站点地图批量导入或网页图片 OCR。
