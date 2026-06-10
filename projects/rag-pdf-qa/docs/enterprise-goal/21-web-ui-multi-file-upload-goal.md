# 企业级第 21 步执行目标：Web UI 多文件批量导入

## 1. 背景

当前企业级分支已经完成异步索引任务、知识库隔离和 Web UI 账号/成员管理。

现在 Web UI 的“文件导入”一次只能选择并提交一个文件。对于团队知识库场景，这会让 PDF、Markdown、txt、html、docx、csv、xlsx 等资料初始化入库变得很低效。

后端已经有可复用的异步索引任务接口：

```text
POST /documents/index-jobs
POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs
GET /documents/index-jobs
```

所以本次优先在前端做批量提交，不新增后端批量上传接口。

## 2. 本次目标

本次完成：

```text
1. Web UI 文件选择器支持 multiple 多文件选择。
2. 选择后显示文件数量和前几个文件名摘要。
3. 点击上传后按顺序逐个创建异步索引任务。
4. 每个成功提交的任务立即进入 Index jobs 列表。
5. 单个文件失败不阻断后续文件继续提交。
6. 批量提交结束后提示全部成功、部分失败或全部失败。
7. 保持当前 knowledge base、chunk_size、overlap、reindex 参数对每个文件生效。
```

## 3. 不做什么

本次不做：

- 不新增后端批量上传 API。
- 不并发提交多个大文件，避免压垮本地开发服务。
- 不修改 index job 数据模型。
- 不修改文档解析、chunk、embedding 或 Qdrant 入库逻辑。
- 不绕过现有上传大小和文件类型校验。

## 4. 需要修改的文件

预计修改：

```text
web/index.html
web/app.js
tests/test_main_api.py
docs/enterprise-goal/README.md
docs/enterprise-summary/
docs/00-project-continuation-guide.md
README.md
```

## 5. 接口变化

本次不新增后端接口。

前端继续调用现有接口：

```text
POST /documents/index-jobs
POST /knowledge-bases/{knowledge_base_id}/documents/index-jobs
```

批量导入策略：

```text
用户选择 N 个文件
-> 前端按顺序为每个文件构造 FormData
-> 每个文件各调用一次 index-jobs 接口
-> 每个返回的 job 放入 Index jobs 列表
-> 批量结束后刷新任务列表
```

## 6. 验收标准

完成后应满足：

```text
1. 文件选择器可以一次选择多个支持格式文件。
2. 单文件选择仍然显示文件名。
3. 多文件选择显示数量和文件名摘要。
4. 上传时顺序提交，不并发提交。
5. 成功提交多个文件后 Index jobs 中能看到多个任务。
6. 单个文件失败时不影响后续文件继续提交。
7. /app 页面静态资源仍能正确加载。
8. node --check、compileall 和 pytest 通过。
```

## 7. 测试方式

本地测试：

```powershell
node --check web/app.js
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests/test_main_api.py tests/test_auth.py
.\.venv\Scripts\python.exe -m pytest
```

接口和页面验证：

```text
GET /app
GET /web/app.js
GET /web/styles.css
Web UI 选择多个文件并点击“上传索引”
```

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/enterprise-summary/21-web-ui-multi-file-upload-summary.md
```
