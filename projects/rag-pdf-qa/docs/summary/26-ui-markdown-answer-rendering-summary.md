# 第 26 步完成总结：优化回答 Markdown 展示

本 summary 记录第 26 步实际完成内容。

对应 goal：

```text
docs/goal/26-ui-markdown-answer-rendering-goal.md
```

---

## 1. 本次完成了什么

本次优化了知识问答页的回答展示：

````text
1. 将 markdownLite 从简单换行替换升级为轻量 Markdown 渲染
2. 支持 **加粗**，渲染为 strong
3. 支持 ``` 代码块，渲染为 pre.md-code code
4. 支持 `行内代码`，渲染为 .md-inline-code
5. 支持有序列表和无序列表
6. 支持答案 / 依据 / 资料不足之处标题展示
7. 增加代码块、行内代码、列表、段落的样式
8. AI 回答气泡加宽到 min(980px, 94%)
9. 静态资源版本号升级到 v=26，避免浏览器缓存旧脚本和样式
````

---

## 2. 改动文件

代码：

```text
web/app.js
web/styles.css
web/index.html
```

测试：

```text
tests/test_main_api.py
```

文档：

```text
docs/goal/26-ui-markdown-answer-rendering-goal.md
docs/summary/26-ui-markdown-answer-rendering-summary.md
```

---

## 3. 关键实现

渲染流程：

```text
原始回答文本
-> 按行解析
-> 识别代码围栏
-> 识别列表 / 标题 / 普通段落
-> 对文本内容先 escape
-> 再转换安全的 Markdown 子集
```

支持的 Markdown 子集：

````text
**加粗**
`行内代码`
```code fence```
1. 有序列表
- 无序列表
答案 / 依据 / 资料不足之处
````

安全策略：

```text
不渲染用户或模型返回的 HTML
所有文本内容都经过 escapeHtml
只插入前端自己生成的固定标签
```

---

## 4. 验证结果

浏览器级验证：

````text
mock /rag/ask 返回包含 **操作步骤：**、```cpp、`wait_for_data_ptr` 的回答
页面 innerText 不包含 **
页面 innerText 不包含 ```
DOM 中存在 strong
DOM 中存在 pre.md-code code
DOM 中存在 .md-inline-code
````

自动化测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

---

## 5. 当前限制

当前不是完整 Markdown 解析器。

暂不支持：

```text
表格 Markdown
引用块
链接自动识别
嵌套列表
图片 Markdown
```

这些对当前 RAG 回答可读性不是最高优先级，后续需要时再扩展。

---

## 6. 后续建议

后续可以继续优化：

```text
1. 对代码块增加复制按钮
2. 对 sources 引用增加可点击定位
3. 对长回答增加段落折叠
4. 引入成熟 Markdown 库，但需要先评估安全策略
```
