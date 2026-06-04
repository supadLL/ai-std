# 第 28 步执行目标：UI 背景颜色偏好

这一步的目标是：

> 在已有系统色切换的基础上，增加独立的背景颜色修改能力，让按钮主色和页面背景色可以分别调整。

---

## 1. 背景

第 27 步已经支持：

```text
中文 / English 切换
系统色切换
自定义系统色
localStorage 保存 UI 偏好
```

但当前“系统色”主要影响按钮、Tab active、强调色等主色，不等于页面背景色。

用户需要继续支持：

```text
背景颜色修改
```

所以需要新增独立的背景色控件。

---

## 2. 本次目标

本次完成：

```text
1. 设置页“界面偏好”中新增背景颜色选择器
2. 背景色独立于系统主色
3. 背景色写入 localStorage
4. 刷新页面后恢复背景色
5. 支持一键恢复默认背景色
6. 背景色应用到 CSS 变量 --bg
7. 静态资源版本号升级，避免浏览器缓存旧 JS / CSS
```

---

## 3. 不做什么

本次不做：

- 复杂主题编辑器
- 自动文字对比度计算
- 背景图片上传
- 明暗模式完整切换
- 后端保存 UI 偏好

---

## 4. 需要修改的文件

预计修改：

```text
web/index.html
web/app.js
web/styles.css
tests/test_main_api.py
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/summary/README.md
```

预计新增：

```text
docs/summary/28-ui-background-color-preference-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. 设置页能看到背景颜色选择器
2. 修改背景色后 CSS 变量 --bg 立即变化
3. 修改背景色不影响系统主色 --accent
4. 偏好写入 localStorage
5. 点击恢复默认后背景色恢复为 #0f1213
6. pytest 通过
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
点击 rose 系统色
设置背景色为 #202a33
确认 --accent = #ff7aa2
确认 --bg = #202a33
点击恢复默认
确认 --bg = #0f1213
确认 localStorage 中 backgroundColor 同步变化
```

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/28-ui-background-color-preference-summary.md
```

