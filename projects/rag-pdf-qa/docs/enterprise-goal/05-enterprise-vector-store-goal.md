# 企业级第 05 步执行目标：服务化 Qdrant 和索引治理

## 1. 背景

当前项目使用 Qdrant local：

```text
QDRANT_LOCAL_PATH=.qdrant
```

这适合本地学习，但企业场景需要服务化向量库，便于：

```text
多实例访问
备份恢复
监控
权限和网络隔离
容量规划
部署运维
```

## 2. 本次目标

本次升级向量存储层：

```text
1. 支持 Qdrant Server URL / API Key 配置
2. 保留 Qdrant local 开发模式
3. collection 命名支持环境和租户隔离
4. payload 增加 tenant_id / knowledge_base_id / document_id
5. 新增索引一致性检查接口或脚本
6. 新增 Docker Compose Qdrant 服务
```

## 3. 不做什么

本次不做：

```text
多向量库适配
Milvus / Elasticsearch 混合检索
复杂 shard 策略
大规模向量压缩
```

## 4. 预计修改文件

```text
app/config.py
app/vector_store.py
app/main.py
docker-compose.yml
.env.example
tests/test_vector_store.py
README.md
```

## 5. 配置建议

```text
QDRANT_MODE=local/server
QDRANT_LOCAL_PATH=.qdrant
QDRANT_URL=http://127.0.0.1:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_PREFIX=rag
```

## 6. 验收标准

```text
1. local 模式仍能运行
2. server 模式可连接 Docker Qdrant
3. collection 创建逻辑可配置
4. search/delete 都带租户过滤
5. pytest 通过
```

## 7. 测试方式

```powershell
docker compose up -d qdrant
.\.venv\Scripts\python.exe -m pytest tests\test_vector_store.py
```
