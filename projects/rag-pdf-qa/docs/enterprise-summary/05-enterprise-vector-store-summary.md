# 企业级第 05 步完成总结：服务化 Qdrant 和索引状态检查

## 本步目标

把原来只能使用 Qdrant local path 的向量存储层升级为企业部署更容易使用的 local/server 双模式，同时保留本地开发体验。

## 已完成内容

1. 新增 Qdrant 配置项：

```text
QDRANT_MODE=local/server
QDRANT_LOCAL_PATH=.qdrant
QDRANT_URL=http://127.0.0.1:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_PREFIX=rag
QDRANT_COLLECTION=rag_chunks
```

2. `app/vector_store.py` 支持：

```text
local mode:  QdrantClient(path=QDRANT_LOCAL_PATH)
server mode: QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
```

3. 保持旧配置兼容：

```text
如果显式设置 QDRANT_COLLECTION，则继续使用该 collection。
如果没有设置 QDRANT_COLLECTION，则按 QDRANT_COLLECTION_PREFIX 生成默认 collection，例如 rag_chunks。
```

4. tenant / knowledge base 过滤继续收紧：

```text
upsert payload 写入 tenant_id / workspace_id / knowledge_base_id / document_id
search 按 tenant_id + knowledge_base_id 过滤
delete 按 tenant_id + knowledge_base_id + document_id 过滤
```

5. 新增状态检查接口：

```text
GET /settings/vector-store/status
```

接口会返回：

```text
Qdrant mode
collection
local_path 或 url
collection 是否存在
vector_size
points_count
metadata document/chunk 数量
points_count 和 metadata indexed_count 是否一致
api_key_configured
```

接口不会返回真实 `QDRANT_API_KEY`。

6. 新增 `docker-compose.yml`：

```powershell
docker compose up -d qdrant
```

## 涉及文件

```text
app/config.py
app/runtime_settings.py
app/vector_store.py
app/main.py
app/evaluation.py
docker-compose.yml
.env.example
tests/test_vector_store.py
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
```

## 验收方式

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## 下一步

建议进入企业级第 06 步：审计日志与基础观测。重点是记录关键操作、用户、知识库、文档、索引任务和错误，先做最小可用审计，不要提前扩展到完整监控平台。
