# 企业级第 20 步完成总结：安全单 URL 网页入库

## 完成内容

本步骤在第 19 步 HTML 文件入库基础上，新增安全的单 URL 网页入库：

- 新增 `app/web_page_fetcher.py`。
- 新增 `POST /web-pages/index`。
- 新增 `POST /knowledge-bases/{knowledge_base_id}/web-pages/index`。
- 只允许 `http` / `https` URL。
- 默认阻止 `localhost`、私网、链路本地、多播、保留地址和未指定地址。
- 抓取前校验 URL host，重定向后再次校验最终 URL。
- 限制超时时间、最大响应字节数和 HTML content-type。
- 抓取到的 HTML 复用第 19 步 HTML loader、chunk、embedding、Qdrant、document metadata 和 source storage 链路。
- URL 入库写入审计 action `web_page.index`。
- `/health` 返回 `web_fetch_enabled`、`web_fetch_max_bytes` 和 `web_fetch_allow_private_hosts`。
- 生产环境如果允许私网抓取，会在 `/health.warnings` 中返回 `web_fetch_private_hosts_allowed`。

## 新增配置

```text
WEB_FETCH_ENABLED=true
WEB_FETCH_TIMEOUT_SECONDS=10
WEB_FETCH_MAX_BYTES=2097152
WEB_FETCH_ALLOW_PRIVATE_HOSTS=false
```

## 涉及文件

```text
app/config.py
app/web_page_fetcher.py
app/main.py
tests/test_web_page_fetcher.py
tests/test_main_api.py
.env.example
README.md
docs/deployment.md
docs/00-project-continuation-guide.md
docs/enterprise-goal/README.md
docs/enterprise-goal/20-safe-url-web-page-ingestion-goal.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_web_page_fetcher.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 当前限制

本步骤只抓取单个公开 HTML URL。

暂时不做网页爬虫、站点地图批量导入、登录态网页抓取、JavaScript 渲染页面解析、定时同步或自定义 CSS selector 抽取。
