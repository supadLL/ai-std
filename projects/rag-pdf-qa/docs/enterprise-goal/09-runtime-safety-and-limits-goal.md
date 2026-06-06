# 企业级第 09 步执行目标：运行安全边界和限流

## 1. 背景

企业级部署不仅要能启动，还要避免最基础的运行风险：

```text
过大的上传文件拖垮内存或磁盘
单个客户端短时间高频请求打满 API
生产配置没有明确的限流和上传边界
健康检查看不到当前保护配置
```

第 08 步已经完成 Compose、健康检查和密钥治理，本步骤继续补齐运行时安全边界。

## 2. 本次目标

```text
1. 新增可配置上传大小上限
2. 所有上传入口统一使用同一套大小限制
3. 新增基础请求限流中间件
4. 限流支持通过环境变量开启、关闭和调参
5. /health 返回限流和上传大小配置状态
6. .env.example、部署文档和 README 说明配置方式
7. 新增测试覆盖上传大小限制和 429 限流响应
```

## 3. 不做什么

本次不做：

```text
Nginx / API Gateway 限流
Redis 分布式限流
按用户套餐计费限流
复杂滑动窗口算法优化
文件病毒扫描
对象存储配额管理
```

后续如果进入多实例部署，再把当前应用内限流替换或升级为 Redis / 网关级限流。

## 4. 预计修改文件

```text
app/config.py
app/main.py
.env.example
docs/deployment.md
README.md
docs/00-project-continuation-guide.md
tests/test_main_api.py
docs/enterprise-summary/09-runtime-safety-and-limits-summary.md
```

## 5. 环境变量建议

```text
MAX_UPLOAD_BYTES=10485760
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

建议生产环境开启：

```text
RATE_LIMIT_ENABLED=true
```

## 6. 验收标准

```text
1. 上传超过 MAX_UPLOAD_BYTES 返回 413
2. 所有 UploadFile 入口都使用统一限制
3. 超过限流阈值返回 429，并带 Retry-After
4. /health 能看到 max_upload_bytes 和 rate_limit_enabled
5. 原有测试全部通过
6. README 和部署文档说明配置方式
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
