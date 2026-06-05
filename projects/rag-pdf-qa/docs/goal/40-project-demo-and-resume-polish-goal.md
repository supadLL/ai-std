# 第 40 步执行目标：项目演示与简历呈现优化

这一步的目标是：

> 把已经完成的工程能力整理成对外可读、可演示、可写简历的项目呈现材料。

---

## 1. 背景

当前项目已经具备个人项目级基础能力，但别人第一次看到仓库时，还需要快速理解：

```text
这个项目解决什么问题？
技术栈是什么？
RAG 链路怎么走？
如何启动？
效果长什么样？
简历可以怎么描述？
```

代码完成只是第一步，项目呈现会直接影响简历和面试沟通效果。

---

## 2. 本次目标

本次完成：

```text
1. README 增加项目架构图
2. README 增加 RAG 链路图
3. README 增加 Web UI 截图
4. README 增加核心接口表
5. README 增加简历描述模板
6. README 增加面试讲解要点
7. docs 增加项目演示脚本
```

---

## 3. 不做什么

本次不做：

- 新增业务功能
- 修改 RAG 检索逻辑
- 修改 DeepSeek 调用
- 修改 UI 交互逻辑
- 美化但不解释的宣传页

---

## 4. 需要修改的文件

预计新增：

```text
docs/summary/project-demo-script.md
docs/assets/
```

预计修改：

```text
README.md
docs/00-project-continuation-guide.md
projects/rag-pdf-qa/README.md
```

可能新增图片：

```text
docs/assets/rag-flow.png
docs/assets/web-ui-screenshot.png
docs/assets/evaluation-screenshot.png
```

完成后新增：

```text
docs/summary/40-project-demo-and-resume-polish-summary.md
```

---

## 5. 接口变化

本次不新增接口。

---

## 6. 验收标准

完成后应满足：

```text
1. 新开发者能通过 README 理解项目定位
2. README 包含启动方式、技术栈、核心能力和演示入口
3. README 包含 RAG 链路图或结构图
4. README 包含至少一张 Web UI 截图
5. docs 中有项目演示脚本
6. 简历描述不夸大，不写企业级平台
```

---

## 7. 测试方式

文档检查：

```text
从 README 开始阅读，确认 5 分钟内能理解项目：
1. 做什么
2. 怎么跑
3. 怎么用
4. 技术亮点
5. 简历怎么讲
```

链接检查：

```text
确认 README 中所有本地文档链接可打开
确认图片路径正确
```

代码检查：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## 8. 完成后的 summary 文档

完成后写入：

```text
docs/summary/40-project-demo-and-resume-polish-summary.md
```
