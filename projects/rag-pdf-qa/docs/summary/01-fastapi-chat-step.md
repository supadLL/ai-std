# 第 1 步学习笔记：跑通 FastAPI + DeepSeek `/chat`

这一步的目标不是学完整的 AI Agent，也不是马上做 RAG。

这一步只做一件事：

> 写一个最小后端服务，提供 `POST /chat` 接口，收到用户问题后调用 DeepSeek，并把回答返回给用户。

只要这一步跑通，后面的 PDF 解析、向量检索、RAG、Agent 工具调用，本质上都是继续往这个服务里加模块。

---

## 1. 这一步实际做了什么

我们在 `ai-std/projects/rag-pdf-qa/` 下创建了一个最小 Python 后端项目：

```text
rag-pdf-qa/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── deepseek_client.py
│   └── main.py
├── docs/
│   └── 01-fastapi-chat-step.md
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

每个文件的作用：

| 文件 | 作用 |
|---|---|
| `requirements.txt` | 记录项目依赖，比如 FastAPI、uvicorn、httpx |
| `.env.example` | 环境变量模板，告诉你需要配置哪些密钥和参数 |
| `.gitignore` | 避免把 `.env`、虚拟环境、缓存文件提交到 Git |
| `app/main.py` | FastAPI 入口，定义 `/health` 和 `/chat` 接口 |
| `app/config.py` | 从 `.env` 读取配置，比如 DeepSeek API Key |
| `app/deepseek_client.py` | 封装调用 DeepSeek API 的 HTTP 请求 |
| `docs/summary/01-fastapi-chat-step.md` | 你正在读的学习笔记 |

---

## 2. 为什么第一步要先做 `/chat`

AI Agent 项目看起来概念很多：

- LLM
- RAG
- Embedding
- Vector DB
- Function Calling
- Memory
- Tool
- Agent Loop

但它们最终都要落到一个后端服务里。

后端服务最基础的能力就是：

```text
接收请求 -> 处理逻辑 -> 返回响应
```

所以第一步先做：

```text
用户发问题 -> FastAPI 收到问题 -> 调 DeepSeek -> 返回回答
```

这条链路跑通后，你就有了一个“能活”的项目。后面加 PDF、Qdrant、Redis，都只是往中间的“处理逻辑”里继续加东西。

---

## 3. FastAPI 是什么

FastAPI 是 Python 的 Web 后端框架。

你可以先把它理解成：

> 一个帮你快速写 HTTP 接口的工具。

不用 FastAPI 的话，你要自己处理很多底层细节：

- 监听端口
- 解析 HTTP 请求
- 解析 JSON
- 校验参数
- 组织响应
- 生成接口文档

用了 FastAPI 后，你只需要写类似这样的代码：

```python
@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    ...
```

这段代码的意思是：

```text
当有人用 POST 方法访问 /chat 时，执行 chat 这个函数。
```

可以用 C/C++ 的思路类比：

```text
路径 /chat 就像一个事件名
chat 函数就是这个事件对应的回调函数
FastAPI 负责把 HTTP 请求分发给这个函数
```

你暂时不需要理解所有 FastAPI 特性，只需要先掌握三件事：

| 概念 | 你现在要知道的意思 |
|---|---|
| `FastAPI()` | 创建一个后端应用 |
| `@app.get(...)` / `@app.post(...)` | 定义接口路径和请求方法 |
| Pydantic `BaseModel` | 定义请求和响应的 JSON 结构 |

---

## 4. `/docs` 页面是从哪里来的

你可以访问：

```text
http://127.0.0.1:8000/docs
```

这个页面不是我们手写的。

它是 FastAPI 自动生成的接口文档页面，底层用的是 Swagger UI。

我们只写了：

```python
app = FastAPI(title="RAG PDF QA", version="0.1.0")
```

以及接口：

```python
@app.get("/health")
async def health():
    ...

@app.post("/chat")
async def chat(...):
    ...
```

FastAPI 会扫描这些接口定义，然后自动生成：

```text
/docs
```

这个页面会展示当前服务有哪些接口：

```text
GET /health
POST /chat
```

并且可以直接点 `Try it out` 测试接口。

你可以这样理解：

```text
我们写后端接口代码
-> FastAPI 根据代码生成接口说明
-> Swagger UI 把接口说明渲染成一个网页
-> 你可以在 /docs 页面里直接测试接口
```

所以 `/docs` 是 FastAPI 自带的“接口说明书 + 调试页面”。

这也是 FastAPI 对新手友好的原因之一：你不用额外写测试页面，也能在浏览器里直接看到和调用接口。

对应代码可以直接看这里：

| 你在 `/docs` 里看到的内容 | 对应代码 |
|---|---|
| 页面标题 `RAG PDF QA` | [`app/main.py`](../../app/main.py) 里的 `app = FastAPI(title="RAG PDF QA", ...)` |
| `GET /health` 接口 | [`app/main.py`](../../app/main.py) 里的 `@app.get("/health")` |
| `POST /chat` 接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/chat")` |
| `/chat` 的请求 JSON 结构 | [`app/main.py`](../../app/main.py) 里的 `ChatRequest` |
| `/chat` 的响应 JSON 结构 | [`app/main.py`](../../app/main.py) 里的 `ChatResponse` |
| `/chat` 里真正调用 DeepSeek 的逻辑 | [`app/deepseek_client.py`](../../app/deepseek_client.py) |
| `/chat` 读取 API Key 的逻辑 | [`app/config.py`](../../app/config.py) |

