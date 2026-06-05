# 第 39 步执行目标：中文模式技术标签可读性优化

## 1. 背景

当前 Web UI 在中文模式下仍然有一些纯英文技术标签：

```text
chunk
overlap
reindex
top_k
threshold
API Base URL
LLM Model
RAG System Prompt
```

这些术语对开发者有用，但对中文用户不够直观。

## 2. 本次目标

本次完成：

```text
1. 中文模式下展示“中文含义 + 英文术语”
2. 英文模式保持原有英文表达
3. 文件导入页补充 chunk / overlap / reindex 中文含义
4. 知识问答页补充 top_k / threshold / document 中文含义
5. 检索评估页补充 top_k / threshold 中文含义
6. 设置页补充 Provider / API Base URL / LLM Model / API Key / Timeout / RAG Prompt 中文含义
7. 更新测试和文档索引
```

## 3. 不做什么

本次不做：

```text
UI 结构重排
RAG 参数逻辑调整
新增帮助弹窗
新增 tooltip 系统
后端接口变化
```

## 4. 需要修改的文件

预计修改：

```text
web/index.html
web/app.js
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

完成后新增：

```text
docs/summary/39-zh-technical-labels-summary.md
```

## 5. 验收标准

完成后应满足：

```text
1. 中文模式下 chunk 显示为“分块大小 chunk”
2. 中文模式下 overlap 显示为“重叠长度 overlap”
3. 中文模式下 reindex 显示为“重新索引 reindex”
4. 中文模式下 top_k 显示为“检索数量 top_k”
5. 中文模式下 threshold 显示为“分数阈值 threshold”
6. 设置页模型相关标签有中文含义
7. 英文模式仍然显示英文
8. pytest 通过
```

## 6. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
node --check web\app.js
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
选择中文
检查文件导入 / 知识问答 / 检索评估 / 设置页标签
切换 English
确认英文模式仍正常
```

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/39-zh-technical-labels-summary.md
```
