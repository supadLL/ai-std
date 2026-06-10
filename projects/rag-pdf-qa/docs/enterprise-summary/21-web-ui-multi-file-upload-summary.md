# 企业级第 21 步完成总结：Web UI 多文件批量导入

## 1. 本次完成了什么

本次在不新增后端批量上传接口的前提下，增强 Web UI 文件导入体验：

```text
1. 文件选择器支持 multiple 多文件选择。
2. 多文件选择后显示数量和文件名摘要。
3. 上传时按顺序逐个创建 index job。
4. 单个文件失败不会中断后续文件提交。
5. 成功创建的任务立即进入 Index jobs 列表并启动轮询。
6. 静态资源版本提升到 v49，避免浏览器继续加载旧 JS/CSS。
```

## 2. 改动文件

| 文件 | 说明 |
|---|---|
| `web/index.html` | 文件输入增加 `multiple`，静态资源版本更新到 `v49` |
| `web/app.js` | 增加批量上传循环、文件名摘要、占位符格式化和批量结果提示 |
| `tests/test_main_api.py` | 更新静态资源版本断言，并检查文件输入支持 `multiple` |
| `docs/enterprise-goal/21-web-ui-multi-file-upload-goal.md` | 新增企业级第 21 步 goal |
| `docs/enterprise-summary/21-web-ui-multi-file-upload-summary.md` | 新增本总结 |
| `docs/00-llm-start-here.md` | 新增后续 LLM 接手指南 |

## 3. 接口变化

本次没有新增后端接口。

前端继续调用：

```text
POST /documents/index-jobs
POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs
```

每个文件单独构造一次 `FormData`，保持当前 `chunk_size`、`overlap`、`reindex` 参数。

## 4. 验证结果

已执行：

```powershell
node --check web/app.js
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests/test_main_api.py tests/test_auth.py
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
node --check web/app.js 通过
compileall app 通过
tests/test_main_api.py tests/test_auth.py：39 passed
全量 pytest：113 passed
```

## 5. 遇到的问题

本次接手时先误把 goal 写到了普通主线的 `docs/goal/`。

后续已按 `enterprise-rag-platform` 分支规范修正为：

```text
docs/enterprise-goal/21-web-ui-multi-file-upload-goal.md
docs/enterprise-summary/21-web-ui-multi-file-upload-summary.md
```

同时新增 `docs/00-llm-start-here.md`，明确后续新 LLM 必须先确认分支，再决定 goal 和 summary 目录。

## 6. 后续影响

团队初始化知识库时，可以一次选择多个文件，由前端顺序创建多个异步索引任务。

这种方式复用现有 index job API，不改变后端任务模型，也避免一次性并发提交多个大文件。

## 7. 下一步建议

下一步可以继续做：

```text
1. Web UI 批量上传进度更细粒度展示。
2. 多文件上传前的格式和大小预检查。
3. Index jobs 支持按批次分组展示。
```
