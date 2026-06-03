# 第 17 步执行目标：增加 content_hash 去重与重建索引策略

这一步的目标是：

> 避免同一个文件反复上传后在 Qdrant 中产生重复 chunks。

---

## 1. 背景

当前如果多次上传同一份 PDF，可能会重复写入相同内容。

这会导致：

```text
检索结果重复
sources 展示混乱
Qdrant 数据膨胀
评估结果不稳定
```

所以需要用文件内容 hash 建立去重策略。

---

## 2. 本次目标

为索引流程增加：

```text
content_hash
duplicate check
reindex mode
```

建议策略：

```text
同一个 content_hash 已存在时，默认不重复索引
用户明确 reindex=true 时，先删除旧 chunks，再重新索引
```

metadata 至少增加：

```text
content_hash
indexed_at
source_file_size
```

---

## 3. 不做什么

本次不做：

- 文件内容差异对比
- 多版本管理
- 云端文件存储
- 权限隔离
- 大规模数据库设计
- UI

---

## 4. 预计修改文件

可能修改：

```text
app/main.py
app/document_store.py
app/vector_store.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/17-document-dedup-content-hash-step.md
docs/summary/17-document-dedup-content-hash-summary.md
```

---

## 5. 接口变化

建议 `/documents/index` 增加可选参数：

```text
reindex: bool = false
```

建议响应包含：

```text
document_id
content_hash
is_duplicate
indexed
message
```

---

## 6. 验收标准

完成后应满足：

```text
1. 同一份文件重复上传时，不重复写入 chunks
2. 返回结果能说明这是重复文件
3. reindex=true 时能删除旧 chunks 并重新索引
4. metadata 中记录 content_hash
5. /documents 列表能展示 content_hash 或 hash 前缀
6. 检索结果不再出现同一文件的重复来源
```

---

## 7. 测试方式

建议测试：

```text
1. 第一次 POST /documents/index
2. 第二次上传同一文件
3. 检查返回 is_duplicate
4. GET /documents 确认只有一条文档记录
5. POST /documents/search 确认 sources 不重复膨胀
6. reindex=true 再上传一次
7. 确认旧 chunks 被替换
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/17-document-dedup-content-hash-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/10-rag-test-result.md
```

