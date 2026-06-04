# 第 23 步执行目标：名称、问答交互和回答质量优化

这一步的目标是：

> 把项目从“PDF 问答”命名和单次结果展示，优化为更贴近多格式知识库 RAG Agent 的网页交互体验。

---

## 1. 背景

当前项目已经支持：

```text
PDF / Markdown / txt / docx / csv / xlsx 入库
RAG 问答
最小 Agent 工具路由
Web UI 初版
```

但仍存在几个体验问题：

```text
1. 项目显示名称仍是 RAG PDF QA，不符合多格式知识库现状
2. Web UI 输入框 Enter 是换行，不符合聊天页面习惯
3. RAG prompt 对详细操作型问题回答偏短
4. 问答生成时页面反馈偏弱，不像聊天页面
```

---

## 2. 本次目标

完成以下优化：

```text
1. 将项目显示名称从 RAG PDF QA 调整为 Local Knowledge RAG Agent
2. Web UI 支持 Enter 发送
3. Web UI 支持 Ctrl+Enter 换行
4. RAG prompt 要求输出更详尽、分步骤、可执行的答案
5. Web UI 改成聊天式消息展示
6. 生成中展示用户消息和 AI 正在解析资料的反馈
```

---

## 3. 不做什么

本次不做：

- 流式 token 输出
- 多轮记忆
- 大型前端工程化
- 新增复杂 Agent 能力
- 云端部署

---

## 4. 预计修改文件

可能修改：

```text
app/main.py
web/index.html
web/styles.css
web/app.js
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
```

完成后新增：

```text
docs/summary/23-ui-answer-quality-refinement-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. /app 页面显示 Local Knowledge RAG Agent
2. FastAPI OpenAPI title 使用新名称
3. Enter 可以直接发送问题
4. Ctrl+Enter 可以插入换行
5. 生成中有聊天式反馈
6. RAG prompt 明确要求详细步骤和可执行说明
7. pytest 通过
8. 8000 服务重启后能访问新 UI
```
