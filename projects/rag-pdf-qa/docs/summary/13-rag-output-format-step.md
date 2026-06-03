# 第 13 步学习笔记：固定 RAG 输出格式

这一步的目标是：

> 让 `/rag/ask` 的回答不再完全自由发挥，而是尽量稳定输出“答案 / 依据 / 资料不足之处”三段结构。

同时根据 `review.md` 的审查建议，先修复一个真实运行期 bug，并引入第一批最小 pytest 回归测试。

---

## 1. 为什么需要固定 RAG 输出格式

第 12 步已经把 `sources` 返回结构优化为：

```text
source_id
score
filename
page_number
chunk_id
preview
```

但 `reply` 仍然由模型自由生成。

这会带来几个问题：

```text
回答结构不稳定
不一定说明依据来自哪个 Source
后续 UI 不好拆分答案和依据
测试时不容易判断回答是否合格
```

所以第 13 步先不做 JSON mode，也不做 function calling。

当前只要求模型用 Markdown 文本按固定格式回答。

---

## 2. 本次新增的回答格式

`/rag/ask` 的响应结构不变。

变化只发生在：

```text
reply
```

现在 prompt 要求 DeepSeek 尽量按以下结构回答：

```text
答案：
- ...

依据：
- [Source 1] ...
- [Source 2] ...

资料不足之处：
- ...
```

如果资料足够，`资料不足之处` 应写：

```text
未发现明显不足
```

如果资料不足，模型应该明确说明缺少什么，不要编造。

---

## 3. 这一步修改了哪些代码

| 文件 | 修改 |
|---|---|
| `app/main.py` | 修复 `/documents/search` 返回时误用未定义变量 `results` 的 bug |
| `app/main.py` | 优化 `_build_rag_messages()`，加入固定三段式输出格式 |
| `app/text_splitter.py` | 为 `_find_reasonable_boundary()` 增加短窗口提前返回 |
| `app/vector_store.py` | Qdrant collection 维度不匹配时增加重建索引提示 |
| `requirements.txt` | 增加 `pytest` |
| `tests/` | 新增第一批最小回归测试 |

---

## 4. 为什么先修 `/documents/search`

审查 `review.md` 后发现，当前代码还有一个直接 bug：

```python
results=[
    _to_search_result_response(result)
    for result in results
]
```

这里的 `results` 没有定义。

正确变量应为：

```python
retrieved_results
```

如果不修这个问题，后续第 14 步建立 RAG 评估问题集时，`/documents/search` 会在成功检索后运行时报错。

---

## 5. 本次新增测试

新增：

```text
tests/test_main_api.py
tests/test_text_splitter.py
tests/test_vector_store.py
```

覆盖：

```text
/documents/search 能正常返回 retrieved_results
_build_rag_messages() 包含三段式输出格式约束
split_pdf_text() 能保持页码和 chunk_id
_find_reasonable_boundary() 在短窗口下直接返回 end
ensure_collection() 维度冲突时包含重建索引提示
```

---

## 6. 如何测试

先安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

运行编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests
```

运行自动化测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## 7. Swagger Docs 怎么验证

启动服务：

```powershell
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

建议验证：

```text
POST /documents/search
POST /rag/ask
```

`/rag/ask` 的请求结构不变：

```json
{
  "question": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "score_threshold": 0.5
}
```

重点查看：

```text
reply 是否包含：答案：
reply 是否包含：依据：
reply 是否包含：资料不足之处：
sources 是否仍然正常返回
```

---

## 8. 当前还没做什么

本次没有做：

```text
JSON mode
used_sources 字段
answer_confidence
rerank
hybrid search
Agent 工具路由
UI
```

这是刻意控制范围。

当前阶段先让回答格式更稳定，并为后续评估建立测试底座。

---

## 9. 下一步

下一步进入：

```text
第 14 步：建立 RAG 评估问题集
```

对应 goal：

```text
docs/goal/14-rag-evaluation-dataset-goal.md
```

