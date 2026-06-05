# 第 36 步完成总结：知识库管理能力增强

## 1. 本次完成了什么

本次把“文件导入 + 文档列表”升级为更可用的本地知识库管理能力。

新增能力：

```text
1. Web UI 支持按文件名筛选文档
2. Web UI 支持按文件类型筛选文档
3. Web UI 支持勾选多个文档并批量删除
4. Web UI 支持查看文档详情
5. Web UI 支持对单个 document_id 上传替换文件并重新索引
6. /documents/search 支持 document_id / file_type 过滤
7. /rag/ask 和 /agent/ask 支持 document_id 限定检索范围
```

因为当前项目没有保存原始上传文件，所以“重新索引”采用可执行的替换式重建：

```text
选择指定 document_id
-> 上传替换文件
-> 解析、切分、向量化
-> 删除旧 Qdrant chunks 和 metadata
-> 使用同一个 document_id 写入新 chunks 和 metadata
```

---

## 2. 改动文件

核心代码：

```text
app/main.py
app/vector_store.py
```

前端：

```text
web/index.html
web/app.js
web/styles.css
```

测试：

```text
tests/test_main_api.py
tests/test_vector_store.py
tests/test_agent.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
docs/summary/36-knowledge-base-management-enhancement-summary.md
```

---

## 3. 接口变化

新增接口：

```text
DELETE /documents/batch
POST /documents/{document_id}/reindex
```

扩展接口：

```text
POST /documents/search
POST /rag/ask
POST /agent/ask
```

`POST /documents/search` 新增可选参数：

```json
{
  "query": "GUI Agent 的核心流程是什么？",
  "limit": 5,
  "document_id": "doc-xxx",
  "file_type": "pdf"
}
```

`POST /rag/ask` 和 `POST /agent/ask` 新增可选参数：

```json
{
  "question": "这份文档的结论是什么？",
  "limit": 5,
  "score_threshold": null,
  "document_id": "doc-xxx"
}
```

---

## 4. Web UI 变化

文件导入页新增知识库管理区：

```text
文件名筛选
文件类型筛选
清除筛选
批量删除
文档详情
单文档重新索引
```

知识问答页新增：

```text
document 下拉选择
```

选择某个文档后，RAG / Agent 提问都会把 `document_id` 传给后端，从而把检索范围限定在该文档内。

---

## 5. 删除和重建索引一致性

批量删除：

```text
document_ids 去重
-> 逐个查 metadata
-> 删除 Qdrant chunks
-> 删除 metadata
-> 返回 deleted / missing_document_ids
```

单文档重建：

```text
先解析和生成新向量
-> 确认可写入 Qdrant collection
-> 删除旧 chunks
-> 删除旧 metadata
-> 使用原 document_id 写入新 chunks
-> 写入新 metadata
```

这样可以减少“旧数据已经删掉，但新文件无法解析”的风险。

---

## 6. 验证结果

编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
```

结果：

```text
通过
```

pytest：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
44 passed
```

新增覆盖：

```text
search_chunks 传递 document_id / file_type filter
/documents/search 返回过滤参数
/documents/batch 删除 chunks 和 metadata
/documents/{document_id}/reindex 保留 document_id 并替换 metadata
Web UI 包含筛选、批量删除、文档限定检索控件
```

---

## 7. 当前限制

当前还没有做：

```text
文档分页
批量重新索引
保存原始上传文件
文档版本历史
按 chunk 级别查看全文
删除前二次输入确认
```

这些适合后续作为管理体验增强继续做。

---

## 8. 下一步

下一步建议进入：

```text
第 37 步：项目演示与简历呈现优化
```

重点方向：

```text
1. 梳理项目亮点
2. 补充演示路径
3. 整理简历描述
4. 确认 README 能让新用户快速启动和体验
```
