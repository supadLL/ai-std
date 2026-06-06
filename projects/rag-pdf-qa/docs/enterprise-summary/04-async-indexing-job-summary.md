# 企业级第 04 步完成总结：异步索引任务

## 1. 本次完成内容

本次把文档入库扩展为异步任务模式：

```text
新增 index_jobs 表
上传文件后创建 index job
后台任务执行解析、chunk、embedding、Qdrant upsert
记录 queued / running / succeeded / failed 状态
记录失败 error_message
支持失败任务手动 retry
Web UI 展示任务列表、状态和重试按钮
```

旧的同步索引接口仍然保留：

```text
POST /documents/index
POST /knowledge-bases/{knowledge_base_id}/documents/index
```

新异步接口：

```text
POST /documents/index-jobs
GET /documents/index-jobs
GET /documents/index-jobs/{job_id}
POST /documents/index-jobs/{job_id}/retry
POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs
GET /knowledge-bases/{knowledge_base_id}/documents/index-jobs
GET /knowledge-bases/{knowledge_base_id}/documents/index-jobs/{job_id}
POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs/{job_id}/retry
```

## 2. 关键设计

本步使用 FastAPI `BackgroundTasks` 实现轻量后台执行，不引入 Celery / RQ / Dramatiq。

上传文件会暂存到：

```text
data/index_jobs/
```

可通过 `.env` 调整：

```text
INDEX_JOB_STORAGE_PATH=data/index_jobs
```

当前 job 和 Step 03 的知识库隔离一致：

```text
每个 job 归属 knowledge_base_id
job 列表和重试必须通过 membership 校验
worker upsert 时继续写入 tenant_id / knowledge_base_id payload
```

## 3. 修改文件

```text
app/models.py
app/index_jobs.py
app/main.py
app/config.py
migrations/versions/003_async_index_jobs.py
web/index.html
web/app.js
web/styles.css
tests/test_index_jobs.py
tests/test_main_api.py
.env.example
README.md
docs/00-project-continuation-guide.md
```

## 4. 验证结果

已通过：

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check web\app.js
.\.venv\Scripts\python.exe -m pytest tests\test_index_jobs.py tests\test_main_api.py --basetemp .pytest_tmp -p no:cacheprovider
```

阶段测试结果：

```text
22 passed
```

完整回归测试在最终提交前执行。

## 5. 下一步

下一步进入企业级第 05 步：

```text
服务化 Qdrant
索引治理
向量库连接配置
集合/索引健康检查
```
