# LCC s04 考点与自测

## 一、知识点 / 考点

1. 动机：s03 把 `check_permission` 硬编码进循环。每加一个检查（日志/git add/slack 通知）都要改 `agent_loop`，循环很快膨胀认不出。→ 扩展应挂在外面，循环是稳定核心。
2. 核心变更：s03 循环和权限逻辑保留；把 `check_permission` 从循环体移到 hook；循环不再直接调检查函数，改为 `trigger_hooks("PreToolUse", block)`，由注册表决定跑什么。
3. 4 个事件覆盖一个 agent cycle：`UserPromptSubmit`（输入提交后、进 LLM 前：输入验证/注入上下文）、`PreToolUse`（执行前：权限/日志）、`PostToolUse`（执行后：副作用如 git add/输出检查）、`Stop`（退出时：收尾，CC 还可强制续跑）。
4. 机制：`HOOKS = {事件: [回调]}`；`register_hook(event, cb)` 追加；`trigger_hooks(event, *args)` 依次跑，返回值 ≠ None 表示"停"（PreToolUse 阻止本次执行；Stop 强制续跑）。
5. 设计要点：扩展通过 `register_hook` 添加，循环只调 `trigger_hooks()`，具体逻辑全在回调里，循环保持干净。
6. CC 对比（进阶）：CC 实际 27 个 hook 事件，教学版讲 4 个核心；`HookResult` 14 字段（`blockingError` 注入对话让模型自纠、`permissionBehavior`、`updatedInput` 改输入等）；关键不变式：hook 返回 allow 仍不能绕过 settings.json 的 deny/ask 规则（教学版无此层 = 安全漏洞）；`stopHookActive` 防 stop hook 无限循环；PostToolUse `preventContinuation` 优雅停机。

## 二、自测题

1. （动机）s03 把权限检查写进循环有什么问题？s04 怎么解决的？
2. （流程）4 个 hook 事件分别在 agent cycle 的哪个节点触发？
3. （细节）PreToolUse 回调返回非 None 表示什么？Stop 回调返回非 None 呢？
4. （设计）为什么说"循环是稳定核心，扩展挂在外面"？好处是什么？
5. （CC对比）CC 有多少个 hook 事件？教学版为什么只讲 4 个？
6. （CC对比/安全）CC 里 hook 返回 allow 能绕过 settings.json 的 deny 规则吗？为什么这很重要？

完成后查看[参考答案](answers/lcc-s04.md)。


