# 第 5 步学习笔记：Embedding 文本向量化

这一步的目标是：

> 把一段文本转换成一组数字向量。

当前新增接口：

```text
POST /embeddings/text
```

它接收一段文本，并返回：

```text
使用的 embedding 模型
向量维度 dimension
向量前 10 个数字预览
```

---

## 1. 为什么需要 embedding

前面我们已经完成：

```text
PDF -> 提取文本 -> 切成 chunk
```

但是计算机不能直接理解“这两段话意思相近”。

比如：

```text
如何订阅激光雷达数据？
```

和：

```text
读取激光雷达数据的方法
```

这两句话字面不一样，但语义接近。

embedding 的作用就是：

```text
把文字转换成数字向量，让计算机可以比较语义相似度。
```

---

## 2. 什么是向量

向量可以先理解成：

```text
一串浮点数
```

例如：

```json
[0.012, -0.083, 0.221, ...]
```

这些数字不是随机数，而是模型对文本语义的数学表示。

意思相近的文本，向量距离通常更近。

意思差很远的文本，向量距离通常更远。

---

## 3. 什么是 dimension

`dimension` 表示这个向量有多少个数字。

当前默认模型：

```text
BAAI/bge-small-zh-v1.5
```

它的维度是：

```text
512
```

也就是说，一段文本会被转换成：

```text
512 个浮点数组成的向量
```

接口不会把 512 个数字全部展示出来，只返回前 10 个作为预览：

```json
{
  "dimension": 512,
  "embedding_preview": [0.01, -0.03, 0.08]
}
```

原因是：

```text
完整向量很长，展示全部不利于阅读。
```

后面存入 Qdrant 时，会存完整向量。

### dimension 能不能人为修改

不能随便改。

`dimension` 是 embedding 模型自己决定的输出规格。

当前模型：

```text
BAAI/bge-small-zh-v1.5
```

固定输出：

```text
512 维向量
```

所以接口返回：

```json
{
  "dimension": 512
}
```

不是因为我们手动指定了 512，而是因为这个模型本身就是 512 维。

如果你换 embedding 模型，dimension 可能会变：

| 模型 | 可能的 dimension |
|---|---|
| `BAAI/bge-small-zh-v1.5` | 512 |
| `jinaai/jina-embeddings-v2-base-zh` | 768 |
| `intfloat/multilingual-e5-large` | 1024 |

后面接 Qdrant 时，dimension 很重要。

Qdrant collection 创建时必须指定向量维度：

```text
如果 embedding 模型输出 512 维，Qdrant collection 也必须按 512 维创建。
```

如果模型输出 512 维，但你把 Qdrant 配成 768 维，后续写入向量会失败。

所以：

```text
dimension = 模型决定的真实向量长度
```

不是普通业务参数，不能为了好看随便改。

---

## 4. embedding 和 LLM 回答有什么区别

这两个容易混。

| 能力 | 输入 | 输出 | 用途 |
|---|---|---|---|
| Chat LLM | 一段文字问题 | 一段文字回答 | 生成答案 |
| Embedding | 一段文字 | 一组数字向量 | 做语义检索 |

当前项目里：

```text
/chat
```

调用 DeepSeek 聊天模型，用来生成回答。

```text
/embeddings/text
```

调用本地 embedding 模型，用来生成向量。

所以：

```text
DeepSeek 负责回答
embedding 模型负责把文本变成可检索的数字
```

---

## 5. 为什么这一步没有继续用 DeepSeek

DeepSeek 当前主要提供聊天补全等生成式接口。

本项目这一步先使用本地开源 embedding 模型：

```text
BAAI/bge-small-zh-v1.5
```

通过：

```text
fastembed
```

在本地生成向量。

这样做的好处：

- 不需要新增 API Key
- 中文支持较好
- 模型体积较小，适合学习
- 后续接 Qdrant 比较顺

---

## 6. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|
| embedding 生成逻辑 | [`app/embedding_client.py`](../../app/embedding_client.py) |
| embedding 接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/embeddings/text")` |
| embedding 模型配置 | [`app/config.py`](../../app/config.py) 里的 `embedding_model` |
| 默认模型配置 | [`.env.example`](../../.env.example) 里的 `EMBEDDING_MODEL` |
| Python 依赖 | [`requirements.txt`](../../requirements.txt) 里的 `fastembed` |