也就是说，你在浏览器里看到的 `/docs`，不是一份独立的手写文档，而是 FastAPI 根据这些 Python 代码自动生成的。

另外 FastAPI 还会自动提供一个机器可读的接口描述：

```text
http://127.0.0.1:8000/openapi.json
```

`/docs` 页面本质上就是根据这个 OpenAPI JSON 渲染出来的。

注意：

```text
OpenAPI 不是 OpenAI。
```

| 名称 | 含义 | 和本项目的关系 |
|---|---|---|
| OpenAPI | 一种 API 接口描述规范，用来描述有哪些接口、参数是什么、返回什么 | FastAPI 自动生成 `/openapi.json` |
| OpenAI | 一家大模型公司，也提供 GPT 等模型 API | 本项目当前没有调用 OpenAI |
| DeepSeek | 当前项目实际调用的大模型 API 服务商 | `/chat` 里调用的是 DeepSeek |

所以当我说“测试 OpenAPI”时，意思是：

```text
检查 FastAPI 自动生成的接口描述里，是否已经注册了新接口。
```

不是说去测试 OpenAI 模型。

现在只需要记住：

| 地址 | 作用 |
|---|---|
| `/health` | 我们自己写的健康检查接口 |
| `/chat` | 我们自己写的大模型聊天接口 |
| `/docs` | FastAPI 自动生成的接口文档页面 |
| `/openapi.json` | FastAPI 自动生成的接口描述数据 |

---

## 5. 什么是 API、HTTP、JSON

### API

API 可以理解成“程序之间约定好的调用入口”。

比如我们的接口：

```text
POST /chat
```

意思是：

> 你把问题发给 `/chat`，我返回 AI 的回答。

### HTTP

HTTP 是浏览器、后端服务、第三方平台之间最常用的通信协议。

常见方法：

| 方法 | 含义 |
|---|---|
| `GET` | 获取信息 |
| `POST` | 提交数据，让服务端处理 |

所以：

```text
GET /health
```

表示检查服务是否活着。

```text
POST /chat
```

表示提交一段用户问题，让服务端调用大模型处理。

### JSON

JSON 是前后端传数据常用的文本格式。

请求示例：

```json
{
  "message": "用一句话解释什么是 RAG"
}
```

响应示例：

```json
{
  "reply": "RAG 是让大模型先检索资料再回答问题的方法。",
  "model": "deepseek-v4-flash",
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 18,
    "total_tokens": 38
  }
}
```

---

## 6. 当前代码的运行流程

当你调用：

```text
POST /chat
```

代码执行流程是：

```text
1. 用户发送 JSON：{"message": "..."}
2. FastAPI 进入 app/main.py 的 chat 函数
3. chat 函数调用 get_settings() 读取配置
4. 创建 DeepSeekClient
5. DeepSeekClient 用 httpx 向 DeepSeek 发 HTTP POST 请求
6. DeepSeek 返回回答
7. FastAPI 把回答包装成 JSON 返回给用户
```

对应文件：

```text
app/main.py
  -> 定义接口

app/config.py
  -> 读取 .env 配置

app/deepseek_client.py
  -> 调 DeepSeek API
```

---

## 7. 关键代码怎么读

### `app/main.py`

