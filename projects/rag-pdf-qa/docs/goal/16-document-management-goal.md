# 第 16 步执行目标：新增知识库文档管理能力

这一步的目标是：

> 从“上传后只能检索”升级为“能查看、删除、重建本地知识库文档”。

状态：已完成。

完成记录：

```text
docs/summary/16-document-management-summary.md
app/document_store.py
```

---

## 1. 背景

当前项目已经能把 PDF 写入 Qdrant。

但还缺少基础文档管理：

```text
不知道当前索引了哪些文件
不能按 document_id 删除文档
不能查看文档的 chunk 数量
不能清晰地区分多个文件
```

这会影响后续 UI 和多格式文档扩展。

---

## 2. 本次目标

新增最小文档管理能力：

```text
GET /documents
GET /documents/{document_id}
DELETE /documents/{document_id}
```

每个文档至少记录：

```text
document_id
filename
file_type
chunk_count
created_at
collection
chunk_size
overlap
embedding_model
```

实现上优先保持简单。

可以先使用本地 JSON metadata 文件，不急着引入数据库。

---

## 3. 不做什么

本次不做：

- 多用户权限
- 登录系统
- 云端存储
- 文件原文长期保存
- 复杂数据库迁移
- UI 页面
- Agent

---

## 4. 预计修改文件

可能新增：

```text
app/document_store.py
data/documents.json
```

可能修改：

```text
app/main.py
app/vector_store.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/16-document-management-summary.md
```

---

## 5. 接口变化

建议新增：

```text
GET /documents
GET /documents/{document_id}
DELETE /documents/{document_id}
```

建议 `/documents/index` 返回新增字段：

```text
document_id
chunk_count
collection
```

---

## 6. 验收标准

完成后应满足：

```text
1. 上传并索引 PDF 后，可以在 GET /documents 看到记录
2. GET /documents/{document_id} 能查看单个文档详情
3. DELETE /documents/{document_id} 能删除该文档在 Qdrant 中的 chunks
4. 删除不存在的 document_id 有清晰错误
5. Swagger Docs 页面能测试新增接口
6. /documents/search 和 /rag/ask 不被破坏
```

---

## 7. 测试方式

建议测试顺序：

```text
1. POST /documents/index
2. GET /documents
3. GET /documents/{document_id}
4. POST /documents/search
5. DELETE /documents/{document_id}
6. GET /documents/{document_id}
7. POST /documents/search
```

删除后应确认：

```text
该 document_id 对应的 chunks 不再参与检索。
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/16-document-management-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
docs/summary/08-rag-agent-advanced-roadmap.md
```
