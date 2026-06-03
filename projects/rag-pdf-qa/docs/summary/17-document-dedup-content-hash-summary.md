# 第 17 步完成总结：content_hash 去重与重建索引策略

本 summary 记录第 17 步实际完成内容。

对应 goal：

```text
docs/goal/17-document-dedup-content-hash-goal.md
```

---

## 1. 本次完成了什么

完成内容：

```text
1. /documents/index 增加 content_hash
2. /documents/index 增加 reindex 参数
3. 同一份文件重复上传时默认不重复写入 Qdrant
4. reindex=true 时删除旧 chunks 并重新索引
5. 文档 metadata 增加 hash、索引时间和文件大小
6. /documents 列表和详情可以看到 content_hash / content_hash_prefix
7. 增加重复上传和 reindex 回归测试
```

---

## 2. 改动文件

代码：

```text
app/main.py
app/document_store.py
app/vector_store.py
```

测试：

```text
tests/test_document_store.py
tests/test_main_api.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/17-document-dedup-content-hash-goal.md
docs/summary/10-rag-test-result.md
```

---

## 3. 接口变化

`POST /documents/index` 新增表单参数：

```text
reindex: bool = false
```

响应新增：

```text
content_hash
content_hash_prefix
is_duplicate
indexed
message
deleted_chunks
```

重复上传同一份文件时：

```text
is_duplicate = true
indexed = false
indexed_count = 0
```

强制重建时：

```text
reindex = true
is_duplicate = false
indexed = true
deleted_chunks = 旧文档 chunk 数量
```

---

## 4. metadata 变化

`data/documents.json` 中每条文档记录新增：

```text
content_hash
content_hash_prefix
indexed_at
source_file_size
```

该文件仍然是本地运行数据，继续被 `.gitignore` 忽略。

---

## 5. 验证结果

已运行：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
compileall 通过
pytest 10 passed
```

新增测试覆盖：

```text
重复上传同一 content_hash 时不解析、不 embedding、不 upsert
reindex=true 时删除旧 chunks，再重新 add metadata
DocumentStore 可以按 content_hash 查找文档
```

真实接口链路也已验证：

```text
第一次 reindex=true 上传：indexed = true
第二次普通上传同一文件：is_duplicate = true, indexed = false
第三次 reindex=true 上传：deleted_chunks = 43, indexed = true
清理测试文档：deleted_chunks = 43
```

---

## 6. 当前限制

本次只做内容 hash 去重。

还没有做：

```text
多版本文档管理
文件差异对比
原文件长期保存
跨格式统一 loader
UI 上的重建按钮
```

---

## 7. 下一步建议

进入第 18 步：

```text
支持 Markdown 和 txt 文档入库
```

对应 goal：

```text
docs/goal/18-markdown-txt-loader-goal.md
```
