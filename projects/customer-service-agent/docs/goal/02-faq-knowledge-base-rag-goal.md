# 第 02 步执行目标：FAQ / 政策知识库 RAG

## 1. 背景

客服 Agent 不能只靠模型常识回答售后政策。

本步建立最小客服知识库：

```text
FAQ
退款政策
发票规则
物流时效
会员权益
人工转接规则
```

## 2. 本次目标

新增能力：

```text
加载本地 FAQ / policy 文档
文本切分
embedding
Qdrant local 索引
语义检索
基于 sources 生成客服回复
```

新增接口：

```text
POST /knowledge/index
POST /knowledge/search
POST /rag/ask
```

## 3. 不做什么

本次不做：

```text
复杂文档格式解析
扫描件 OCR
多租户知识库
网页抓取
LLM-as-a-judge
```

先使用 Markdown / JSON 样例知识库。

## 4. 预计改动文件

```text
app/embedding_client.py
app/text_splitter.py
app/vector_store.py
app/knowledge_loader.py
app/main.py
data/knowledge/faq.md
data/knowledge/policies.md
tests/test_knowledge_loader.py
tests/test_vector_store.py
tests/test_main_api.py
docs/summary/02-faq-knowledge-base-rag-summary.md
```

## 5. RAG 回复要求

回复应包含：

```text
直接答复
依据
还需要用户补充的信息
```

如果资料不足，不能编造政策。

## 6. 验收标准

```text
可以索引本地 FAQ / policy 样例
/knowledge/search 返回 sources
/rag/ask 能基于 sources 回答
低相关度时返回资料不足
pytest 覆盖切分、检索和资料不足场景
```

## 7. 测试方式

```powershell
python -m compileall app tests
python -m pytest
```

手动验证：

```text
问题：七天无理由退款需要满足什么条件？
期望：命中退款政策，并说明条件和例外。
```

