# 第 25 步完成总结：修复 UI Tab 布局混排

本 summary 记录第 25 步实际完成内容。

对应 goal：

```text
docs/goal/25-ui-tab-layout-fix-goal.md
```

---

## 1. 本次完成了什么

本次针对 Web UI 的 Tab 体验做了修复：

```text
1. 左侧 Tab 改成明确的垂直导航
2. Tab 按钮增加稳定高度、宽度、active 状态和二级英文标识
3. 非当前页面增加 hidden 属性
4. JS 切换 Tab 时同步 active、hidden、aria-selected
5. /web/styles.css 和 /web/app.js 增加版本 query，避免浏览器缓存旧资源
6. workspace 增加 overflow 管理，避免多个页面混在同一滚动流
7. 导入页、问答页、设置页同一时间只显示一个
```

---

## 2. 改动文件

代码：

```text
web/index.html
web/styles.css
web/app.js
```

测试：

```text
tests/test_main_api.py
```

文档：

```text
docs/goal/25-ui-tab-layout-fix-goal.md
docs/summary/25-ui-tab-layout-fix-summary.md
```

---

## 3. 关键修复点

页面隔离：

```text
初始状态：tab-import active
tab-ask hidden
tab-settings hidden
```

切换时：

```text
当前页：active + hidden=false
其他页：active=false + hidden=true
```

缓存处理：

```text
/web/styles.css?v=25
/web/app.js?v=25
```

这样浏览器会重新加载最新样式和脚本，避免继续显示旧版本 UI。

---

## 4. 验证结果

浏览器级验证结果：

```text
真实访问 http://127.0.0.1:8000/app
/web/styles.css?v=25 已加载
/web/app.js?v=25 已加载
左侧 tab-nav display = flex
左侧 tab-nav flex-direction = column
三个 Tab 按钮宽度约 262px，高度约 64px
activeButton = import
初始只有 tab-import 显示
tab-ask 初始 hidden=true / display=none
tab-settings 初始 hidden=true / display=none
tab-import 高度约 918px
tab-ask 高度 = 0
tab-settings 高度 = 0
切换到知识问答后 sourceList 仍然存在
切换到设置后 systemPromptInput 仍然存在
```

自动化测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

结果：

```text
compileall 通过
pytest 28 passed
```

---

## 5. 后续建议

后续如果继续优化 UI，可以考虑：

```text
1. 给知识问答页增加 Agent / RAG 模式切换
2. 给文件列表增加删除、重建索引、搜索过滤
3. 给设置页增加 prompt profile
4. 加入更清晰的文档索引状态和失败原因展示
```
