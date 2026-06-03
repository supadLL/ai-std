# 第 4 步学习笔记：文档切分 chunk

这一步的目标是：

> 把 PDF 提取出来的长文本，切成多个适合后续检索的小文本块。

当前新增接口：

```text
POST /documents/chunk
```

它接收一个 PDF 文件，并返回：

```text
这个 PDF 被切成了多少个 chunk
每个 chunk 来自第几页
每个 chunk 有多少字符
每个 chunk 的文本内容
```

---

## 1. 为什么需要文档切分

上一阶段我们已经能做：

```text
PDF -> 提取文本
```

但一整份 PDF 的文本通常太长，不能直接进入 RAG。

原因有三个：

1. 大模型一次能读的上下文长度有限。
2. 文本太长会让检索不精准。
3. 后续向量数据库检索的是“小块文本”，不是整本书。

所以 RAG 通常会先做：

```text
长文档 -> 切成多个 chunk -> 对每个 chunk 做 embedding -> 存入向量库
```

你可以把 chunk 理解成：

> 一个适合被搜索、被引用、被喂给大模型的小段文本。

---

## 2. 这一步新增了哪些代码

| 内容 | 对应代码 |
|---|---|
| 文本切分逻辑 | [`app/text_splitter.py`](../../app/text_splitter.py) |
| PDF 每页保留完整文本 | [`app/pdf_extractor.py`](../../app/pdf_extractor.py) 里的 `ExtractedPage.text` |
| 文件上传 + 切分接口 | [`app/main.py`](../../app/main.py) 里的 `@app.post("/documents/chunk")` |
| 接口响应结构 | [`app/main.py`](../../app/main.py) 里的 `PdfChunkResponse` 和 `TextChunkResponse` |

新增接口：

```python
@app.post("/documents/chunk", response_model=PdfChunkResponse)
async def chunk_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
) -> PdfChunkResponse:
    ...
```

这表示：

```text
上传一个 PDF
同时可以传 chunk_size 和 overlap 两个参数
服务端返回切分后的 chunks
```

---

## 3. 什么是 chunk_size

`chunk_size` 表示每个文本块尽量控制在多少字符以内。

当前默认值：

```text
chunk_size = 800
```

也就是：

```text
每个 chunk 尽量不超过 800 个字符
```

注意：这里先按“字符数”切，不按 token 切。

原因是初学阶段字符数更直观。后面做成本统计和精细优化时，再引入 token 级切分。

更直观地说，假设有一段文本：

```text
ABCDEFGHIJ
```

如果：

```text
chunk_size = 4
overlap = 0
```

大概会切成：

```text
chunk 1: ABCD
chunk 2: EFGH
chunk 3: IJ
```

所以 `chunk_size` 控制的是：

```text
每一块最多装多少内容
```

在真实项目里，`chunk_size = 800` 的意思就是：

```text
每个 chunk 尽量是一段 800 字以内的文本
```

它不是页数，也不是文件大小，而是文本长度。

### chunk_size 太小的问题

比如：

```text
chunk_size = 100
```

可能导致一句话、一个步骤、一个代码片段被切断。

结果是：

```text
语义不完整
检索命中了也没法回答
```

### chunk_size 太大的问题

比如：

```text
chunk_size = 3000
```

一个 chunk 里可能混入太多主题。

结果是：

```text
检索不精准
喂给大模型的上下文噪声太多
```

所以当前先用：

```text
800
```

作为默认值。

---

## 4. 什么是 overlap

`overlap` 表示相邻 chunk 之间重复保留多少字符。

当前默认值：

```text
overlap = 100
```

假设：

```text
chunk_size = 800
overlap = 100
```

可以粗略理解成：

```text
第 1 块：第 1 到 800 个字符
第 2 块：从第 701 个字符附近开始
```

中间重复的 100 个字符，就是 overlap。

继续用这个例子：

```text
ABCDEFGHIJ
```

如果：

```text
chunk_size = 4
overlap = 1
```

大概会切成：

```text
chunk 1: ABCD
chunk 2: DEFG
chunk 3: GHIJ
```

你会发现：

```text
D 同时出现在 chunk 1 和 chunk 2
G 同时出现在 chunk 2 和 chunk 3
```

这些重复部分就是 `overlap`。

所以 `overlap` 控制的是：

```text
相邻两块之间重复保留多少上下文
```

### 为什么需要 overlap

因为关键信息可能刚好卡在两个 chunk 的边界。

如果没有 overlap：

```text
前半句在 chunk 1
后半句在 chunk 2
```

检索时命中任何一个 chunk，都可能信息不完整。

有了 overlap 后，相邻块之间会共享一小段上下文，能减少“切断语义”的问题。

---

## 5. 当前切分策略是什么

当前策略是：

```text
先按页处理
每页内部再切 chunk
尽量在自然边界切开
相邻 chunk 保留 overlap
```

代码位置：

```text
app/text_splitter.py
```

核心函数：

```python
split_pdf_text(extracted, chunk_size=800, overlap=100)
```

它会遍历每一页：

```python
for page in extracted.pages:
    for chunk_text in _split_text_by_page(...):
        ...
```

