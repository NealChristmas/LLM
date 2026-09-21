# LCC s05 考点与自测

## 一、知识点 / 考点

1. 动机：长任务中模型做着做着就偏（改3文件跑测试发现失败 → 修着修着忘了最初目标）。根因：对话越长，工具结果填满上下文，系统提示影响力被稀释，10步重构做完1-3步就即兴发挥。
2. 核心变更：保留 hook 结构；新增 `todo_write` 工具 + reminder 机制。dispatch 不变（新工具仍走 `TOOL_HANDLERS`）。
3. 关键洞察：`todo_write` 本身不做任何实际工作（不能读文件/跑命令），只让 Agent 在动手前理清思路——增加的是**规划能力**，不是执行能力。
4. 工作流：收到任务 → `todo_write` 列所有步骤（全 pending）→ 做一个改 `in_progress` → 做完改 `completed` → 看下一个 `pending` → 继续。
5. nag reminder：连续 3 轮没调 `todo_write`，循环自动注入 `<reminder>Update your todos.</reminder>`（教学机制，CC 无固定3轮逻辑）。
6. SYSTEM 提示加入"先计划再执行"引导。
7. CC 对比（进阶）：CC 两套任务系统并存——TodoWrite(V1) 内存列表 AppState；Task System(V2=s12) 文件持久化 + 依赖图 + 并发锁 + ownership，`isTodoV2Enabled()` 控制（交互式默认V2，SDK非交互默认V1，`CLAUDE_CODE_ENABLE_TASKS` 强制V2）。CC 用 `activeForm` 给 UI spinner；CC 的 nudge 是"3+todo全完成但无 verification 项时追加 verification nudge"。Task System 增量：文件持久化、`blockedBy` 依赖图、proper-lockfile 并发锁、四个独立工具、TaskCreated/Completed hooks。

## 二、自测题

1. （动机）长任务里模型为什么会"做着做着就偏"？根因是什么？
2. （洞察）todo_write 给 Agent 增加的是"执行能力"还是"规划能力"？它自己能读文件/跑命令吗？
3. （流程）Agent 收到复杂任务后的典型 todo 工作流是什么？状态怎么变？
4. （机制）nag reminder 是什么？触发条件是什么？它是 CC 的真实机制吗？
5. （设计）为什么 todo_write 也要走 `TOOL_HANDLERS` 分发，而不是特殊处理？
6. （CC对比）CC 有两套任务系统，分别是什么？V2 相比 V1 的核心增量举两个。

完成后查看[参考答案](answers/lcc-s05.md)。


