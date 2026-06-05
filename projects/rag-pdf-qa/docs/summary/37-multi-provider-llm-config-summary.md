# 第 37 步完成总结：多模型供应商与自定义 API 配置

## 1. 本次完成了什么

本次把原来偏 DeepSeek 的模型接入方式升级为通用 LLM Provider 配置。

当前默认仍然是 DeepSeek，但已经支持在 Web UI 和 `/settings` 中切换：

```text
DeepSeek
Qwen / 通义千问
Doubao / 豆包
OpenAI / GPT
Claude compatible
Ollama local
MiniMax
Custom OpenAI-compatible
```

本次实现仍以 OpenAI-compatible Chat Completions 协议为主。Claude 原生 Messages API、多模型同时回答、价格统计和在线模型列表拉取不在本次范围。

## 2. 改动文件

核心代码：

```text
app/llm_providers.py
app/config.py
app/runtime_settings.py
app/deepseek_client.py
app/main.py
```

Web UI：

```text
web/index.html
web/app.js
```

测试：

```text
tests/test_main_api.py
tests/test_agent.py
tests/test_runtime_settings.py
tests/test_llm_client.py
```

配置和文档：

```text
.env.example
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

## 3. 接口变化

`GET /settings` 新增主字段：

```json
{
  "llm_provider": "deepseek",
  "llm_base_url": "https://api.deepseek.com",
  "llm_model": "deepseek-v4-flash",
  "llm_api_key_configured": true,
  "llm_api_key_source": "env",
  "available_providers": []
}
```

`PUT /settings` 新增可保存字段：

```json
{
  "llm_provider": "qwen",
  "llm_api_key": "只提交，不返回",
  "llm_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "llm_model": "qwen-plus"
}
```

旧字段仍然兼容：

```text
deepseek_api_key
deepseek_base_url
deepseek_model
api_key_configured
api_key_source
```

这样之前的 DeepSeek 配置和测试不会被破坏，新项目优先使用 `LLM_*`。

## 4. Web UI 变化

设置页新增 `Provider` 下拉框。

选择 provider 后会自动填充推荐的：

```text
API Base URL
LLM Model
```

模型字段仍然允许手动输入，并通过 datalist 提供推荐模型候选。

API Key 输入框仍然不会展示真实密钥，保存后只显示密钥来源：

```text
runtime
env
none
```

Ollama provider 不强制要求 API Key，默认地址为：

```text
http://127.0.0.1:11434/v1
```

## 5. 环境变量变化

推荐新配置：

```text
LLM_PROVIDER=deepseek
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

旧配置仍可用：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

运行时配置优先级：

```text
data/runtime_settings.json
-> LLM_* 环境变量
-> DEEPSEEK_* 旧环境变量
-> provider 默认值
```

## 6. 验证结果

已执行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_api.py tests\test_agent.py tests\test_runtime_settings.py tests\test_llm_client.py
```

结果：

```text
28 passed
```

后续提交前还需要跑全量：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
git diff --check
```

## 7. 后续影响

这一步让项目从“DeepSeek 单供应商 RAG 工具”变成“可配置 LLM Provider 的本地知识库 RAG Agent”。

后续可以继续做：

```text
项目演示路径整理
README 面向新用户的配置说明
简历项目描述
模型响应质量横向评估
Claude 原生 Messages API 适配
本地 Ollama 体验优化
```

下一步建议执行：

```text
docs/goal/38-project-demo-and-resume-polish-goal.md
```