每个 chunk 都带着：

```text
chunk_id
page_number
char_count
text
```

这样后面做 RAG 时，可以知道答案来源于 PDF 的哪一页。

---

## 6. 什么是“自然边界”

代码不会完全机械地每 800 个字符切一刀。

它会尽量找这些边界：

```python
separators = ["\n\n", "\n", "。", "；", "，", ". ", " "]
```

含义：

| 分隔符 | 优先级含义 |
|---|---|
| `\n\n` | 段落边界 |
| `\n` | 换行 |
| `。` | 中文句号 |
| `；` | 中文分号 |
| `，` | 中文逗号 |
| `. ` | 英文句号 |
| 空格 | 英文单词边界 |

这样做的目的：

```text
尽量不要把一句话、一个段落、一个代码片段切得太碎
```

这是一种简化版的 RecursiveCharacterTextSplitter 思路。

---

## 7. 为什么现在不直接用 LangChain

LangChain 里有成熟的 `RecursiveCharacterTextSplitter`。

但当前阶段我们先自己实现一个简化版。

原因：

1. 你能真正理解切分逻辑。
2. 面试时能讲清楚为什么这么切。
3. 后面如果换成 LangChain，也知道它大概在帮你做什么。

学习目标不是“会调用一个库”，而是理解：

```text
文档为什么要切
切多大
为什么要 overlap
切分结果怎么影响检索质量
```

---

## 8. 当前接口返回什么

调用：

```text
POST /documents/chunk
```

返回结构：

```json
{
  "filename": "用户使用手册.pdf",
  "page_count": 10,
  "char_count": 5419,
  "chunk_size": 800,
  "overlap": 100,
  "chunk_count": 12,
  "scanned_like": false,
  "chunks": [
    {
      "chunk_id": 1,
      "page_number": 1,
      "char_count": 650,
      "text": "..."
    }
  ]
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `chunk_size` | 本次切分目标大小 |
| `overlap` | 相邻 chunk 重叠字符数 |
| `chunk_count` | 总共切出了多少块 |
| `chunk_id` | 第几个 chunk |
| `page_number` | 这个 chunk 来自 PDF 第几页 |
| `char_count` | 这个 chunk 的字符数 |
| `text` | chunk 的文本内容 |

---

## 9. 如何在 `/docs` 页面测试

打开：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /documents/chunk
```

操作步骤：

1. 点 `Try it out`
2. 上传一个 PDF
3. `chunk_size` 先填 `800`
4. `overlap` 先填 `100`
5. 点 `Execute`
6. 查看 `chunk_count` 和 `chunks`

你可以试着改参数：

```text
chunk_size = 500, overlap = 50
chunk_size = 1000, overlap = 100
```

观察：

```text
chunk_count 会怎么变化
每个 chunk 的内容是否完整
```

### `Send empty value` 是什么

`Send empty value` 是 Swagger UI 自动生成页面里的选项，不是我们自己写的功能。

它的作用是控制：

```text
当输入框是空的时，到底要不要把这个空值发送给后端。
```

以 `chunk_size` 为例。

如果你不填 `chunk_size`，并且不发送空值，后端会使用代码里的默认值：

```python
chunk_size: int = Form(800)
```

也就是：

```text
chunk_size = 800
```

但如果你勾选 `Send empty value`，Swagger UI 可能会把它当成空字符串发给后端：

```text
chunk_size = ""
```

这时 FastAPI 会尝试把空字符串转换成整数。

因为：

```text
"" 不是合法整数
```

所以可能返回：

```text
422 Unprocessable Entity
```

简单记：

| 操作 | 含义 | 对当前接口的影响 |
|---|---|---|
| 不填参数，不勾选 `Send empty value` | 不发送这个字段 | 使用默认值，比如 `chunk_size=800` |
| 不填参数，勾选 `Send empty value` | 发送空字符串 | 可能触发参数校验错误 |
| 填入 `800` | 发送具体值 | 使用你填的值 |

所以测试当前接口时，建议：

```text
要么填具体数字
要么不填并不勾选 Send empty value
```

---

## 10. 如何判断切分结果好不好

先看三个指标：

| 指标 | 怎么看 |
|---|---|
| `chunk_count` | 太多说明切太碎，太少说明切太粗 |
| `char_count` | 单个 chunk 是否接近但不超过 chunk_size |
| `text` | 是否基本保留一段完整语义 |

人工检查时重点看：

1. 有没有把一句话切断得很难懂。
2. 有没有把完全不相关的主题塞进同一个 chunk。
3. 代码片段是否被切得太碎。
4. 标题和正文是否还在相邻位置。

这一步不追求完美。

目标是先做出一个可用的 baseline。

### 更直观的判断方式

可以把一个 chunk 理解成：

```text
将来检索命中后，喂给大模型的一张“资料卡片”。
```

所以好的 chunk 应该像一张能单独看懂的资料卡片：

```text
有主题
有足够上下文
能回答一个小问题
没有塞进太多无关内容
```

不好的 chunk 常见有两种。

第一种：切得太碎。

