# 第 27 步完成总结：UI 语言和系统色偏好

本 summary 记录第 27 步实际完成内容。

对应 goal：

```text
docs/goal/27-ui-language-theme-preferences-goal.md
```

---

## 1. 本次完成了什么

本次在设置页增加了界面偏好能力：

```text
1. 新增中文 / English 语言切换
2. 新增系统色预设切换
3. 新增自定义系统色选择
4. 页面静态文案增加 data-i18n key
5. JS 增加中英文 translations 字典
6. 切换语言时同步更新大标题、Tab、页面标题、按钮、placeholder、状态文案等
7. 切换系统色时同步更新 CSS 变量 --accent / --accent-rgb / --accent-2 / --accent-2-rgb
8. 用户偏好保存到 localStorage
9. 静态资源版本号升级到 v=27
```

---

## 2. 改动文件

代码：

```text
web/index.html
web/app.js
web/styles.css
```

测试：

```text
tests/test_main_api.py
```

文档：

```text
README.md
docs/00-project-continuation-guide.md
docs/goal/README.md
docs/goal/27-ui-language-theme-preferences-goal.md
docs/summary/README.md
docs/summary/27-ui-language-theme-preferences-summary.md
```

---

## 3. 功能说明

语言切换：

```text
中文
English
```

会影响：

```text
大标题
左侧 Tab
页面标题
按钮文案
输入框 placeholder
空状态
toast 提示
debug 标签
```

不会影响：

```text
模型生成的回答内容
用户上传的知识库内容
文件名
sources 原文
```

系统色切换：

```text
teal
blue
violet
rose
custom color
```

会影响：

```text
主按钮渐变
Tab active 状态
状态 pill
代码块强调色
背景氛围色
```

---

## 4. 验证结果

浏览器级验证：

```text
点击 English 后 document.documentElement.lang = en
大标题显示 Local Knowledge RAG Agent
文件导入 Tab 显示 Import Files
设置页标题显示 Model & Prompts
问题输入 placeholder 显示 Ask a question
点击 blue 后 --accent = #5aa7ff
localStorage 写入 language=en、themeColor=blue
点击中文后 document.documentElement.lang = zh-CN
大标题显示 本地知识库 RAG Agent
选择自定义颜色 #ff3366 后 --accent = #ff3366
localStorage 写入 themeColor=custom、customColor=#ff3366
无控制台错误
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

## 5. 当前限制

当前偏好只保存在浏览器本地：

```text
localStorage.ragPdfQaUiPreferences
```

如果换浏览器或清理浏览器数据，需要重新设置。

本次没有做：

```text
后端保存 UI 偏好
多用户偏好同步
回答内容自动翻译
亮色 / 暗色模式
```

---

## 6. 后续建议

后续可以继续：

```text
1. 增加浅色 / 深色模式
2. 给 prompt profile 增加语言版本
3. 将 UI 偏好保存到后端 runtime settings
4. 增加一键恢复默认 UI 设置
```
