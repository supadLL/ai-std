# 第 25 步执行目标：修复 UI Tab 布局混排

这一步的目标是：

> 修复 Web UI 中左侧 Tab 不像真正导航、页面内容混在一起、浏览器缓存导致旧样式继续生效的问题。

---

## 1. 背景

第 24 步已经加入：

```text
文件导入
知识问答
设置
```

三个 Tab 页面。

但实际浏览器效果存在问题：

```text
1. 左侧 Tab 看起来像普通小按钮
2. 主区域可能同时显示文件导入和知识问答内容
3. 旧 CSS / JS 可能被浏览器缓存，导致最新布局没有生效
4. 页面功能虽然存在，但视觉和交互不够清晰
```

---

## 2. 本次目标

本次修复：

```text
1. 左侧导航改成明确的垂直 Tab 菜单
2. 每个 Tab 按钮有稳定宽高和 active 状态
3. 非当前页面使用 hidden 属性隐藏
4. JS 切换时同步 active、hidden、aria-selected
5. 静态资源增加版本 query，避免浏览器继续使用旧 CSS / JS
6. 主区域同一时间只显示一个页面
7. 问答页仍然保留右侧 sources / debug 区域
```

---

## 3. 不做什么

本次不做：

- 重新设计整套品牌视觉
- 引入 React / Vue 等前端框架
- 增加新的后端接口
- 改动 RAG 检索逻辑
- 改动运行时 settings 存储结构

---

## 4. 需要修改的文件

预计修改：

```text
web/index.html
web/styles.css
web/app.js
tests/test_main_api.py
docs/summary/25-ui-tab-layout-fix-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. 初始打开 /app 只显示文件导入页
2. 左侧 Tab 是垂直导航，不是挤在一起的小按钮
3. 切到知识问答页时，文件导入页隐藏
4. 切到设置页时，文件导入页和知识问答页隐藏
5. 知识问答页仍然保留 sourceList
6. 设置页仍然保留 prompt 输入框
7. 浏览器能加载带版本号的 CSS / JS
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
确认左侧 Tab 垂直排列
确认初始只有文件导入页可见
点击知识问答，确认右侧 sources 面板可见
点击设置，确认 prompt 设置页可见
```

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/25-ui-tab-layout-fix-summary.md
```

