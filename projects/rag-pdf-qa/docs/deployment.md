# 部署说明：企业级 RAG 平台雏形

这份文档对应企业级第 08 步：部署、环境和密钥治理。

目标是让项目可以在一台局域网机器上启动，其他人通过这台机器的 IP 和端口访问 Web UI、Swagger Docs，并用已注册/已初始化的账号登录。

---

## 1. 部署前准备

部署机器需要：

```text
Docker Desktop 或 Docker Engine
Git
可访问模型供应商 API 的网络
```

如果只是本机开发，可以继续使用 `.venv` + SQLite；如果要给局域网多人访问，推荐使用 Docker Compose。

---

## 2. 配置环境变量

复制模板：

```powershell
Copy-Item .env.example .env
```

部署前至少修改这些值：

```text
APP_ENV=production
APP_SECRET_KEY=替换成足够长的随机字符串
SECRET_ENCRYPTION_KEY=替换成另一个足够长的随机字符串
LLM_API_KEY=真实模型 API Key
POSTGRES_PASSWORD=替换成数据库密码
```

不要把 `.env` 提交到 GitHub。项目已通过 `.gitignore` 和 `.dockerignore` 排除 `.env`、数据库文件、Qdrant 数据和测试缓存。

---

## 3. Docker Compose 启动

在项目根目录执行：

```powershell
docker compose up --build
```

后台运行：

```powershell
docker compose up --build -d
```

当前 Compose 会启动：

| 服务 | 作用 |
|---|---|
| `api` | FastAPI + Web UI |
| `db` | PostgreSQL 数据库 |
| `qdrant` | 服务化向量库 |
| `redis` | 预留给后续异步队列和缓存 |

默认端口：

```text
Web UI:        http://部署机器IP:8000/app
Swagger Docs: http://部署机器IP:8000/docs
Health Check: http://部署机器IP:8000/health
Qdrant:       http://部署机器IP:6333
```

如果这台机器防火墙没有放行 8000，局域网其他机器会访问不到，需要在系统防火墙里允许入站 TCP 8000。

---

## 4. 初始化和登录

第一次启动后，在 Swagger Docs 或 Web UI 初始化管理员：

```text
POST /auth/bootstrap-admin
```

之后使用：

```text
POST /auth/login
```

拿到 Bearer token 后即可访问文档上传、RAG 问答、评估、设置等接口。Web UI 会把 token 保存在浏览器本地，退出时清除。

---

## 5. 数据和密钥落点

Compose 使用 Docker volume 保存运行数据：

| Volume | 内容 |
|---|---|
| `app_data` | API 服务运行数据 |
| `postgres_data` | PostgreSQL 数据 |
| `qdrant_storage` | Qdrant 向量数据 |
| `redis_data` | Redis 数据 |

数据库里保存的运行时 LLM API Key 和 LLM profile API Key 会以 `enc:v1` 密文格式存储。读取旧明文数据时仍兼容；下一次保存会写入密文。

`SECRET_ENCRYPTION_KEY` 用来解密这些密文。已经有运行数据后，不要随意更换它；如果必须更换，应先清空或重新保存运行时 API Key。

接口响应只返回：

```text
api_key_configured
api_key_source
api_key_label
```

不会返回真实 API Key。

---

## 6. 健康检查

访问：

```text
http://127.0.0.1:8000/health
```

示例字段：

```json
{
  "status": "ok",
  "app_env": "production",
  "database_reachable": true,
  "qdrant_mode": "server",
  "qdrant_url": "http://qdrant:6333",
  "redis_configured": true,
  "secret_encryption_configured": true,
  "warnings": []
}
```

如果生产环境仍使用默认 `APP_SECRET_KEY`、没有配置 `SECRET_ENCRYPTION_KEY`，或仍使用 Qdrant local 模式，`warnings` 会提示。

---

## 7. 常用运维命令

查看服务：

```powershell
docker compose ps
```

查看 API 日志：

```powershell
docker compose logs -f api
```

停止服务：

```powershell
docker compose down
```

停止并删除 volume 会清空数据库和向量数据，谨慎使用：

```powershell
docker compose down -v
```

---

## 8. 当前边界

本步骤不做 Kubernetes、Terraform、Vault/KMS 深度集成和多地域容灾。

当前目标是形成可落地的企业部署雏形：

```text
Docker Compose
PostgreSQL
Qdrant server
Redis 预留
健康检查
密钥脱敏与数据库加密存储
局域网访问说明
```
