# 企业级第 10 步完成总结：原始文件存储治理

本步骤补齐企业级 RAG 平台的原始文件保存和可追溯 metadata。

---

## 1. 本次新增能力

```text
本地 source file storage 适配层
文档成功入库后保存原始上传文件
documents metadata 记录 source_storage_backend/source_storage_key
duplicate 文档复用已有 source storage 引用
reindex 更新 source storage 引用
迁移 006_source_file_storage
SQLite 兼容补列
/documents 响应展示 source storage metadata，不返回绝对路径
```

---

## 2. 新增配置

```text
SOURCE_STORAGE_ENABLED=true
SOURCE_STORAGE_BACKEND=local
SOURCE_STORAGE_PATH=data/source_files
```

Docker Compose 中默认：

```text
SOURCE_STORAGE_PATH=/app/data/source_files
```

该目录位于 `app_data` volume 内，会随容器重建保留。

---

## 3. Metadata 字段

`documents` 表新增：

```text
source_storage_backend
source_storage_key
```

接口响应只返回相对 object key，例如：

```text
org_default/ws_default/kb_default/doc_id/hash-filename.pdf
```

不会返回本机绝对路径。

---

## 4. 修改文件

| 文件 | 说明 |
|---|---|
| `app/source_storage.py` | 本地 source storage 适配层 |
| `app/config.py` | 新增 SOURCE_STORAGE_* 配置 |
| `app/models.py` | documents 新增存储引用字段 |
| `app/document_store.py` | DocumentRecord 和 add_document 支持存储引用 |
| `app/main.py` | 入库、duplicate、reindex 响应接入 source storage |
| `app/db.py` | SQLite 旧库兼容补列 |
| `migrations/versions/006_source_file_storage.py` | Alembic 迁移 |
| `.env.example` | 新增配置模板 |
| `docker-compose.yml` | Compose source storage 配置 |
| `Dockerfile` | 创建 `/app/data/source_files` |
| `.gitignore` | 排除 `data/source_files/` |
| `tests/test_source_storage.py` | 覆盖本地写入和 object key |
| `tests/test_document_store.py` | 覆盖 metadata 字段 |
| `tests/test_database.py` | 覆盖数据库持久化 |
| `tests/test_main_api.py` | 覆盖 API 入库返回和 source file 写入 |

---

## 5. 验证方式

已执行：

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest tests\test_source_storage.py tests\test_document_store.py tests\test_database.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

结果：

```text
targeted tests: 28 passed
full pytest: 77 passed
```

---

## 6. 当前边界

本次只实现本地 backend。后续可以在不改变 documents metadata 字段的前提下扩展：

```text
MinIO / S3 backend
源文件下载接口
生命周期清理
病毒扫描
对象存储备份
```
