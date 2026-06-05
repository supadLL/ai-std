# 企业级第 07 步执行目标：企业级评估和质量治理

## 1. 背景

当前项目已经有本地检索评估，但企业场景还需要：

```text
评估历史
按知识库评估
回答质量评估
用户反馈
低质量问题追踪
Prompt 和模型变更对比
```

## 2. 本次目标

本次升级评估能力：

```text
1. evaluation_runs 入库
2. evaluation_cases 支持知识库归属
3. Web UI 展示评估历史
4. 支持对比不同 top_k / score_threshold / model
5. 新增用户反馈 thumbs up/down
6. 预留 LLM-as-a-judge 回答质量评估
```

## 3. 不做什么

本次不做：

```text
自动化复杂 benchmark 平台
多模型成本排行榜
完整人工标注系统
大规模 A/B 实验
```

## 4. 预计修改文件

```text
app/evaluation.py
app/main.py
app/models.py
web/index.html
web/app.js
tests/test_rag_evaluation.py
tests/test_main_api.py
```

## 5. 接口建议

```text
GET /evaluation/runs
GET /evaluation/runs/{run_id}
POST /evaluation/run
POST /feedback/answers
```

## 6. 验收标准

```text
1. 每次评估保存为独立 run
2. Web UI 可以查看历史评估
3. 可按知识库查看评估结果
4. 用户可以对回答反馈好/坏
5. pytest 通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rag_evaluation.py tests\test_main_api.py
```
