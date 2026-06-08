# 第 07 步执行目标：客服评估、质检和回归测试集

## 1. 背景

客服 Agent 的质量不能只靠“看起来回答不错”。

需要评估：

```text
是否命中正确知识
是否调用正确工具
是否错误承诺退款
是否在该转人工时转人工
是否追问必要信息
```

## 2. 本次目标

新增评估数据集：

```text
FAQ 问答类
订单查询类
物流查询类
退款判断类
投诉转人工类
资料不足追问类
```

新增能力：

```text
本地评估脚本
评估结果 JSON / Markdown 输出
Web UI 评估面板
pytest 回归测试
```

新增接口：

```text
GET /evaluation/questions
POST /evaluation/run
GET /evaluation/latest
```

## 3. 不做什么

本次不做：

```text
复杂 LLM-as-a-judge
在线 A/B 测试
真实用户反馈闭环
客服绩效系统
```

## 4. 预计改动文件

```text
app/evaluation.py
app/main.py
data/eval/customer_service_eval_cases.json
scripts/run_customer_service_evaluation.py
tests/test_evaluation.py
web/app.js
web/index.html
web/styles.css
docs/summary/07-evaluation-and-quality-governance-summary.md
```

## 5. 指标建议

```text
route_accuracy
tool_accuracy
source_hit_rate
handoff_accuracy
missing_info_followup_rate
unsafe_commitment_count
```

## 6. 验收标准

```text
至少 20 条评估 case
评估脚本能输出 JSON 和 Markdown
能统计 route / tool / handoff 准确率
错误退款承诺能被标记
Web UI 能展示最近评估结果
```

## 7. 测试方式

```powershell
python -m compileall app tests scripts
python -m pytest
python scripts/run_customer_service_evaluation.py
```

