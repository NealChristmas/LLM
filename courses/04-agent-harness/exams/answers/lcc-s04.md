# LCC s04 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s04.md)，再核对。

1. 问题：每加一个检查（日志/git add/通知）都要改 `agent_loop`，循环膨胀、难维护。解决：把检查逻辑移到 hook，循环只调 `trigger_hooks()`，扩展通过 `register_hook` 添加，循环保持干净。
2. `UserPromptSubmit`：用户输入提交后、进 LLM 前；`PreToolUse`：工具执行前；`PostToolUse`：工具执行后；`Stop`：循环即将退出时。
3. PreToolUse 返回非 None → 阻止本次工具执行（结果回填"被阻止"）；Stop 返回非 None → 不退出，注入返回值继续跑（强制续跑）。
4. 好处：循环稳定不改、扩展可插拔（加日志/权限/通知互不干扰）、职责分离。改循环 = 动核心风险大；挂 hook = 加边角零侵入。
5. 27 个。教学版只讲 4 个因为这 4 个覆盖了一个完整 agent cycle 的关键节点（输入→执行前→执行后→退出），其余 23 个是同样的模式，懂了 4 个就能举一反三。
6. 不能。CC 的不变式：hook 返回 allow 仍要检查 settings.json 的 deny/ask 规则。重要因为否则用户的 hook 脚本一句"allow"就能绕过企业安全策略，形成安全漏洞。

