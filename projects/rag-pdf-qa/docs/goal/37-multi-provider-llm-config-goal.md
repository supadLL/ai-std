# 第 37 步执行目标：多模型供应商与自定义 API 配置

这一步的目标是：

> 把当前偏 DeepSeek 的 LLM 接入方式，升级为可选择供应商、可选择模型、可填写自定义 API 的通用模型配置能力。

---

## 1. 背景

当前项目已经支持在 Web UI 设置：

```text
DeepSeek base_url
DeepSeek model
API Key
timeout
RAG prompt
```

但这仍然是偏单一供应商的设计。

后续如果别人使用本项目，可能希望接入：

```text
DeepSeek
通义千问 / Qwen
豆包 / Doubao
OpenAI / GPT
Claude
Ollama 本地模型
MiniMax
其他 OpenAI-compatible API
自定义 API Base URL
```

所以本步需要把“DeepSeek 设置”抽象为“LLM Provider 设置”。

---

## 2. 本次目标

本次完成：

```text
1. 新增 LLM provider 配置概念
2. Web UI 设置页支持选择供应商
3. Web UI 设置页支持选择或填写模型名
4. Web UI 设置页支持自定义 API Base URL
5. 支持 OpenAI-compatible Chat Completions 接口
6. 保留 DeepSeek 作为默认供应商
7. 支持 Ollama 本地模型的最小配置说明
8. README / 00 号文档更新多模型配置说明
```

建议 provider 选项：

```text
deepseek
qwen
doubao
openai
claude
ollama
minimax
custom_openai_compatible
```

---

## 3. 不做什么

本次不做：

- 多模型同时回答
- 多模型横向评测
- 自动选择最优模型
- Claude 原生 Messages API 完整适配
- 非 OpenAI-compatible 协议的深度封装
- 模型价格自动统计
- 在线拉取模型列表

如果 Claude、豆包、MiniMax 等供应商当前使用 OpenAI-compatible endpoint，可以先走通用兼容模式。

---

## 4. 需要修改的文件

预计修改：

```text
app/config.py
app/runtime_settings.py
app/deepseek_client.py
app/main.py
web/index.html
web/app.js
web/styles.css
README.md
docs/00-project-continuation-guide.md
```

可能新增：

```text
app/llm_client.py
app/llm_providers.py
```

测试：

```text
tests/test_main_api.py
tests/test_agent.py
tests/test_runtime_settings.py
tests/test_llm_client.py
```

完成后新增：

```text
docs/summary/37-multi-provider-llm-config-summary.md
```

---

## 5. 接口变化

扩展：

```text
GET /settings
PUT /settings
POST /chat
POST /rag/ask
POST /agent/ask
```

`GET /settings` 建议新增：

```json
{
  "llm_provider": "deepseek",
  "llm_base_url": "https://api.deepseek.com",
  "llm_model": "deepseek-chat",
  "llm_api_key_configured": true,
  "llm_api_key_source": "env",
  "available_providers": [
    {
      "provider": "deepseek",
      "label": "DeepSeek",
      "default_base_url": "https://api.deepseek.com",
      "default_models": ["deepseek-chat", "deepseek-reasoner"]
    }
  ]
}
```

兼容策略：

```text
旧字段 deepseek_base_url / deepseek_model / api_key_configured 可暂时保留
新字段 llm_provider / llm_base_url / llm_model / llm_api_key_configured 作为主字段
```

---

## 6. 环境变量建议

保留旧变量：

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
```

新增通用变量：

```text
LLM_PROVIDER=deepseek
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
```

优先级建议：

```text
运行时设置 data/runtime_settings.json
-> 通用 LLM_* 环境变量
-> 旧 DeepSeek 环境变量
-> provider 默认值
```

---

## 7. Web UI 变化

设置页从：

```text
API Base URL
LLM Model
API Key
```

升级为：

```text
Provider
Model
API Base URL
API Key
Timeout
```

交互建议：

```text
1. 选择 provider 后自动填入默认 base_url 和推荐模型
2. 允许用户手动覆盖 base_url 和 model
3. provider 为 custom_openai_compatible 时，base_url 和 model 必填
4. provider 为 ollama 时，base_url 默认 http://127.0.0.1:11434/v1，API Key 可为空或填 ollama
5. 不在页面展示真实 API Key
```

---

## 8. 验收标准

完成后应满足：

```text
1. DeepSeek 现有流程不被破坏
2. 设置页可以选择不同 provider
3. 可以填写自定义 base_url 和 model
4. /chat 使用当前 provider 配置
5. /rag/ask 使用当前 provider 配置
6. /agent/ask 使用当前 provider 配置
7. 不返回真实 API Key
8. Swagger Docs 可测试
9. pytest 通过
```

---

## 9. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

接口测试：

```text
GET /settings
PUT /settings
POST /chat
POST /rag/ask
POST /agent/ask
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
进入设置页
切换 provider
保存后重新读取
确认不会展示真实 API Key
```

---

## 10. 完成后的 summary 文档

完成后写入：

```text
docs/summary/37-multi-provider-llm-config-summary.md
```
