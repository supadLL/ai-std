# 企业级第 09 步完成总结：运行安全边界和限流

本步骤补齐企业部署后的最小运行保护：上传大小限制和基础请求限流。

---

## 1. 本次新增能力

```text
MAX_UPLOAD_BYTES 可配置上传大小上限
所有 UploadFile 入口统一使用上传大小检查
应用内基础请求限流
超过限流阈值返回 429
429 响应带 Retry-After
/health 返回上传和限流配置状态
Docker Compose 生产默认开启限流
```

---

## 2. 新增配置

```text
MAX_UPLOAD_BYTES=10485760
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

开发环境默认不启用限流，生产环境默认启用限流。Compose 中显式设置：

```text
RATE_LIMIT_ENABLED=true
```

---

## 3. 保护范围

统一上传限制覆盖：

```text
POST /documents/extract
POST /documents/chunk
POST /documents/index
POST /documents/index-jobs
POST /documents/{document_id}/reindex
```

限流在 FastAPI middleware 层执行，按客户端 IP 统计。以下路径豁免：

```text
/health
/docs
/openapi.json
/redoc
/web/*
OPTIONS
```

---

## 4. 修改文件

| 文件 | 说明 |
|---|---|
| `app/config.py` | 新增上传和限流配置 |
| `app/main.py` | 新增限流 middleware、统一上传读取、health 字段 |
| `.env.example` | 新增配置模板 |
| `docker-compose.yml` | Compose 生产默认开启限流 |
| `README.md` | 更新能力和配置说明 |
| `docs/deployment.md` | 更新部署配置 |
| `docs/00-project-continuation-guide.md` | 更新项目阶段 |
| `tests/test_main_api.py` | 覆盖 413 和 429 |
| `docs/enterprise-goal/09-runtime-safety-and-limits-goal.md` | 第 09 步目标 |

---

## 5. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

结果：

```text
tests/test_main_api.py: 23 passed
full pytest: 76 passed
```

关键验收：

```text
超出 MAX_UPLOAD_BYTES 返回 413
超过 RATE_LIMIT_REQUESTS 返回 429
429 带 Retry-After
/health 返回 max_upload_bytes 和 rate_limit_* 字段
```

---

## 6. 当前边界

本次是单进程应用内限流。多实例部署时应升级到：

```text
Redis 分布式限流
API Gateway / Nginx 限流
更完整的文件扫描和配额治理
```
