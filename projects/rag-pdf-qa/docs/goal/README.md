# goal 执行文档规范

这个目录用于存放：

> 每个阶段开始写代码之前，需要先明确的执行目标、范围、验收标准和测试方式。

也就是说：

```text
先写 goal
再写代码
最后写 summary
```

---

## 1. 为什么需要 goal 文档

之前的节奏更偏向：

```text
写代码
-> 补 docs
-> 总结本次做了什么
```

这样的问题是：

```text
开工前目标不够清楚
容易边写边偏
新对话不知道下一步为什么这样做
完成后很难判断是否真的完成
```

所以后续每个重要步骤都要先创建 goal 文档。

---

## 2. 命名规范

建议：

```text
docs/goal/13-rag-output-format-goal.md
docs/goal/14-rag-evaluation-dataset-goal.md
docs/goal/15-chunk-topk-parameter-evaluation-goal.md
```

格式：

```text
编号-主题-goal.md
```

编号要尽量和主 docs 步骤保持一致。

---

## 3. goal 文档模板

建议包含：

```markdown
# 第 N 步执行目标：标题

## 1. 背景

为什么现在要做这一步。

## 2. 本次目标

这一步具体要完成什么。

## 3. 不做什么

明确排除范围，避免跑偏。

## 4. 需要修改的文件

预计涉及哪些代码和文档。

## 5. 接口变化

如果有接口变化，写清楚请求和响应。

## 6. 验收标准

完成后如何判断真的完成。

## 7. 测试方式

需要跑哪些命令、哪些接口。

## 8. 完成后的 summary 文档

完成后应该写到哪个 summary 文件。
```

---

## 4. 执行要求

后续进入新阶段前，先创建对应 goal 文档。

如果新对话接手项目，应先读：

```text
docs/goal/README.md
docs/goal/当前要执行的 goal 文件
docs/00-project-continuation-guide.md
```

再开始改代码。

---

## 5. 当前后续执行路线

后续建议按下面顺序一步一步实现。

当前状态：

```text
rag-pdf-qa 主线已完成到第 27 步。
```

后续如果继续扩展，先创建新的 goal 文档，再写代码。

当前已创建的 goal 文件：

| 步骤 | goal 文档 | 目标 |
|---:|---|---|
| 13 | [13-rag-output-format-goal.md](13-rag-output-format-goal.md) | 固定 RAG 输出格式 |
| 14 | [14-rag-evaluation-dataset-goal.md](14-rag-evaluation-dataset-goal.md) | 建立 RAG 评估问题集 |
| 15 | [15-chunk-topk-parameter-evaluation-goal.md](15-chunk-topk-parameter-evaluation-goal.md) | 评估 chunk 参数和 top_k |
| 16 | [16-document-management-goal.md](16-document-management-goal.md) | 新增知识库文档管理能力 |
| 17 | [17-document-dedup-content-hash-goal.md](17-document-dedup-content-hash-goal.md) | 增加 content_hash 去重与重建索引策略 |
| 18 | [18-markdown-txt-loader-goal.md](18-markdown-txt-loader-goal.md) | 支持 Markdown 和 txt 文档入库 |
| 19 | [19-docx-table-loader-goal.md](19-docx-table-loader-goal.md) | 支持 docx 与表格类文档的最小解析 |
| 20 | [20-modern-web-ui-goal.md](20-modern-web-ui-goal.md) | 实现现代风 RAG Web UI |
| 21 | [21-rag-agent-tool-routing-goal.md](21-rag-agent-tool-routing-goal.md) | 实现最小 RAG Agent 工具路由 |
| 22 | [22-tests-and-project-final-summary-goal.md](22-tests-and-project-final-summary-goal.md) | 项目测试、收口和最终总结 |
| 23 | [23-ui-answer-quality-refinement-goal.md](23-ui-answer-quality-refinement-goal.md) | 名称、问答交互和回答质量优化 |
| 24 | [24-ui-tabs-runtime-settings-goal.md](24-ui-tabs-runtime-settings-goal.md) | UI 分页与运行时模型设置 |
| 25 | [25-ui-tab-layout-fix-goal.md](25-ui-tab-layout-fix-goal.md) | 修复 UI Tab 布局混排 |
| 26 | [26-ui-markdown-answer-rendering-goal.md](26-ui-markdown-answer-rendering-goal.md) | 优化回答 Markdown 展示 |
| 27 | [27-ui-language-theme-preferences-goal.md](27-ui-language-theme-preferences-goal.md) | UI 语言和系统色偏好 |

执行时不要跳过当前步骤直接做后面的功能。

如果中途发现某一步范围太大，可以拆成子步骤，例如：

```text
16-a-document-list-goal.md
16-b-document-delete-goal.md
```

但拆分后也要同步更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
```

