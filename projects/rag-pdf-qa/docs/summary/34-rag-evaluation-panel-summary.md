# 第 34 步完成总结：RAG 评估脚本与评估面板

## 1. 本次完成了什么

本次把已有的 RAG 评估问题集升级成可运行、可复测、可展示的检索质量评估能力。

新增能力：

```text
1. 本地 RAG 检索评估模块
2. 独立评估脚本 scripts/run_rag_evaluation.py
3. 评估结果 JSON / Markdown 输出
4. FastAPI 评估接口
5. Web UI 检索评估页签
6. pytest 回归测试
```

本次评估默认只调用本地 embedding 和本地 Qdrant，不调用 DeepSeek，不消耗 LLM token。

---

## 2. 改动文件

核心代码：

```text
app/evaluation.py
app/main.py
scripts/run_rag_evaluation.py
```

前端：

```text
web/index.html
web/app.js
web/styles.css
```

测试：

```text
tests/test_main_api.py
tests/test_rag_evaluation.py
```

数据输出：

```text
data/eval/latest_rag_evaluation.json
data/eval/latest_rag_evaluation.md
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
docs/summary/34-rag-evaluation-panel-summary.md
```

---

## 3. 接口变化

新增接口：

```text
GET /evaluation/questions
POST /evaluation/run
GET /evaluation/latest
```

接口说明：

| 接口 | 作用 | 是否调用 DeepSeek |
|---|---|---|
| `GET /evaluation/questions` | 读取当前评估问题集 | 否 |
| `POST /evaluation/run` | 运行本地检索评估并保存结果 | 否 |
| `GET /evaluation/latest` | 读取最近一次评估结果 | 否 |

`POST /evaluation/run` 支持参数：

```json
{
  "limit": 5,
  "score_threshold": null
}
```

---

## 4. 评估逻辑

评估输入来自：

```text
data/eval/rag_eval_cases.json
```

每个 case 会执行：

```text
question
-> embed_text
-> search_chunks
-> 根据 expected_pages / expected_keywords 判断命中
-> 记录 top_pages / top_scores / top_sources
```

当前统计指标：

```text
case_count
scored_case_count
hit_count
hit_rate
page_hit_rate
keyword_hit_rate
low_score_result_count
```

---

## 5. Web UI 变化

Web UI 左侧新增：

```text
检索评估 / Evaluation
```

页面能力：

```text
1. 设置 top_k
2. 设置 score_threshold
3. 运行评估
4. 读取最近一次评估结果
5. 展示 hit_rate / page_hit / keyword_hit / low_score
6. 展示每个 case 的命中状态、top pages、scores、matched keywords 和 sources
```

小屏下 tab 改为两列布局，避免四个页签挤压。

---

## 6. 验证结果

编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
```

结果：

```text
通过
```

pytest：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
39 passed
```

脚本验证：

```powershell
.\.venv\Scripts\python.exe scripts\run_rag_evaluation.py
```

本地当前结果：

```text
hit_rate=0.9286
page_hit_rate=0.7143
keyword_hit_rate=0.9286
```

---

## 7. 当前限制

当前评估仍是检索评估，不是完整回答质量评估。

还没有做：

```text
LLM-as-a-judge
多模型横评
答案忠实度评分
自动生成评估问题
前端评估历史记录列表
```

这些可以作为后续增强，但不建议马上引入复杂评估框架。

---

## 8. 下一步

下一步建议进入：

```text
第 35 步：Agent 工具路由增强
```

重点方向：

```text
1. 让 /agent/ask 返回 route_reason
2. 区分 chat / rag / evaluation / management 类问题
3. 让 Web UI 支持 Agent 模式入口
4. 保持 RAG 检索链路可解释
```
