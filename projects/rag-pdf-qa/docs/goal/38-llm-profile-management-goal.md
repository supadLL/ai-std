# 第 38 步执行目标：LLM API 配置档案管理

## 1. 背景

第 37 步已经把单一 DeepSeek 配置升级为可选择多个 OpenAI-compatible Provider。

但当前设置页仍然是“单个表单”的形态：

```text
Provider
Base URL
Model
API Key
Timeout
```

实际使用时，更合理的方式是把模型配置做成一个可管理列表：

```text
供应商
API Key 是否已配置
模型
是否启用
操作：启用 / 编辑 / 删除 / 新增
```

这样可以提前配置多个模型，例如 DeepSeek、Qwen、Ollama、自定义网关，然后一键切换当前底层 LLM。

## 2. 本次目标

本次完成：

```text
1. 新增 LLM 配置档案 profile 概念
2. 支持保存多个 LLM profile 到 data/runtime_settings.json
3. 支持设置一个 active profile 作为当前 LLM
4. 保留第 37 步单字段配置兼容
5. Web UI 设置页展示 profile 管理表格
6. Web UI 支持新增 profile 弹窗
7. Web UI 支持编辑 profile 弹窗
8. Web UI 支持删除非启用 profile
9. Web UI 支持一键启用 profile
10. 不在接口和页面展示真实 API Key
11. Swagger Docs 可测试新增接口
```

## 3. 不做什么

本次不做：

```text
多模型同时回答
多模型横向评测
模型价格统计
在线拉取 provider 模型列表
真实 API Key 解密展示
真实模型连通性探测
Claude 原生 Messages API 适配
```

API Key 只允许新增或覆盖，不允许从后端读回明文。

## 4. 需要修改的文件

预计修改：

```text
app/runtime_settings.py
app/main.py
web/index.html
web/app.js
web/styles.css
tests/test_main_api.py
tests/test_runtime_settings.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

完成后新增：

```text
docs/summary/38-llm-profile-management-summary.md
```

## 5. 接口变化

新增接口：

```text
POST /settings/llm-profiles
PUT /settings/llm-profiles/{profile_id}
DELETE /settings/llm-profiles/{profile_id}
POST /settings/llm-profiles/{profile_id}/activate
```

`GET /settings` 新增：

```json
{
  "active_llm_profile_id": "profile-id",
  "llm_profiles": [
    {
      "profile_id": "profile-id",
      "name": "DeepSeek Pro",
      "provider": "deepseek",
      "base_url": "https://api.deepseek.com",
      "model": "deepseek-v4-pro",
      "enabled": true,
      "api_key_configured": true,
      "api_key_source": "runtime"
    }
  ]
}
```

## 6. 验收标准

完成后应满足：

```text
1. 设置页出现 LLM profile 表格
2. 点击“新增 API”出现弹窗
3. 弹窗可以创建 provider / base_url / model / API Key
4. 表格可以编辑已有 profile
5. 表格可以删除非启用 profile
6. 表格可以一键启用另一个 profile
7. /chat、/rag/ask、/agent/ask 使用当前 active profile
8. API 和页面不返回真实 API Key
9. 旧 llm_* / deepseek_* 配置仍兼容
10. pytest 通过
```

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

接口测试：

```text
GET /settings
POST /settings/llm-profiles
PUT /settings/llm-profiles/{profile_id}
POST /settings/llm-profiles/{profile_id}/activate
DELETE /settings/llm-profiles/{profile_id}
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
进入设置页
新增一个 API 配置
编辑模型名
启用该配置
删除另一个未启用配置
确认真实 API Key 不显示
```

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/38-llm-profile-management-summary.md
```
