# 第 2 步学习笔记：配置 API Key 并测试 `/chat`

这一步的目标是验证：

```text
本地 FastAPI 服务
-> 读取 .env 里的 DeepSeek API Key
-> 调用 DeepSeek Chat Completions
-> 返回模型回答和 token usage
```

我们已经完成了一次真实测试，结果是：

```text
POST /chat -> 200 OK
```

返回中包含：

- `reply`：模型回答
- `model`：实际使用的模型
- `usage`：本次调用消耗的 token 信息

---

## 1. 正确的 API Key 放在哪里

真实 API Key 应该放在：

```text
.env
```

不要放在：

```text
.env.example
```

原因：

| 文件 | 是否应该放真实 key | 原因 |
|---|---|---|
| `.env` | 是 | 本地私密配置，已经被 `.gitignore` 忽略 |
| `.env.example` | 否 | 模板文件，通常会提交到 Git，不能放秘密信息 |

正确做法：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`：

```text
DEEPSEEK_API_KEY=你的真实 API Key
```

---

## 2. 为什么要重启服务

如果服务已经启动，然后你才修改 `.env`，旧进程可能没有读到最新配置。

所以改完 `.env` 后，建议重启：

```powershell
uvicorn app.main:app --reload
```

当前代码里 `get_settings()` 也会重新加载 `.env`，但初学阶段先养成“改配置后重启服务”的习惯，会少很多排查成本。

---

## 3. 第一个测试：健康检查

先测试服务本身是否活着：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

期望结果：

```json
{
  "status": "ok"
}
```

这个测试不调用 DeepSeek，只证明：

- FastAPI 服务启动了
- 端口能访问
- 路由注册正常

---

## 4. 第二个测试：真实调用 `/chat`

调用：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{ message = "用一句话解释什么是 FastAPI" } | ConvertTo-Json)
```

期望结果类似：

```json
{
  "reply": "FastAPI 是一个用于快速构建 API 的 Python Web 框架。",
  "model": "deepseek-v4-flash",
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 75,
    "total_tokens": 103
  }
}
```

你不需要背 token 字段，但要知道：

| 字段 | 含义 |
|---|---|
| `prompt_tokens` | 输入消耗的 token |
| `completion_tokens` | 模型输出消耗的 token |
| `total_tokens` | 本次请求总消耗 |

这些数据后面会用于成本统计。

---

## 5. 当前测试通过说明什么

`POST /chat -> 200 OK` 说明这一整条链路已经通了：

```text
请求 JSON
-> FastAPI 路由
-> Pydantic 参数校验
-> 读取 .env
-> httpx 调 DeepSeek
-> 解析 DeepSeek 响应
-> 返回 JSON
```

这就是 AI 项目的第一个地基。

后续做 RAG 时，只是把中间这一步：

```text
直接把用户问题发给 DeepSeek
```

改成：

```text
先检索 PDF 相关内容
-> 把检索结果和用户问题一起发给 DeepSeek
```

---

## 6. 常见错误怎么判断

| 现象 | 可能原因 | 处理方式 |
|---|---|---|
| `DEEPSEEK_API_KEY is not configured` | 没有 `.env`，或 key 写在 `.env.example`，或 `.env` 编码异常 | 确认真实 key 在 `.env`，重启服务 |
| `401` | API Key 错误或失效 | 重新检查 DeepSeek 控制台里的 key |
| `402` 或余额相关错误 | 账户余额/额度不足 | 检查 DeepSeek 账户额度 |
| `429` | 请求太频繁 | 等一会儿再试，后面会学限流和重试 |
| `502` | 你的服务调用 DeepSeek 失败 | 看返回的 `detail` 字段 |
| `422` | 请求 JSON 格式不对 | 检查是否传了 `{"message":"..."}` |
| 中文显示成 `ä¸...` 这类乱码 | PowerShell 按错误编码解析了 UTF-8 响应 | 服务响应头需要带 `charset=utf-8`，当前代码已处理 |

### PowerShell 中文乱码说明

如果接口返回的中文变成类似：

```text
ä¸FastAPI æ...
```

说明请求本身成功了，但客户端显示/解析编码错了。

这次的原因是 FastAPI 默认响应头是：

```text
Content-Type: application/json
```

Windows PowerShell 可能没有按 UTF-8 解码中文。

所以我们在 `app/main.py` 里加了自定义响应类型：

```python
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"
```

让响应头变成：

```text
Content-Type: application/json; charset=utf-8
```

这样 PowerShell 就能正确显示中文。

---

## 7. 这一阶段你要掌握什么

你现在要能说清楚：

1. `.env` 是放本地私密配置的。
2. `.env.example` 只是模板，不能放真实 key。
3. `/health` 用来测服务是否启动。
4. `/chat` 用来测完整 LLM 调用链路。
5. 返回里的 `usage` 是 token 消耗，后面能用于成本统计。
6. `200 OK` 说明调用成功。
7. `502` 往往说明你的服务调用外部 API 失败。

掌握这些就可以进入下一步：PDF 文档解析。