核心代码：

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    client = DeepSeekClient(settings)

    try:
        result = await client.chat(request.message)
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(**result)
```

逐行理解：

| 代码 | 含义 |
|---|---|
| `@app.post("/chat")` | 定义一个 POST 接口，路径是 `/chat` |
| `request: ChatRequest` | 请求体必须符合 `ChatRequest` 的结构 |
| `get_settings()` | 读取 `.env` 配置 |
| `DeepSeekClient(settings)` | 创建 DeepSeek 调用客户端 |
| `await client.chat(...)` | 异步调用 DeepSeek |
| `HTTPException(status_code=502, ...)` | 如果 DeepSeek 调用失败，返回 502 |
| `ChatResponse(**result)` | 把结果转换成响应结构 |

### `app/config.py`

这个文件只做一件事：

> 从环境变量里读取配置。

最重要的是：

```python
api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
```

意思是：

> 从环境变量里拿 `DEEPSEEK_API_KEY`。

为什么不把 API Key 写死在代码里？

因为 API Key 是秘密信息，不能提交到 Git，也不能放在公开代码里。

### `app/deepseek_client.py`

这个文件负责真正调用 DeepSeek：

```python
url = f"{self._settings.deepseek_base_url}/chat/completions"
```

DeepSeek 的 Chat Completions 接口路径是：

```text
/chat/completions
```

请求体里最重要的是：

```python
payload = {
    "model": self._settings.deepseek_model,
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": message},
    ],
}
```

可以先这样理解：

| 字段 | 含义 |
|---|---|
| `model` | 使用哪个大模型 |
| `messages` | 对话内容 |
| `system` | 给模型的角色/规则说明 |
| `user` | 用户真正输入的问题 |

---

## 8. 什么是虚拟环境 `.venv`

Python 项目通常会创建自己的虚拟环境：

```text
.venv/
```

它的作用是：

> 把这个项目需要的 Python 依赖隔离起来，不污染系统 Python，也不被其他项目影响。

可以类比成：

```text
每个项目有自己的一套动态库/依赖目录
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

---

## 9. 什么是 uvicorn

FastAPI 只是“应用框架”，它本身不直接监听端口。

真正负责启动服务、监听端口的是 uvicorn。

启动命令：

```powershell
uvicorn app.main:app --reload
```

这句话拆开看：

| 部分 | 含义 |
|---|---|
| `uvicorn` | 启动 ASGI Web 服务 |
| `app.main` | 找到 `app/main.py` 这个模块 |
| `:app` | 使用 `main.py` 里的 `app = FastAPI(...)` 对象 |
| `--reload` | 代码改了自动重启，开发时使用 |

---

## 10. 为什么要有 `/health`

`/health` 是健康检查接口。

它不做复杂逻辑，只返回：

```json
{
  "status": "ok"
}
```

它的作用是确认：

- 服务启动成功
- 端口能访问
- FastAPI 路由正常

以后部署到服务器、Docker、云平台时，健康检查会很常用。

---

## 11. 为什么 `/chat` 失败时返回 502

当前 `/chat` 依赖 DeepSeek。

如果 DeepSeek 超时、返回错误、API Key 没配，说明：

```text
你的服务收到了请求，但调用下游服务失败了。
```

这种情况常用 `502 Bad Gateway`。

可以先粗略理解成：

| 状态码 | 含义 |
|---|---|
| `200` | 成功 |
| `400` | 用户请求有问题 |
| `422` | 请求 JSON 格式或字段校验失败 |
| `500` | 自己服务内部错误 |
| `502` | 自己服务调用外部服务失败 |

---

## 12. 你现在应该掌握到什么程度

这一阶段不要求你“精通 FastAPI”。

你只需要能讲清楚：

1. FastAPI 是用来写 HTTP 接口的 Python 框架。
2. `@app.post("/chat")` 表示定义一个 POST 接口。
3. Pydantic 模型用来定义请求和响应 JSON 结构。
4. `.env` 用来放 API Key 这类不能写死在代码里的配置。
5. `httpx` 用来从你的后端服务里调用 DeepSeek。
6. `uvicorn` 用来把 FastAPI 应用启动起来。
7. `/health` 用来检查服务是否正常。
8. `/docs` 是 FastAPI 自动生成的接口文档和测试页面。
9. `/chat` 当前完成了“用户问题 -> DeepSeek -> 返回回答”的最小链路。

这就够了。

---

## 13. 当前不要学什么

现在不要展开这些内容：

- 不要深入 ASGI 原理
- 不要学习完整 FastAPI 官方文档
- 不要急着学 LangChain
- 不要做前端页面
- 不要接 Qdrant
- 不要写 Agent 循环
- 不要研究复杂项目分层

先把 `/chat` 跑通，再进入 PDF 解析。

---

## 14. 给自己的小练习

为了确认你真的理解了这一步，建议你做 3 个小练习：

1. 把 `/health` 的返回改成：

   ```json
   {
     "status": "ok",
     "service": "rag-pdf-qa"
   }
   ```

2. 在 `/chat` 响应里加一个字段：

   ```json
   {
     "provider": "deepseek"
   }
   ```

3. 故意把 `.env` 里的 API Key 删掉，调用 `/chat`，观察错误提示。

这三个练习都做完，你就完成了第 1 步的学习。

---

## 15. 一句话总结

这一步搭的是 AI 项目的“最小后端底座”：

```text
FastAPI 接收用户请求
-> httpx 调用 DeepSeek
-> 返回 JSON 响应
```

后面的 RAG 和 Agent，本质上都是在这条链路中间继续加能力。

