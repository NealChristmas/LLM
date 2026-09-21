# LCC s05 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s05.md)，再核对。

1. 对话越长，工具结果不断填满上下文，系统提示（含最初目标）的影响力被稀释；10步重构做完1-3步，后面的步骤已被挤出注意力，模型开始即兴发挥。根因是上下文注意力被稀释，不是模型"忘了"。
2. 规划能力。它自己不能读文件/跑命令/做任何实际工作，只是让 Agent 动手前先把步骤列清楚、状态标好。
3. 收到任务 → 先调 `todo_write` 列全部步骤（status 全 `pending`）→ 取一个改 `in_progress` 开做 → 做完改 `completed` → 看下一个 `pending` 继续，直到全 `completed`。
4. 连续 3 轮没调 `todo_write`，循环在下一次 LLM 调用前自动注入一条 `<reminder>Update your todos.</reminder>` 提醒模型更新清单。不是 CC 真实机制（教学版造的），CC 更接近"3+todo全完成但无 verification 时追加 verification nudge"。
5. 因为它本质就是个工具（模型决定何时调、传什么参数），走统一 dispatch 让循环不变、机制一致；特殊处理反而破坏"加工具只加一行映射"的设计，让循环又膨胀。
6. V1 = TodoWrite（内存列表，退出清空）；V2 = Task System（s12）。V2 增量举两个：① 文件持久化（`tasks/{listId}/{taskId}.json`，重启可恢复）② `blockedBy` 依赖图（任务间依赖排序）。（另：proper-lockfile 并发锁、四个独立工具、TaskCreated/Completed hooks。）

