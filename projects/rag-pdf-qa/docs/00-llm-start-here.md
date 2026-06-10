# 新对话 / 新 LLM 接手指南

这份文档给后续新开的 AI 对话或其他 LLM 使用，目标是避免一上来就改错目录、跳过 goal、漏写 summary，或者把普通主线和企业级分支混在一起。

## 1. 第一步：先确认分支

进入项目目录后先执行：

```powershell
cd D:\ll-work\ai-play\ai-std\projects\rag-pdf-qa
git branch --show-current
git status --short
```

然后按分支判断文档位置：

| 当前分支 | goal 位置 | summary 位置 | 说明 |
|---|---|---|---|
| `main` 或普通学习主线 | `docs/goal/` | `docs/summary/` | 本地个人 RAG Agent 学习主线 |
| `enterprise-rag-platform` | `docs/enterprise-goal/` | `docs/enterprise-summary/` | 企业级 RAG 平台改造主线 |

不要在 `enterprise-rag-platform` 分支把新 goal 写到 `docs/goal/`。

## 2. 第二步：读取入口文档

每次接手都先读：

```text
README.md
docs/00-project-continuation-guide.md
docs/00-llm-start-here.md
```

如果当前分支是 `enterprise-rag-platform`，继续读：

```text
docs/enterprise-goal/README.md
docs/enterprise-goal/00-enterprise-roadmap.md
docs/enterprise-goal/当前要执行的 NN-*-goal.md
```

如果当前分支是普通学习主线，继续读：

```text
docs/goal/README.md
docs/goal/当前要执行的 NN-*-goal.md
docs/summary/README.md
```

## 3. 第三步：开始前必须说明当前状态

修改代码前，先用一小段话说明：

```text
当前分支是什么
当前应使用哪个 goal/summary 目录
当前已经完成到哪一步
本次准备执行哪个 goal
```

如果发现用户指定的文档目录和当前分支不一致，先纠正文档位置，再继续。

## 4. 固定执行顺序

重要功能必须按下面顺序执行：

```text
1. 读项目文档和当前 goal
2. 如果没有 goal，先创建 goal
3. 写代码
4. 跑测试
5. 写 summary
6. 同步 README 和 docs/00-project-continuation-guide.md
7. git status 检查
8. git commit
```

不要采用“先写代码，最后再想文档放哪”的方式。

## 5. 企业级分支当前规则

在 `enterprise-rag-platform` 分支：

```text
goal 放 docs/enterprise-goal/
summary 放 docs/enterprise-summary/
每一步编号沿用企业级编号
每一步都要考虑登录鉴权、知识库权限、审计、数据隔离和本地开发体验
```

当前企业级分支已经完成到第 21 步：

```text
21-web-ui-multi-file-upload-goal.md
21-web-ui-multi-file-upload-summary.md
```

后续新增企业级能力从第 22 步继续编号。

## 6. 常用验证命令

代码修改后至少执行：

```powershell
node --check web/app.js
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests/test_main_api.py tests/test_auth.py
.\.venv\Scripts\python.exe -m pytest
```

如果改了 Web UI，确认：

```text
GET /app
GET /web/app.js
GET /web/styles.css
```

如果改了 API，确认：

```text
GET /health
GET /openapi.json
GET /docs
```

## 7. 提交前检查清单

提交前确认：

```text
文档目录和当前分支匹配
goal 已存在且编号正确
summary 已记录实际改动和测试结果
README 已加入新 summary 链接
docs/00-project-continuation-guide.md 已同步当前能力
没有真实 API Key、token、数据库文件或 .env 内容进入提交
测试结果已通过
```

最后再提交：

```powershell
git status --short
git add ...
git commit -m "..."
```
