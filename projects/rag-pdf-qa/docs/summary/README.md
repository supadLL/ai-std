# summary 总结文档规范

这个目录用于存放：

> 每个阶段完成之后的总结、实际改动、验证结果和后续影响。

它和 `docs/goal/` 对应：

```text
goal：开工前写，说明要做什么
summary：完成后写，说明实际做了什么
```

---

## 1. 为什么需要 summary 文档

学习型项目不能只留下代码。

还要留下：

```text
做了什么
为什么这样做
改了哪些文件
怎么验证
遇到了什么问题
下一步是什么
```

这样后续新对话或新开发者才能接上。

---

## 2. 命名规范

建议：

```text
docs/summary/11-12-score-threshold-sources-summary.md
docs/summary/13-rag-output-format-summary.md
docs/summary/13-rag-output-format-step.md
docs/summary/14-rag-evaluation-dataset-summary.md
docs/summary/15-chunk-topk-parameter-evaluation-summary.md
docs/summary/16-document-management-summary.md
docs/summary/17-document-dedup-content-hash-summary.md
docs/summary/18-markdown-txt-loader-summary.md
docs/summary/19-docx-table-loader-summary.md
docs/summary/20-modern-web-ui-summary.md
docs/summary/21-rag-agent-tool-routing-summary.md
docs/summary/22-tests-and-project-final-summary.md
docs/summary/project-demo-checklist.md
docs/summary/23-ui-answer-quality-refinement-summary.md
docs/summary/24-ui-tabs-runtime-settings-summary.md
docs/summary/25-ui-tab-layout-fix-summary.md
docs/summary/26-ui-markdown-answer-rendering-summary.md
docs/summary/27-ui-language-theme-preferences-summary.md
docs/summary/28-ui-background-color-preference-summary.md
docs/summary/29-web-title-favicon-summary.md
docs/summary/30-ui-background-surface-color-summary.md
docs/summary/31-one-click-start-and-docker-summary.md
docs/summary/32-scanned-pdf-ocr-summary.md
docs/summary/33-multiformat-image-ocr-loader-summary.md
docs/summary/34-rag-evaluation-panel-summary.md
docs/summary/35-agent-routing-enhancement-summary.md
docs/summary/36-knowledge-base-management-enhancement-summary.md
```

格式：

```text
编号-主题-summary.md
```

如果一次完成多个强相关步骤，可以合并成一个 summary。

从第 14 步开始，完成后只保留一个 summary 文档。

```text
goal：开工前目标
summary：完成后记录
```

不再额外创建 `*-step.md`，避免同一步出现两份完成说明。

---

## 3. summary 文档模板

建议包含：

```markdown
# 第 N 步完成总结：标题

## 1. 本次完成了什么

概括实际完成内容。

## 2. 改动文件

列出代码、docs、README 等。

## 3. 接口变化

列出请求/响应变化。

## 4. 验证结果

列出测试命令、接口结果、关键输出。

## 5. 遇到的问题

记录 bug、编码问题、服务重启问题等。

## 6. 后续影响

说明这一步对下一步有什么帮助。

## 7. 下一步建议

明确下一步应该做什么。
```

---

## 4. 执行要求

每次完成一个重要阶段后，都要创建或更新 summary。

如果只改了很小的 typo，可以不单独写 summary。

但涉及接口、数据结构、RAG 链路、文档结构、测试结果的改动，都必须写 summary。