```text
chunk_size 太小
```

表现是：

```text
一个操作步骤被拆成好几块
一段代码被拆成好几块
标题和正文分开了
单个 chunk 看不懂它在说什么
```

例如用户问：

```text
如何订阅激光雷达数据？
```

如果一个 chunk 只有：

```text
laser_driver->subscribe(subscriber_id);
```

它就太碎了，因为缺少：

```text
需要 include 什么头文件
driver 怎么获取
subscriber_id 是什么
前后步骤是什么
```

第二种：切得太粗。

```text
chunk_size 太大
```

表现是：

```text
一个 chunk 里混了多个主题
既讲初始化，又讲订阅，又讲异常处理，又讲释放资源
检索虽然命中了，但里面噪声很多
```

例如用户只问：

```text
如何取消订阅？
```

如果命中的 chunk 同时包含：

```text
初始化
读取数据
错误处理
取消订阅
资源释放
```

那它就可能太粗了，大模型需要从一堆无关内容里找答案。

### 判断好坏的核心问题

不要只看数字，要问自己：

```text
如果用户问一个具体问题，命中的这个 chunk 能不能单独支撑回答？
```

能，就比较好。

不能，就要调参数。

### 用你的用户手册举例

你的 PDF 是技术手册，里面有：

```text
标题
说明文字
代码片段
函数名
include 路径
操作步骤
```

这种文档通常不适合切太小。

如果：

```text
chunk_size = 200
overlap = 50
```

容易把一段代码和说明拆碎，适合验证接口功能，但不适合作为最终 RAG 参数。

如果：

```text
chunk_size = 800
overlap = 100
```

通常更适合技术手册，因为一个 chunk 更可能包含完整步骤和代码上下文。

### 为什么 chunk 的 char_count 不一定等于 chunk_size

`chunk_size = 800` 的意思不是：

```text
每个 chunk 必须刚好 800 字
```

而是：

```text
每个 chunk 尽量不超过 800 字
```

当前代码还会尽量在自然边界切开，比如：

```text
换行
句号
逗号
空格
```

并且当前是按页切分，不会强行把第 1 页和第 2 页合并成一个 chunk。

所以你会看到：

```text
chunk_size = 800
但某个 chunk 的 char_count 可能只有 398
```

这不一定是坏事，可能只是因为这一页本身内容比较短，或者在自然边界处提前切开了。

### 一个实用调参流程

你可以这样试：

```text
先用 chunk_size=800, overlap=100
准备 5 个用户可能会问的问题
人工看每个问题对应的 chunk 是否能支撑回答
如果 chunk 看起来太碎，就调大 chunk_size
如果 chunk 里混了太多主题，就调小 chunk_size
如果边界处信息丢了，就调大 overlap
```

对你的技术手册，建议先比较这三组：

```text
500 / 80
800 / 100
1000 / 150
```

暂时不要用：

```text
200 / 50
```

除非只是验证接口是否能切分。

---

## 11. 参数限制

当前代码限制：

```text
100 <= chunk_size <= 3000
0 <= overlap < chunk_size
```

原因：

- `chunk_size` 太小，切出来没有意义。
- `chunk_size` 太大，检索会变粗。
- `overlap` 不能大于等于 `chunk_size`，否则切分可能无法向前推进。

如果参数不合法，接口会返回 `400`。

---

## 12. 当前验证结果

已经用仓库里的样本 PDF 测过：

```text
D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
```

接口返回：

```text
POST /documents/chunk -> 200 OK
```

切分摘要：

```json
{
  "filename": "GUIagent.pdf",
  "page_count": 43,
  "char_count": 9511,
  "chunk_size": 800,
  "overlap": 100,
  "chunk_count": 43
}
```

也确认了 `/docs` 页面已经注册新接口：

```text
/documents/chunk
```

参数保护也测过：

```text
chunk_size = 100
overlap = 100
```

接口返回：

```text
400
```

错误信息：

```json
{
  "detail": "overlap must be smaller than chunk_size"
}
```

说明：

```text
overlap 不能大于等于 chunk_size，否则切分无法稳定向前推进。
```

---

## 13. 这一阶段你要掌握什么

现在你要能说清楚：

1. chunk 是 RAG 检索的基本单位。
2. `chunk_size` 控制每块文本大概多长。
3. `overlap` 用来保留相邻块的上下文。
4. 切太小会丢语义，切太大会检索不精准。
5. 当前切分是按页进行的，每个 chunk 保留 `page_number`。
6. 自然边界切分比机械按字符切更合理。
7. 这一步还没有做 embedding，也没有接 Qdrant。

---

## 14. 当前不要学什么

现在不要展开：

- 向量数据库
- embedding 模型
- Qdrant collection
- Hybrid Search
- RAG Prompt
- rerank

下一步才是：

```text
把 chunk 转成向量，并存入向量数据库
```

---

## 15. 一句话总结

这一步完成的是：

```text
PDF 文本
-> 按页切分
-> 按 chunk_size 控制长度
-> 用 overlap 保留上下文
-> 返回带页码的 chunks
```

这是 RAG 检索链路的前置步骤。

