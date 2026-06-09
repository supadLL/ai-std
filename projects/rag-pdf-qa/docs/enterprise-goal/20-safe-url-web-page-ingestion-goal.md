# 企业级第 20 步执行目标：安全单 URL 网页入库

## 1. 背景

第 19 步已经支持上传保存好的 `.html` / `.htm` 文件，并把网页正文接入 RAG 链路。

但实际使用时，用户经常只拿到一个网页 URL。企业落地不能直接做无边界爬虫，因为服务器主动访问用户输入的 URL 会带来 SSRF、内网探测、重定向绕过、超大响应和非 HTML 内容等风险。

第 20 步目标是实现一个“安全单 URL 网页入库”最小闭环：只抓取一个明确 URL，做严格安全校验，再复用第 19 步 HTML loader 入库。

## 2. 本次目标

```text
1. 新增安全网页抓取模块
2. 新增 POST /web-pages/index
3. 新增 POST /knowledge-bases/{knowledge_base_id}/web-pages/index
4. 仅允许 http / https URL
5. 默认阻止 localhost、私网、链路本地、多播、保留地址等 host
6. 限制下载大小、超时时间、重定向次数和 HTML 内容类型
7. 抓取到的 HTML 复用 HTML loader、chunk、embedding、Qdrant 和 document metadata 链路
8. 写入 audit log
9. 单元测试和文档更新
```

## 3. 不做什么

本步骤不做：

```text
网页爬虫
站点地图批量导入
登录态网页抓取
JavaScript 渲染页面解析
定时同步
网页差异更新
图片 OCR 或图片 caption
自定义 CSS selector 抽取
```

## 4. 预期接口

```text
POST /web-pages/index
POST /knowledge-bases/{knowledge_base_id}/web-pages/index
```

请求示例：

```json
{
  "url": "https://example.com/docs/intro",
  "chunk_size": 800,
  "overlap": 100,
  "reindex": false
}
```

## 5. 预期修改文件

```text
app/config.py
app/web_page_fetcher.py
app/main.py
tests/test_web_page_fetcher.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-summary/20-safe-url-web-page-ingestion-summary.md
```

## 6. 验收标准

```text
1. 合法 HTML URL 可以入库，并返回 file_type=html
2. localhost / 127.0.0.1 / 私网 IP URL 默认被拒绝
3. 非 http/https URL 被拒绝
4. 非 HTML content-type 被拒绝
5. 超过大小限制的响应被拒绝
6. 入库结果写入 audit action=web_page.index
7. 已有文件上传入库流程不回退
8. pytest tests/test_web_page_fetcher.py tests/test_main_api.py 通过
9. pytest 全量通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_web_page_fetcher.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
