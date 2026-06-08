# 第 08 步执行目标：项目演示、README 和简历呈现收口

## 1. 背景

完成核心能力后，需要把项目整理成能被别人快速理解和演示的形态。

这一步不重点写新业务功能，而是做项目表达收口。

## 2. 本次目标

完善：

```text
README 项目速览
项目架构图
Agent 路由流程图
核心能力表
核心接口表
演示脚本
演示检查清单
简历描述模板
面试讲解要点
```

## 3. 不做什么

本次不做：

```text
新增大功能
重构 Agent 架构
更换技术栈
复杂部署
```

## 4. 预计改动文件

```text
README.md
docs/summary/project-demo-script.md
docs/summary/project-demo-checklist.md
docs/summary/08-demo-and-resume-polish-summary.md
docs/assets/
```

## 5. 简历表达方向

可以突出：

```text
业务工具调用
可解释 Agent 路由
RAG + tool 混合决策
多轮会话状态
工单和人工转接
客服质检评估
Web UI 演示
```

## 6. 验收标准

```text
README 能让新用户理解项目做什么
README 有启动方式和接口入口
演示脚本能覆盖主流程
简历描述准确不过度包装
项目限制写清楚
pytest 仍然通过
```

## 7. 测试方式

```powershell
python -m compileall app tests scripts
python -m pytest
```

手动按演示脚本走一遍：

```text
启动服务
打开 Web UI
演示订单查询
演示退款判断
演示政策 RAG
演示人工转接和工单
演示评估面板
```

