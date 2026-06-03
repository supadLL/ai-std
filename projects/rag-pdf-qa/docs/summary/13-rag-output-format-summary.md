# 第 13 步完成总结：固定 RAG 输出格式与最小回归测试

本 summary 记录第 13 步实际完成内容。

对应 goal：

```text
docs/goal/13-rag-output-format-goal.md
```

---

## 1. 本次完成了什么

完成三类工作：

```text
1. 修复 /documents/search 的运行期变量 bug
2. 固定 /rag/ask 的 RAG 回答格式
3. 引入第一批最小 pytest 回归测试
```

---

## 2. 代码改动

主要修改：

```text
app/main.py
app/text_splitter.py
app/vector_store.py
requirements.txt
```

新增测试：

```text
tests/test_main_api.py
tests/test_text_splitter.py
tests/test_vector_store.py
```

---

## 3. 接口变化

接口路径和请求响应字段不变。

`POST /documents/search`：

```text
修复成功检索后返回结果时的 NameError 风险。
```

`POST /rag/ask`：

```text
响应结构不变，但 reply 会被 prompt 约束为三段式 Markdown。
```

期望格式：

```text
答案：
...

依据：
- [Source 1] ...

资料不足之处：
...
```

---

## 4. 顺带修复和优化

`app/text_splitter.py`：

```text
_find_reasonable_boundary() 在 min_boundary >= end 时直接返回 end。
```

`app/vector_store.py`：

```text
Qdrant collection 向量维度不匹配时，错误信息会提示重建本地索引。
```

这样后续切换 embedding 模型或重建索引时更容易恢复。

---

## 5. 验证结果

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
compileall 通过
pytest 5 passed
```

本次没有自动调用真实 DeepSeek API，避免消耗 token。

---

## 6. 遇到的问题

一开始发现当前环境没有安装 pytest：

```text
No module named pytest
```

已处理：

```text
requirements.txt 增加 pytest>=8.0,<9
项目 .venv 安装 pytest
```

---

## 7. 后续影响

这一步让后续第 14、15 步更稳：

```text
/documents/search 可以作为评估入口
RAG reply 有稳定格式，方便人工和 UI 检查
pytest 骨架已经建立，后续每一步可以继续补测试
```

---

## 8. 下一步建议

下一步进入：

```text
第 14 步：建立 RAG 评估问题集
```

对应 goal：

```text
docs/goal/14-rag-evaluation-dataset-goal.md
```

