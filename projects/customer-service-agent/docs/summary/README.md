# summary 总结文档规范

这个目录用于存放 `customer-service-agent` 每个阶段完成后的总结。

它和 `docs/goal/` 对应：

```text
goal：开工前写，说明要做什么
summary：完成后写，说明实际做了什么
```

## 命名规范

```text
NN-topic-summary.md
```

例如：

```text
01-project-bootstrap-and-chat-summary.md
02-faq-knowledge-base-rag-summary.md
```

## summary 模板

建议每份 summary 包含：

```markdown
# 第 N 步完成总结：标题

## 1. 本次完成了什么

## 2. 改动文件

## 3. 接口或数据结构变化

## 4. 验证结果

## 5. 遇到的问题

## 6. 后续影响

## 7. 下一步建议
```

## 执行要求

涉及下面内容时必须写 summary：

```text
新增接口
新增工具
新增 RAG 能力
新增会话或工单数据结构
新增 Web UI 能力
新增评估指标
修改项目阶段判断
```

很小的 typo 或纯格式调整可以不单独写 summary。

