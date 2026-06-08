# 第 06 步执行目标：客服聊天 Web UI 和管理视图

## 1. 背景

这个项目需要能被直观看到和演示。

Web UI 应该突出客服 Agent 的业务流程，而不是只展示 API。

## 2. 本次目标

新增本地 Web UI：

```text
用户聊天窗口
Agent route 展示
tools_used 展示
sources 展示
订单 mock 数据查看
工单列表
知识库样例查看
```

新增入口：

```text
GET /
GET /app
```

## 3. 不做什么

本次不做：

```text
复杂前端框架
登录权限
移动端深度适配
真实客服坐席工作台
```

## 4. 预计改动文件

```text
web/index.html
web/app.js
web/styles.css
app/main.py
tests/test_main_api.py
docs/summary/06-web-ui-summary.md
```

## 5. 页面结构建议

```text
左侧导航：
  客服对话
  工单管理
  Mock 数据
  知识库

主区域：
  聊天消息
  输入框
  Agent 调试信息
  sources / tools 展示
```

## 6. 验收标准

```text
/app 可以打开页面
页面能发起 Agent 问答
页面能展示 route_reason 和 tools_used
页面能展示工单列表
页面能查看 mock 订单数据
JS 语法检查通过
pytest 仍然通过
```

## 7. 测试方式

```powershell
node --check web/app.js
python -m compileall app tests
python -m pytest
```

手动验证：

```text
打开 http://127.0.0.1:8010/app
输入：订单 CS1001 到哪了？
查看 route、tools_used 和回复。
```

