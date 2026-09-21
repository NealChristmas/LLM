# LCC s08 考点与自测

## 一、知识点 / 考点

1. **动机**：上下文窗口有限；`messages` 堆满文件内容/命令输出 → API 报 `prompt_too_long` → Agent 卡死。不压缩干不了长任务。
2. **核心原则：便宜的先跑，贵的后跑**。前三层纯文本/结构操作 **0 API**（便宜）；第四层才调一次 LLM 摘要（贵）；最后应急兜底 API 报错。
3. **L1 snip_compact**：消息数 > 50 → 留头 3 + 尾 47，中间裁掉留占位符；特殊保护：不把 `assistant(tool_use)` 和紧跟的 `user(tool_result)` 拆开。0 API。遗留：tool_result 内容仍在剩余消息里累积。
4. **L2 micro_compact**：只留最近 3 条 tool_result 完整内容，更旧超 120 字符替换成一行占位符。0 API。遗留：单条新结果可能就 500KB。
5. **L3 tool_result_budget**：最后一条 user 消息里 tool_result 总和 > 200KB → 按大小排序，从最大的开始落盘到 `.task_outputs/`，上下文留 `<persisted-output>` 标记 + 前 2000 字符预览。0 API。遗留：机械操作不理解内容，token 仍可能超。
6. **L4 compact_history**：前三层跑完 token 仍超阈值 → 调一次 LLM：① 写 transcript 到 `.transcripts/` ② LLM 摘要（目标/发现/已改文件/剩余工作/约束）③ 所有旧消息换成一条 `[Compacted]\n\n{summary}`。1 API。**熔断器**：连续失败 3 次停。
7. **应急 reactive_compact**：API 还报 `prompt_too_long`(413) 时触发；策略更温和（留最近约 5 条原始 + 早期摘要）；重试上限 1 次，再失败抛异常（完整错误恢复留给 s11）。
8. **执行顺序**：`budget → snip → micro → auto`（编号 L1-L4 是教学用，执行不是 1→2→3→4）。**关键：budget 必须在 micro 前**——micro 会把旧大 tool_result 替换成占位符，budget 必须先落盘防内容永久丢失。CC 源码也是 `applyToolResultBudget` 放最前。
9. **compact_history vs reactive_compact**：触发（阈值/模型主动 vs API 报错）、策略（全量摘要只留一条 vs 温和留最近 5 条）、性质（常规 vs 兜底救火）。
10. **CC 对比（进阶）**：顺序多了 `contextCollapse`；snip 是 feature gate（`HISTORY_SNIP`）只在主线程启用 + 暴露 `SnipTool`；micro 两条路径（time-based 60min / cached 按计数）；autoCompact 阈值用**精确 token** = `contextWindow - maxOutputTokens - 13000`（教学版用字符数估算）；摘要 prompt 严（开头 `CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.`，先 `<analysis>` 再 `<summary>`）；**后压缩恢复**（compact 后自动重读最近 5 文件，每个 5K、总 50K 预算，教学版不恢复）；`readFileState` 重复读未变文件返回 `FILE_UNCHANGED_STUB`；还有 `sessionMemoryCompact` 辅助机制（s09 后回头看）。

## 二、自测题

1. （动机）为什么 Agent 跑久了会卡死？不压缩会怎样？
2. （原则）四层压缩的核心设计原则是什么？为什么前三层在前、第四层最后？
3. （层细节）L1 snip / L2 micro / L3 budget 各做什么？分别花 API 吗？每层留下什么问题给下一层？
4. （顺序）实际执行顺序是什么？为什么 budget 必须在 micro 前面？反过来会怎样？
5. （对比）compact_history 和 reactive_compact 的触发、策略、性质有什么不同？
6. （CC对比）CC 的 autoCompact 阈值怎么算？摘要 prompt 有什么硬性要求？教学版省了哪个"后压缩恢复"机制？

完成后查看[参考答案](answers/lcc-s08.md)。