核心函数：

```python
def embed_text(text: str, model_name: str) -> list[float]:
    ...
```

它做的事：

```text
接收文本
加载 embedding 模型
生成向量
返回 list[float]
```

---

## 7. 当前接口返回什么

请求：

```json
{
  "text": "如何订阅激光雷达数据？"
}
```

响应类似：

```json
{
  "text": "如何订阅激光雷达数据？",
  "model": "BAAI/bge-small-zh-v1.5",
  "dimension": 512,
  "embedding_preview": [
    -0.011,
    0.024,
    0.053
  ]
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `text` | 原始文本 |
| `model` | 使用的 embedding 模型 |
| `dimension` | 向量维度 |
| `embedding_preview` | 向量前 10 个数字 |

### preview_count 会不会影响后续查询

不会。

完整 embedding 向量有 512 个数字，但接口只返回前 10 个用于观察：

```python
embedding_preview = vector[:10]
```

所以你看到的：

```json
{
  "preview_count": 10
}
```

只表示：

```text
当前响应里展示了 10 个数字。
```

它不影响：

- embedding 模型
- 向量真实维度
- 后续 Qdrant 存储
- 后续语义检索

后面真正存入 Qdrant 时，会存完整的：

```text
512 维向量
```

不是只存 `embedding_preview` 里的 10 个数字。

所以：

| 字段 | 是否可人为修改 | 是否影响后续查询 |
|---|---|---|
| `dimension` | 不应手动改，模型决定 | 会影响，必须和 Qdrant 维度一致 |
| `embedding_preview` 展示数量 | 可以改，只是展示 | 不影响 |
| `preview_count` | 可以随展示数量变化 | 不影响 |

---

## 8. 如何在 `/docs` 页面测试

打开：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /embeddings/text
```

输入：

```json
{
  "text": "如何订阅激光雷达数据？"
}
```

点 `Execute`。

第一次执行可能会慢一些，因为本地需要下载 embedding 模型。

模型下载完成后，后续会快很多。

这也是为什么第一次调用时，其他接口可能会短暂变慢。

当前代码已经把 embedding 生成放进线程池：

```python
vector = await run_in_threadpool(...)
```

这样可以减少模型加载/计算时对 FastAPI 事件循环的阻塞。

---

## 9. 如何判断 embedding 接口成功

看三个字段：

```text
status code = 200
dimension = 512
embedding_preview 有数字
```

如果满足这三个条件，说明文本已经成功转换成向量。

注意：

```text
embedding_preview 里的数字本身不需要人工理解。
```

你只需要知道：

```text
这些数字会被 Qdrant 用来计算相似度。
```

---

## 10. 什么是相似度

embedding 生成向量后，就可以比较两段文本的语义距离。

例如：

```text
问题：如何订阅激光雷达数据？
chunk A：读取激光雷达数据需要先创建 driver，然后调用 subscribe。
chunk B：设备外壳尺寸为 120mm。
```

理想情况下：

```text
问题向量 和 chunk A 向量 更接近
问题向量 和 chunk B 向量 更远
```

这就是向量检索的基础。

后面 Qdrant 要做的事就是：

```text
给定一个问题向量
从数据库里找最相似的 chunk 向量
```

---

## 11. 当前验证结果

已经测试：

```text
POST /embeddings/text -> 200 OK
```

请求：

```json
{
  "text": "如何订阅激光雷达数据？"
}
```

返回摘要：

```json
{
  "model": "BAAI/bge-small-zh-v1.5",
  "dimension": 512,
  "preview_count": 10
}
```

也确认了 `/docs` 页面已经注册新接口：

```text
/embeddings/text
```

当前所有接口：

```text
/health
/chat
/documents/extract
/documents/chunk
/embeddings/text
```

说明：

```text
文本已经可以成功转换成 512 维向量。
```

---

## 12. 当前不要学什么

现在不要展开：

- Qdrant collection
- 向量索引参数
- cosine / dot / euclidean 的数学细节
- rerank
- Hybrid Search

下一步才是：

```text
把 chunk 的完整向量存入 Qdrant
```

---

## 13. 一句话总结

这一步完成的是：

```text
文本
-> embedding 模型
-> 512 维数字向量
```

它不是用来生成回答的，而是用来做语义检索的。

