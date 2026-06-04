# 第 27 步执行目标：UI 语言和系统色偏好

这一步的目标是：

> 在 Web UI 中增加中文 / 英文语言切换，以及系统色切换能力，让界面更适合不同使用习惯和展示场景。

---

## 1. 背景

当前 Web UI 已经支持：

```text
文件导入
知识问答
设置
运行时 LLM / prompt 配置
Markdown 回答渲染
```

但界面仍然缺少两个基础偏好能力：

```text
1. 页面静态文案不能在中文 / 英文之间切换
2. 系统主色固定，不能根据用户偏好调整
```

后续这个项目可能用于学习、演示或换环境使用，所以需要把这些偏好放到设置页中。

---

## 2. 本次目标

本次完成：

```text
1. 设置页新增“界面偏好”区域
2. 支持中文 / English 切换
3. 切换语言后更新大标题、Tab、页面标题、按钮、placeholder、状态提示等静态文案
4. 支持系统色切换
5. 提供多个预设系统色
6. 支持自定义颜色选择
7. 语言和系统色保存到 localStorage
8. 刷新页面后自动恢复用户偏好
9. 静态资源版本号升级，避免浏览器缓存旧 JS / CSS
```

---

## 3. 不做什么

本次不做：

- 后端多语言接口
- 翻译 RAG 回答内容
- 翻译用户上传的知识库内容
- 多主题亮色 / 暗色切换
- 用户登录后的偏好同步

当前偏好只保存在当前浏览器本地。

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
docs/summary/27-ui-language-theme-preferences-summary.md
```

---

## 5. 验收标准

完成后应满足：

```text
1. 设置页能看到语言切换控件
2. 设置页能看到系统色切换控件
3. 点击 English 后，大标题、Tab、页面标题、按钮和 placeholder 变成英文
4. 点击中文后，界面恢复中文
5. 点击预设颜色后，系统主色立即变化
6. 使用自定义颜色后，系统主色立即变化
7. 偏好写入 localStorage
8. 页面刷新后偏好仍然生效
9. pytest 通过
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
点击 English
确认 document.documentElement.lang = en
确认标题和 Tab 变成英文
点击中文
确认 document.documentElement.lang = zh-CN
点击预设系统色
确认 --accent 变量变化
选择自定义颜色
确认 localStorage 中记录 customColor
```

---

## 7. 完成后的 summary 文档

完成后写入：

```text
docs/summary/27-ui-language-theme-preferences-summary.md
```

