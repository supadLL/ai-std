# 第 26 步执行目标：优化回答 Markdown 展示

这一步的目标是：

> 让知识问答页的 AI 回答更适合人类阅读，不再把 `**加粗**`、代码围栏等 Markdown 原始标记直接显示出来。

---

## 1. 背景

RAG prompt 会要求模型输出结构化内容，例如：

````text
答案：
**操作步骤：**
```cpp
...
```
````

但前端此前只做了：

```text
HTML escape
换行转 <br>
```

所以页面会直接显示：

````text
**操作步骤：**
```cpp
````

这会让回答看起来不像正常聊天页面，也不利于阅读代码和步骤。

---

## 2. 本次目标

本次完成：

````text
1. 前端增加安全的轻量 Markdown 渲染
2. 支持 **加粗**
3. 支持 ``` 代码块
4. 支持 `行内代码`
5. 支持有序列表和无序列表
6. 支持答案 / 依据 / 资料不足之处标题展示
7. 增加代码块、行内代码、列表的 CSS 样式
8. 回答气泡适当加宽，方便阅读较长技术回答
9. 静态资源版本号升级，避免浏览器缓存旧 JS / CSS
````

---

## 3. 不做什么

本次不做：

- 引入完整 Markdown 库
- 支持所有 GitHub Flavored Markdown
- 支持 HTML 原样渲染
- 改动后端 RAG prompt
- 改动 DeepSeek 调用逻辑

当前重点是让常见 RAG 回答格式可读，并保持 XSS 安全。

---

## 4. 需要修改的文件

预计修改：

```text
web/app.js
web/styles.css
web/index.html
tests/test_main_api.py
docs/summary/26-ui-markdown-answer-rendering-summary.md
```

---

## 5. 验收标准

完成后应满足：

````text
1. 页面不再直接显示 **操作步骤** 这种 Markdown 加粗标记
2. 页面不再直接显示 ```cpp 这种代码围栏
3. 加粗内容会渲染成 strong
4. 代码块会渲染成 pre/code
5. 行内代码会渲染成 code
6. 列表结构比纯文本换行更清晰
7. HTML 内容仍然会被 escape，不直接执行
8. pytest 通过
````

---

## 6. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

浏览器验证：

````text
mock /rag/ask 返回包含 **加粗**、```cpp、`行内代码` 的回答
确认页面 innerText 不包含 ** 和 ```
确认 DOM 中存在 strong、pre.md-code code、.md-inline-code
````

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/26-ui-markdown-answer-rendering-summary.md
```
