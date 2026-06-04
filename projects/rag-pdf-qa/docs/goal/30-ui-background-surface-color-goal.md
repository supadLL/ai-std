# 第 30 步执行目标：背景色作用到整体 UI 面板

这一步的目标是：

> 修正背景颜色偏好当前只影响页面最底层背景的问题，让背景颜色能影响整个 UI 的主要背景块，包括左侧导航、主工作区面板、表单区、文档卡片和 sources 卡片。

---

## 1. 背景

第 28 步新增了背景颜色设置：

```text
backgroundColor -> CSS 变量 --bg
```

但实际效果是：

```text
只修改了最底层 body 背景
侧栏 / 主面板 / 卡片 / 表单仍然是固定灰色半透明块
```

这不符合用户想要的“整个 UI 背景颜色”。

---

## 2. 本次目标

本次完成：

```text
1. 背景颜色不仅作用到 --bg
2. 背景颜色同时派生出面板背景色
3. 左侧导航面板使用背景色派生色
4. 主工作区面板使用背景色派生色
5. 表单区、文档卡片、sources 卡片、debug 卡片使用背景色派生色
6. 保留玻璃质感和边框层次
7. 系统主色按钮仍然独立于背景色
8. 静态资源版本号升级，避免浏览器缓存旧 CSS / JS
```

---

## 3. 不做什么

本次不做：

- 完整主题编辑器
- 自动选择文字颜色
- 改动语言切换
- 改动 RAG 后端逻辑
- 新增后端接口

---

## 4. 需要修改的文件

预计修改：

```text
web/app.js
web/styles.css
web/index.html
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

预计新增：

```text
docs/summary/30-ui-background-surface-color-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. 修改背景颜色后 --bg 变化
2. 修改背景颜色后 --panel 变化
3. 修改背景颜色后 --panel-strong 变化
4. 修改背景颜色后 --surface 变化
5. 修改背景颜色后 --surface-strong 变化
6. 左侧导航和主工作区不再保持固定灰色
7. 系统主色 --accent 不受背景色修改影响
8. pytest 通过
```

---

## 6. 测试方式

代码测试：

```powershell
.\.venv\Scripts\python.exe -m compileall app tests scripts
.\.venv\Scripts\python.exe -m pytest
```

浏览器验证：

```text
打开 http://127.0.0.1:8000/app
进入设置页
设置系统主色为 rose
设置背景色为 #202a33
确认 --accent = #ff7aa2
确认 --bg = #202a33
确认 --panel / --surface 等变量同步变为 #202a33 派生色
确认左侧导航和主面板背景色发生变化
```

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/30-ui-background-surface-color-summary.md
```

