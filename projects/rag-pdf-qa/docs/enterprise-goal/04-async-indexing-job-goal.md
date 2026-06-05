# 企业级第 04 步执行目标：大文件异步入库任务

## 1. 背景

当前文档入库通过 HTTP 请求同步完成。

企业场景中，文件可能很大，OCR 和 embedding 也可能耗时较长，同步请求容易：

```text
超时
阻塞 worker
无法展示进度
失败后难以重试
```

## 2. 本次目标

本次将文档入库升级为异步任务：

```text
1. 新增 index_jobs 表
2. 上传文件后创建 job
3. 后台 worker 执行解析、chunk、embedding、upsert
4. Web UI 展示任务状态
5. 支持失败原因记录
6. 支持手动重试
```

## 3. 不做什么

本次不做：

```text
复杂分布式任务调度
优先级队列
任务取消
任务并发限额策略
```

可以先用 FastAPI BackgroundTasks 或轻量队列，后续再升级 Celery / RQ / Dramatiq。

## 4. 预计修改文件

```text
app/index_jobs.py
app/main.py
app/document_loaders.py
app/vector_store.py
web/index.html
web/app.js
tests/test_index_jobs.py
```

## 5. 接口建议

```text
POST /documents/index-jobs
GET /documents/index-jobs
GET /documents/index-jobs/{job_id}
POST /documents/index-jobs/{job_id}/retry
```

状态：

```text
queued
running
succeeded
failed
```

## 6. 验收标准

```text
1. 上传文件立即返回 job_id
2. job 状态可查询
3. 成功后文档出现在知识库
4. 失败后记录 error_message
5. Web UI 可以看到任务进度
6. pytest 通过
```

## 7. 测试方式

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_index_jobs.py tests\test_main_api.py
```
