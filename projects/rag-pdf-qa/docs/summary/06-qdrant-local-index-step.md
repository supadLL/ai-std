# 第 6 步学习笔记：Qdrant 本地向量存储与检索

这一步的目标是：

> 把 PDF 切出来的 chunk 向量存入 Qdrant，并能用问题检索出相关 chunk。

当前新增两个接口：

```text
POST /documents/index
POST /documents/search
```

这一步开始，项目从“能生成向量”进入到“能检索知识库”。

---

## 1. 为什么需要 Qdrant

前面已经完成：

```text
PDF -> 提取文本 -> chunk 切分 -> embedding 向量化
```

但是 embedding 生成出来后，需要有地方保存。

普通数据库适合查：

```text
id = 123
name = "xxx"
```

向量数据库适合查：

```text
哪几段文本和这个问题语义最接近？
```

Qdrant 就是一个向量数据库。

它负责：

```text
存储 chunk 的完整向量
存储 chunk 的文本和页码等 payload
根据问题向量检索最相似的 chunk
```

---

## 2. 为什么先用本地模式

真实项目通常会用 Docker 启动 Qdrant 服务。

但当前你的环境还没有 Docker，所以先用 Qdrant Python client 的本地持久化模式：

```python
QdrantClient(path=".qdrant")
```

这会把向量数据保存到项目目录下：

```text
.qdrant/
```

这个目录已经写入 `.gitignore`，不会提交到 Git。

本地模式的好处：

- 不需要 Docker
- 不需要额外服务进程
- 适合学习和本地验证
- 后面切到 Docker Qdrant 时，核心概念基本不变

---

## 3. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|
| Qdrant 本地 client、collection、upsert、search | [`app/vector_store.py`](../../app/vector_store.py) |
| 文档索引接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/documents/index")` |
| 文档检索接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/documents/search")` |
| Qdrant 配置 | [`app/config.py`](../../app/config.py) 里的 `qdrant_local_path` 和 `qdrant_collection` |
| 默认配置 | [`.env.example`](../../.env.example) 里的 `QDRANT_LOCAL_PATH` 和 `QDRANT_COLLECTION` |
| Python 依赖 | [`requirements.txt`](../../requirements.txt) 里的 `qdrant-client` |

---

## 4. collection 是什么

Qdrant 里的 collection 可以先理解成：

```text
一张专门存向量的表
```

当前默认 collection：

```text
rag_chunks
```

它里面存的是：

```text
每个 chunk 的向量
每个 chunk 的文本
每个 chunk 来自哪个 PDF、哪一页
```

后面如果你做多个知识库，可以用多个 collection 隔离。

---

## 5. point 是什么

Qdrant 里每条向量记录叫 point。

一个 point 大概包含：

```text
id
vector
payload
```

当前项目里，一个 chunk 对应一个 point。

也就是：

```text
1 个 chunk -> 1 个 embedding vector -> 1 个 Qdrant point
```

---

## 6. vector 是什么

vector 就是 embedding 模型输出的完整向量。

当前模型：

```text
BAAI/bge-small-zh-v1.5
```

输出：

```text
512 维向量
```

注意：

```text
存入 Qdrant 的是完整 512 维向量，不是 embedding_preview 的前 10 个数字。
```

`embedding_preview` 只是给人看的调试信息。

---

## 7. payload 是什么

payload 是和向量一起存储的业务信息。

当前每个 point 的 payload 包含：

```json
{
  "filename": "用户使用手册.pdf",
  "page_number": 1,
  "chunk_id": 1,
  "char_count": 398,
  "text": "chunk 的完整文本"
}
```

为什么需要 payload？

因为向量本身只是一串数字。

检索命中后，我们需要知道：

```text
这段文本是什么
来自哪个文件
来自哪一页
```

这些信息都放在 payload 里。

---

## 8. upsert 是什么

upsert = update + insert。

意思是：

```text
如果 point 不存在，就插入
如果 point 已存在，就更新
```

当前代码里：

```python
client.upsert(collection_name=collection_name, points=points)
```

用于把 chunk 向量写入 Qdrant。

---

## 9. 为什么 dimension 必须匹配

Qdrant collection 创建时必须指定向量维度：

```python
models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
```

当前 embedding 模型输出 512 维，所以 collection 也必须是 512 维。

如果 collection 是 768 维，而你写入 512 维向量，会失败。

所以：

```text
embedding model 的 dimension
= Qdrant collection 的 vector size
```

这两个必须一致。

---

## 10. distance 是什么

当前使用：

```text
COSINE
```

也就是余弦相似度。

