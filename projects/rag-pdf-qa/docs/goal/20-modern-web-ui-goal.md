# 第 20 步执行目标：实现现代风 RAG Web UI

这一步的目标是：

> 从 Swagger Docs 测试工具，升级为有自己交互页面的本地 RAG 应用。

---

## 1. 背景

当前主要通过：

```text
http://127.0.0.1:8000/docs
```

测试接口。

这适合学习 API，但不适合作为个人项目展示。

后续需要一个能完成核心流程的 UI：

```text
上传文件
查看知识库
提问
查看回答
查看 sources 和检索分数
```

---

## 2. 本次目标

实现第一版 Web UI。

功能优先级：

```text
1. 文件上传并索引
2. 文档列表展示
3. 问题输入和 RAG 回答展示
4. sources 面板展示
5. top_k / score_threshold 参数控制
6. token usage 或基础调试信息展示
```

视觉方向：

```text
现代风
玻璃质感
圆角
桌面端优先
网页端可访问
```

布局建议：

```text
左侧：知识库文档列表
中间：问答区
右侧：sources / 检索调试信息
底部：输入框和参数控制
```

---

## 3. 不做什么

本次不做：

- 登录注册
- 多用户权限
- 复杂路由系统
- 大型前端工程过度设计
- 复杂动画
- Agent UI
- 云端部署

---

## 4. 预计修改文件

如果使用 FastAPI 静态页面，可能新增：

```text
web/
  index.html
  styles.css
  app.js
```

可能修改：

```text
app/main.py
README.md
docs/00-project-continuation-guide.md
```

建议新增：

```text
docs/summary/20-modern-web-ui-step.md
docs/summary/20-modern-web-ui-summary.md
```

---

## 5. 接口变化

可能新增：

```text
GET /
GET /app
```

也可以只通过静态文件访问 UI。

后端已有接口应继续可用：

```text
/docs
/documents/index
/documents
/documents/search
/rag/ask
```

---

## 6. 验收标准

完成后应满足：

```text
1. 浏览器打开 UI 页面能看到应用主界面
2. 可以上传文件并触发索引
3. 可以输入问题并得到 RAG 回答
4. 可以看到 sources 列表
5. 可以调整 top_k 和 score_threshold
6. UI 不影响 /docs 页面
7. 8000 端口仍然是默认服务端口
```

---

## 7. 测试方式

建议测试：

```text
1. 启动 uvicorn app.main:app --reload
2. 打开 http://127.0.0.1:8000/docs
3. 确认 Swagger 正常
4. 打开 UI 页面
5. 上传测试文档
6. 提问并检查 reply/sources
7. 调整 top_k/score_threshold 后再次提问
```

如果使用前端 dev server，应记录端口。

但后端仍保持：

```text
http://127.0.0.1:8000
```

---

## 8. 完成后的 summary 文档

完成后创建：

```text
docs/summary/20-modern-web-ui-summary.md
```

并更新：

```text
README.md
docs/00-project-continuation-guide.md
```

