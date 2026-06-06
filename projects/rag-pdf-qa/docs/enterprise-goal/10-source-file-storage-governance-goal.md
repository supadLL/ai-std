# 企业级第 10 步执行目标：原始文件存储治理

## 1. 背景

企业级 RAG 平台不能只保存向量和 metadata。为了后续审计、重建索引、备份迁移和问题排查，需要保留原始上传文件的可追溯引用。

当前项目已经有：

```text
文档 metadata 入库
content_hash 去重
异步 index_jobs 临时文件保存
Docker volume 运行数据
```

但仍缺少：

```text
同步入库的原始文件保存
文档 metadata 中的源文件存储引用
统一的 source storage 配置
未来替换 MinIO/S3 的适配点
```

## 2. 本次目标

```text
1. 新增本地 source file storage 适配层
2. 文档成功入库时保存原始上传文件
3. documents metadata 记录 source_storage_backend 和 source_storage_key
4. 去重命中时复用已有 source storage 引用
5. reindex 时更新 source storage 引用
6. 新增迁移文件和 SQLite 兼容补列
7. /documents 响应展示 source storage metadata，不暴露绝对路径
8. .env.example / Compose / README / deployment 文档说明配置方式
```

## 3. 不做什么

本次不做：

```text
真实 S3 / MinIO 客户端集成
源文件下载接口
源文件病毒扫描
源文件生命周期清理
跨区域备份
大文件分片上传
```

后续如果要引入对象存储服务，可以保留本次 metadata 字段，只替换 storage backend。

## 4. 预计修改文件

```text
app/config.py
app/source_storage.py
app/document_store.py
app/models.py
app/main.py
app/db.py
migrations/versions/006_source_file_storage.py
tests/test_document_store.py
tests/test_main_api.py
.env.example
docker-compose.yml
README.md
docs/deployment.md
docs/00-project-continuation-guide.md
```

## 5. 环境变量建议

```text
SOURCE_STORAGE_ENABLED=true
SOURCE_STORAGE_BACKEND=local
SOURCE_STORAGE_PATH=data/source_files
```

Docker Compose 中建议使用：

```text
SOURCE_STORAGE_PATH=/app/data/source_files
```

## 6. 验收标准

```text
1. 新文档入库后 source file 被写入 source storage
2. document metadata 有 source_storage_backend/source_storage_key
3. duplicate 文档复用已有 storage metadata
4. reindex 更新 storage metadata
5. 接口不返回绝对本机路径
6. 测试全部通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests\test_document_store.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```
