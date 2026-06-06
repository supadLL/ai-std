# 企业级第 08 步完成总结：部署、环境和密钥治理

本步骤把项目从“本机手动启动”推进到“可用 Docker Compose 在局域网部署”的企业级基础形态。

---

## 1. 本次新增能力

```text
Docker Compose 编排 api / db / qdrant / redis
企业版 .env.example 配置模板
Dockerfile 健康检查
/health 启动健康检查
APP_ENV / REDIS_URL / SECRET_ENCRYPTION_KEY 配置
数据库内 LLM API Key 加密存储
部署文档 docs/deployment.md
运行数据和密钥构建忽略规则
```

---

## 2. 部署方式

复制环境模板：

```powershell
Copy-Item .env.example .env
```

生产或局域网共享部署前，修改：

```text
APP_ENV=production
APP_SECRET_KEY=随机长密钥
SECRET_ENCRYPTION_KEY=随机长密钥
LLM_API_KEY=真实模型 API Key
POSTGRES_PASSWORD=数据库密码
```

启动：

```powershell
docker compose up --build
```

访问：

```text
http://部署机器IP:8000/app
http://部署机器IP:8000/docs
http://部署机器IP:8000/health
```

---

## 3. 密钥治理

本次新增 `app.security.encrypt_secret()` 和 `decrypt_secret()`：

```text
明文 -> enc:v1:<nonce>:<ciphertext>:<tag>
```

当前加密用于：

```text
runtime_settings.deepseek_api_key
runtime_settings.llm_api_key
llm_profiles.api_key
```

读取旧明文数据时仍兼容；保存时会写回密文。

注意：`SECRET_ENCRYPTION_KEY` 是解密依据，已经有运行数据后不要随意更换；如果必须更换，需要重新保存运行时 API Key。

接口仍然只返回：

```text
api_key_configured
api_key_source
api_key_label
```

不会返回真实 API Key。

---

## 4. 健康检查

`GET /health` 现在返回：

```text
status
app_env
database_reachable
qdrant_mode
qdrant_url
redis_configured
secret_encryption_configured
warnings
```

如果数据库不可达，会返回 `503`，Docker healthcheck 会据此判断 API 是否健康。

生产环境如果仍使用默认 `APP_SECRET_KEY`、没有配置 `SECRET_ENCRYPTION_KEY`，或使用 Qdrant local 模式，`warnings` 会提示。

---

## 5. 修改文件

| 文件 | 说明 |
|---|---|
| `docker-compose.yml` | 编排 api / PostgreSQL / Qdrant / Redis |
| `Dockerfile` | 增加健康检查、迁移文件和评估问题集 |
| `.env.example` | 企业部署配置模板 |
| `.dockerignore` | 排除密钥、运行数据和缓存 |
| `.gitignore` | 排除运行数据目录和测试临时目录 |
| `requirements.txt` | 增加 PostgreSQL 驱动 |
| `app/config.py` | 增加 APP_ENV、REDIS_URL、SECRET_ENCRYPTION_KEY |
| `app/security.py` | 增加密钥加密/解密 |
| `app/runtime_settings.py` | API Key 入库加密、读取解密 |
| `app/main.py` | `/health` 启动健康检查 |
| `docs/deployment.md` | 新增部署说明 |
| `tests/test_runtime_settings.py` | 验证密钥密文入库 |
| `tests/test_main_api.py` | 验证 health 不泄露敏感值 |

---

## 6. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_settings.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
```

结果：

```text
25 passed
```

最终仍需执行完整回归：

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

如本机安装 Docker，可额外执行：

```powershell
docker compose config
docker compose up --build
Invoke-RestMethod http://127.0.0.1:8000/health
```

---

## 7. 当前边界

本次没有做：

```text
Kubernetes
Terraform
Vault/KMS 深度集成
灰度发布
多地域容灾
Redis 队列替代当前后台任务
```

这些属于后续生产化深化方向。
