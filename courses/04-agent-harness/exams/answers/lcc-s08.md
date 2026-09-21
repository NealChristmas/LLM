# LCC s08 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s08.md)，再核对。

1. messages 堆满文件内容/命令输出，总 token 超上下文窗口，API 报 `prompt_too_long` 拒绝。不压缩，Agent 在大项目里干不了长任务（一上来就满）。
2. 便宜的先跑贵的后跑。前三层纯文本/结构操作 0 API（便宜），能腾够就绝不用贵的；第四层才调一次 LLM 摘要（贵）。省 API 调用、省钱省时间。
3. L1 snip：消息 > 50 留头 3 尾 47 裁中间，0 API，遗留 tool_result 内容仍在剩余消息累积；L2 micro：只留最近 3 条 tool_result 完整内容、更旧占位，0 API，遗留单条新结果可能 500KB；L3 budget：最后一条 user 消息 tool_result 总和 > 200KB 落盘到 `.task_outputs/` 留标记 + 预览，0 API，遗留机械操作不理解内容、token 仍可能超。
4. `budget → snip → micro → auto`。budget 必须在 micro 前：micro 会把旧大 tool_result 替换成一行占位符，budget 必须先把完整内容落盘，否则 micro 一替换那 30KB 旧文件就**永久丢了**。反过来（micro 先）会丢失内容。CC 源码也把 `applyToolResultBudget` 放最前。
5. 触发：compact_history 是 token 超阈值 / 模型主动调 compact 工具；reactive 是 API 报 `prompt_too_long`。策略：compact_history 全量摘要只留一条；reactive 温和留最近 5 条 + 早期摘要。性质：常规 vs 兜底救火。
6. 阈值 = `contextWindow - maxOutputTokens - 13000`（精确 token，教学版用字符数估算）。摘要 prompt 硬性：开头 `CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.`（禁调工具），要求先 `<analysis>` 再 `<summary>`。教学版省了"后压缩恢复"——compact 后自动重读最近 5 个文件（每个 5K、总 50K 预算），教学版只留摘要不恢复。

