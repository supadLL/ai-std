# 第 29 步执行目标：网页标题与项目图标

这一步的目标是：

> 优化浏览器 Tab 中的网页标题展示，并为 Local Knowledge RAG Agent 生成一个科技感、立体感的项目图标，用作网页 favicon / 展示图标。

---

## 1. 背景

当前浏览器 Tab 显示仍比较普通：

```text
标题：Local Knowledge RAG Agent
图标：浏览器默认图标
```

这会让项目在浏览器中缺少辨识度。

当前项目已经逐渐从接口 Demo 发展为本地 RAG Agent 工具，因此需要一个更符合项目气质的网页展示图标。

---

## 2. 本次目标

本次完成：

```text
1. 优化网页 title
2. 生成一个符合项目主题的科技感立体图标
3. 将图标保存到项目 web assets 中
4. 在 index.html 中接入 favicon
5. 支持浏览器 Tab 展示图标
6. 静态资源版本号升级，避免浏览器缓存旧资源
```

图标方向：

```text
Local Knowledge RAG Agent
知识库
向量检索
AI Agent
科技感
立体感
深色背景适配
```

---

## 3. 不做什么

本次不做：

- 完整品牌 VI
- 多尺寸全套 PWA 图标
- 动态图标
- 重新设计主页面布局
- 修改 RAG 后端逻辑

---

## 4. 需要修改的文件

预计修改：

```text
web/index.html
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

预计新增：

```text
web/assets/rag-agent-icon.png
docs/summary/29-web-title-favicon-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. web/assets/rag-agent-icon.png 存在
2. index.html 中有 favicon link
3. favicon link 指向项目内图标文件
4. title 比原来更适合浏览器 Tab 展示
5. /app 页面能返回新 title 和 favicon link
6. pytest 通过
```

---

## 6. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

浏览器 / 接口验证：

```text
GET http://127.0.0.1:8000/app
确认 title 更新
确认 HTML 包含 /web/assets/rag-agent-icon.png
确认 GET /web/assets/rag-agent-icon.png 返回 200
```

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/29-web-title-favicon-summary.md
```

