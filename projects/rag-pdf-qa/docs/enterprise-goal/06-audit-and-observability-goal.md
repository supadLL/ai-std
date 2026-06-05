# 企业级第 06 步执行目标：审计日志、指标和可观测性

## 1. 背景

企业场景需要知道：

```text
谁上传了文件
谁删除了文档
谁修改了模型配置
谁问了什么问题
LLM 调用了哪个 provider
一次 RAG 问答耗时多少
失败发生在哪个阶段
```

当前项目只有最小错误处理，没有完整审计和可观测体系。

## 2. 本次目标

本次建立基础可观测能力：

```text
1. 新增 audit_logs 表
2. 关键操作写审计日志
3. 增加请求 request_id
4. 增加结构化日志
5. 记录 RAG 检索耗时、LLM 耗时、总耗时
6. 记录 LLM provider、model、token usage
7. 增加健康检查和指标端点
```

## 3. 不做什么

本次不做：

```text
完整 SIEM 集成
复杂日志检索系统
分布式 tracing 全链路
Prometheus Grafana 完整大盘
```

可以先建立结构化日志和数据库审计。

## 4. 预计修改文件

```text
app/audit.py
app/logging_config.py
app/main.py
app/deepseek_client.py
app/vector_store.py
tests/test_audit.py
tests/test_main_api.py
```

## 5. 审计事件建议

```text
auth.login
document.index
document.delete
document.reindex
rag.ask
agent.ask
settings.update
llm_profile.create
llm_profile.activate
```

## 6. 验收标准

```text
1. 关键接口产生 audit log
2. audit log 包含 user_id、tenant_id、action、resource_id、request_id
3. RAG 响应或日志记录耗时
4. LLM usage 可追踪
5. pytest 通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_audit.py tests\test_main_api.py
```
