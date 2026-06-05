# 第 31 步执行目标：一键启动与 Docker 化

这一步的目标是：

> 让本项目从“本机手动启动”升级为“新环境也能快速唤醒”，降低换电脑、clone 项目、演示项目时的启动成本。

---

## 1. 背景

当前项目已经具备完整的本地 RAG 链路，但启动方式仍然依赖开发者记住命令：

```text
创建虚拟环境
安装依赖
配置 .env
启动 uvicorn 8000
访问 /app 或 /docs
```

这对学习过程是够用的，但如果要作为简历项目、演示项目或后续给别人使用，需要更清晰的一键启动能力。

---

## 2. 本次目标

本次完成：

```text
1. 新增 Windows 本地一键启动脚本
2. 新增环境检查脚本，检查 .venv / .env / 端口 8000 / 依赖安装状态
3. 新增 Dockerfile 或 docker-compose 最小方案
4. 保持默认端口 8000
5. README 增加本地启动、Docker 启动、常见失败处理
6. 不暴露真实 API Key
```

推荐优先级：

```text
先做本地一键启动脚本
再做 Dockerfile
最后考虑 docker-compose
```

---

## 3. 不做什么

本次不做：

- 云端部署
- 登录鉴权
- HTTPS
- CI/CD
- 多环境配置中心
- 把 Qdrant local 替换成远程 Qdrant

---

## 4. 需要修改的文件

预计新增：

```text
scripts/start.ps1
scripts/check_environment.ps1
Dockerfile
.dockerignore
```

预计修改：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/README.md
```

完成后新增：

```text
docs/summary/31-one-click-start-and-docker-summary.md
```

---

## 5. 接口变化

本次不新增后端接口。

服务入口仍然保持：

```text
Web UI:        http://127.0.0.1:8000/app
Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/health
```

---

## 6. 验收标准

完成后应满足：

```text
1. 本地执行 scripts/start.ps1 能启动 8000 服务
2. scripts/check_environment.ps1 能提示缺失项
3. 没有 .env 时能提示用户复制 .env.example
4. 8000 被占用时能给出清晰提示
5. Docker 构建不包含真实 .env、.qdrant、data/runtime_settings.json
6. /health、/app、/docs 均可访问
```

---

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

启动测试：

```powershell
.\scripts\check_environment.ps1
.\scripts\start.ps1
```

接口验证：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

Docker 验证：

```powershell
docker build -t local-rag-agent .
docker run --rm -p 8000:8000 --env-file .env local-rag-agent
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/31-one-click-start-and-docker-summary.md
```
