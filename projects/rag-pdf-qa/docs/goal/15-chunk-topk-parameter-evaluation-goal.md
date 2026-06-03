# 第 15 步执行目标：评估 chunk 参数和 top_k

这一步的目标是：

> 用第 14 步的问题集，系统比较 chunk_size、overlap、top_k 对检索质量的影响。

---

## 1. 背景

当前 chunk 参数主要依赖经验值：

```text
chunk_size = 800
overlap = 100
top_k / limit = 5
```

但不同文档类型适合的参数不一样。

如果 chunk 太小：

```text
上下文容易断裂
```

如果 chunk 太大：

```text
检索粒度变粗，噪声变多
```

所以这一步要把参数从“感觉不错”变成“有测试依据”。

---

## 2. 本次目标

对比至少 3 组 chunk 参数：

```text
500 / 80
800 / 100
1000 / 150
```

并对比至少 2 组 top_k：

```text
top_k = 3
top_k = 5
```

记录：

```text
检索命中率
低分噪声情况
回答是否稳定
推荐默认参数
```

---

## 3. 不做什么

本次不做：

- 换 embedding 模型
- 引入 rerank
- 引入 hybrid search
- 做 UI
- 做 Agent
- 一次支持多格式文档

---

## 4. 预计修改文件

可能修改：

```text
app/config.py
app/main.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/15-chunk-topk-parameter-evaluation-step.md
docs/summary/15-chunk-topk-parameter-evaluation-summary.md
```

可选新增：

```text
data/eval/chunk_topk_eval_result.md
```

---

## 5. 接口变化

已有接口已经支持关键参数：

```text
POST /documents/index
  chunk_size
  overlap

POST /documents/search
  limit

POST /rag/ask
  limit
  score_threshold
```

本次原则上不新增接口。

如果发现参数默认值需要调整，应在 docs 中说明原因。

---

## 6. 验收标准

完成后应满足：

```text
1. 至少比较 3 组 chunk_size / overlap
2. 至少比较 top_k = 3 和 top_k = 5
3. 每组参数都跑同一套评估问题
4. 有命中率或命中数量记录
5. 给出推荐默认参数
6. 说明推荐参数的取舍
```

---

## 7. 测试方式

建议流程：

```text
1. 清理或重建 Qdrant collection
2. 用参数 A 重新索引同一份 PDF
3. 跑第 14 步评估问题
4. 记录 /documents/search 结果
5. 重复参数 B、C
6. 抽样调用 /rag/ask 看回答质量
```

注意：

```text
同一轮对比必须使用同一份 PDF、同一套问题、同一个 embedding 模型。
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/15-chunk-topk-parameter-evaluation-summary.md
```

并更新：

```text
docs/summary/10-rag-test-result.md
README.md
docs/00-project-continuation-guide.md
```