你现在不需要深入数学，只要知道：

```text
Qdrant 会用它判断两个向量的语义距离。
```

问题向量和 chunk 向量越接近，score 通常越高。

---

## 11. `/documents/index` 做了什么

调用：

```text
POST /documents/index
```

流程是：

```text
上传 PDF
-> 提取文本
-> 切分 chunk
-> 每个 chunk 生成 embedding
-> 确保 Qdrant collection 存在
-> upsert 到 Qdrant
```

返回类似：

```json
{
  "filename": "用户使用手册.pdf",
  "collection": "rag_chunks",
  "page_count": 10,
  "chunk_count": 10,
  "indexed_count": 10,
  "dimension": 512,
  "local_path": ".qdrant"
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `chunk_count` | 切出了多少个 chunk |
| `indexed_count` | 成功写入 Qdrant 的 point 数 |
| `dimension` | 写入向量的维度 |
| `local_path` | 本地 Qdrant 数据目录 |

---

## 12. `/documents/search` 做了什么

调用：

```text
POST /documents/search
```

请求：

```json
{
  "query": "如何订阅激光雷达数据？",
  "limit": 5
}
```

流程是：

```text
用户问题
-> 生成 query embedding
-> 去 Qdrant 查最相似的 chunk
-> 返回命中的文本和页码
```

返回类似：

```json
{
  "query": "如何订阅激光雷达数据？",
  "collection": "rag_chunks",
  "limit": 5,
  "results": [
    {
      "score": 0.78,
      "filename": "用户使用手册.pdf",
      "page_number": 1,
      "chunk_id": 1,
      "text": "..."
    }
  ]
}
```

现在这个接口还不会让 DeepSeek 回答。

它只做：

```text
检索相关资料
```

下一步才会把检索结果喂给 DeepSeek，形成完整 RAG 回答。

---

## 13. 如何在 `/docs` 页面测试

打开：

```text
http://127.0.0.1:8000/docs
```

先测试：

```text
POST /documents/index
```

上传 PDF，参数先用：

```text
chunk_size = 800
overlap = 100
```

看到 `indexed_count > 0`，说明写入成功。

然后测试：

```text
POST /documents/search
```

输入：

```json
{
  "query": "如何订阅激光雷达数据？",
  "limit": 5
}
```

看返回的 `results` 里是否有相关 chunk。

---

## 14. 如何判断检索是否有效

先人工看三个东西：

| 字段 | 怎么看 |
|---|---|
| `score` | 相似度分数，越高通常越相关 |
| `page_number` | 是否来自正确页附近 |
| `text` | 是否真的包含能回答问题的信息 |

不要只看 score。

真正重要的是：

```text
返回的 text 能不能支撑回答用户问题。
```

如果检索结果不相关，后面 RAG 回答也会差。

---

## 15. 当前不要学什么

## 15. 当前验证结果

已经用仓库里的样本 PDF 测过：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

索引接口返回：

```text
POST /documents/index -> 200 OK
```

索引摘要：

```json
{
  "filename": "GUIagent.pdf",
  "collection": "rag_chunks",
  "page_count": 43,
  "chunk_count": 43,
  "indexed_count": 43,
  "dimension": 512,
  "local_path": ".qdrant"
}
```

说明：

```text
43 个 chunk 已经写入本地 Qdrant，向量维度是 512。
```

本地数据目录也已经生成：

```text
.qdrant/
├── collection/
├── .lock
└── meta.json
```

检索接口也已验证：

```text
POST /documents/search -> 200 OK
```

测试问题：

```text
GUI 智能体有哪些技术分支？
```

Top 1 命中结果：

```json
{
  "score": 0.7441551493935123,
  "filename": "GUIagent.pdf",
  "page_number": 11,
  "chunk_id": 11,
  "text": "技术分支\n❑ 基于闭源模型构建的GUI Agent..."
}
```

这个结果是合理的，因为问题问的是“技术分支”，检索结果命中了标题为“技术分支”的 chunk。

也确认了 `/docs` 页面已经注册新接口：

```text
/documents/index
/documents/search
```

---

## 16. 当前不要学什么

现在不要展开：

- Docker Qdrant 部署
- 分布式 Qdrant
- HNSW 索引参数
- Hybrid Search
- rerank
- 多 collection 权限隔离

当前目标只是：

```text
本地完成向量存储和语义检索闭环。
```

---

## 17. 一句话总结

这一步完成的是：

```text
chunk 文本
-> embedding 完整向量
-> Qdrant 本地 collection
-> 根据问题检索相关 chunk
```

这是完整 RAG 回答之前的最后一块基础设施。

