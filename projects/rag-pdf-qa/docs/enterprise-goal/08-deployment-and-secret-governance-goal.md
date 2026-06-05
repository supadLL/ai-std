# 企业级第 08 步执行目标：部署、环境和密钥治理

## 1. 背景

企业级项目不能依赖本地手动启动和明文密钥散落。

当前项目已经有 Dockerfile 和启动脚本，但还需要：

```text
Docker Compose 编排
数据库和 Qdrant 服务
环境变量分层
API Key 加密或外部密钥管理
生产/开发配置区分
部署文档
```

## 2. 本次目标

本次建立企业级部署基础：

```text
1. 新增 docker-compose.yml
2. 编排 api / db / qdrant / redis
3. 新增 .env.example 企业版配置
4. LLM API Key 不在接口明文返回
5. 数据库中密钥加密存储
6. 新增部署文档
7. 新增启动健康检查
```

## 3. 不做什么

本次不做：

```text
Kubernetes 生产部署
云厂商 Terraform
企业 Vault 深度集成
灰度发布
多地域容灾
```

## 4. 预计修改文件

```text
docker-compose.yml
Dockerfile
.dockerignore
.env.example
app/config.py
app/security.py
docs/deployment.md
README.md
```

## 5. 环境变量建议

```text
APP_ENV=development/production
APP_SECRET_KEY=
DATABASE_URL=
REDIS_URL=
QDRANT_URL=
QDRANT_API_KEY=
SECRET_ENCRYPTION_KEY=
```

## 6. 验收标准

```text
1. docker compose up 可以启动核心服务
2. /health 返回 ok
3. /docs 可访问
4. API Key 不进入镜像
5. 数据目录不被误提交
6. README 有部署步骤
```

## 7. 测试方式

```powershell
docker compose up --build
Invoke-RestMethod http://127.0.0.1:8000/health
```
