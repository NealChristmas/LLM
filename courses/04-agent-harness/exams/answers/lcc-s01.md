# LCC s01 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s01.md)，再核对。

1. 把模型输出的命令手动跑一遍、把输出粘贴回对话框让它继续——这个"中间层"来回。loop 自动执行命令 + 把结果喂回模型，省掉人。
2. `response.stop_reason`。`"tool_use"` → 执行工具 → 结果喂回 → 继续循环；非 `"tool_use"` → `return` 退出循环。
3. 一次循环可能有多个 `tool_use` block，回填时 id 用来把每条 `tool_result` 对应到正确的 `tool_use`，模型靠 id 知道哪条结果回答的是哪次调用。不带 id 模型无法对应，结果错位、推理崩。
4. `role:"user"`。tool_result 是"给模型的输入"（环境对模型的反馈），和 user 消息一样是喂给模型的信息；assistant 角色是模型自己的输出，结果不是模型产出的。
5. 不能。agency（感知 + 推理 + 决策）是模型训练出来的能力；harness 是死代码，没有判断力。让 harness 用 if-else 决策 = LCC 开篇批判的"提示词水管工"，脆弱、不可泛化。
6. 流式响应里 `stop_reason` 可能还没更新，但内容里已经有 `tool_use` 块了，不可靠。CC 用 `needsFollowUp` 标志：流式接收时只要检测到 `tool_use` 块就置 true，靠它决定是否继续。

