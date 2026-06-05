# 第 36 步执行目标：知识库管理能力增强

这一步的目标是：

> 把当前“能上传、能列表、能删除”的知识库管理，升级为更适合长期使用的本地知识库管理界面。

---

## 1. 背景

当前已经支持：

```text
文档上传入库
文档列表
文档详情
删除文档
content_hash 去重
reindex=true 重建索引
```

但如果长期使用，还会需要：

```text
按文档筛选检索
批量删除
重新索引
查看 chunk 数量和入库时间
按文档状态排查问题
```

---

## 2. 本次目标

本次完成：

```text
1. Web UI 增加更清晰的知识库管理区
2. 支持按文件名 / 文件类型筛选文档列表
3. 支持单文档重新索引
4. 支持批量删除
5. 文档详情展示 chunk_count、content_hash、created_at、file_type
6. 检索时可选限定某个 document_id
```

---

## 3. 不做什么

本次不做：

- 多用户知识库
- 权限系统
- 远程对象存储
- 文档版本树
- 全文倒排索引
- 大规模分页优化

---

## 4. 需要修改的文件

预计修改：

```text
app/main.py
app/document_store.py
app/vector_store.py
web/index.html
web/app.js
web/styles.css
README.md
docs/00-project-continuation-guide.md
```

测试：

```text
tests/test_document_store.py
tests/test_main_api.py
tests/test_vector_store.py
```

完成后新增：

```text
docs/summary/36-knowledge-base-management-enhancement-summary.md
```

---

## 5. 接口变化

可能新增或扩展：

```text
POST /documents/{document_id}/reindex
DELETE /documents/batch
POST /documents/search
```

`POST /documents/search` 可增加：

```text
document_id: string | null
file_type: string | null
```

---

## 6. 验收标准

完成后应满足：

```text
1. Web UI 能筛选文档列表
2. Web UI 能批量删除文档
3. 单文档可以重新索引
4. 检索可以限定 document_id
5. 删除或重建后 Qdrant 和 metadata 保持一致
6. pytest 通过
```

---

## 7. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

接口测试：

```text
GET /documents
POST /documents/search
POST /documents/{document_id}/reindex
DELETE /documents/batch
```

页面验证：

```text
打开 http://127.0.0.1:8000/app
进入文件导入 / 知识库管理
执行筛选、批量删除、重新索引
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/36-knowledge-base-management-enhancement-summary.md
```
