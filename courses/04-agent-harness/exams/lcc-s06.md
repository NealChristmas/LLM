# LCC s06 考点与自测

## 一、知识点 / 考点

1. **动机**：主 Agent 修 bug 时读 30 文件、聊 60 轮，`messages` 涨到 120 条，大部分是"追踪调用链"的中间过程，和最终目标无关。中间过程占满上下文 → Agent 越来越"健忘"，记不住最初问题。→ 类比人"开新终端"追踪、回来继续修。Agent 也需要：独立子进程 + 独立消息列表 + 专心做一件事。
2. **核心方案**：新增 `task` 工具。调用即 `spawn` 一个子 Agent：全新 `messages[]`，跑自己的循环，结束后**只把摘要文本**回传主 Agent。对话上下文被丢弃，但**文件系统副作用（写/改文件、跑命令）保留**在工作目录。
3. **四个关键设计决策**：
   - **上下文隔离**：全新 `messages[]`——子 Agent 中间过程不污染主 Agent
   - **只回传结论**：`extract_text(last_message)`——不是回传整个 messages
   - **禁止递归**：子 Agent 无 `task` 工具——防止再 spawn 新子 Agent（套娃失控）
   - **安全策略不跳过**：子 Agent 工具调用也走 `PreToolUse` hook——上下文隔离 ≠ 权限隔离
4. **dispatch 不变**：`task` 仍走 `TOOL_HANDLERS["task"] = spawn_subagent` 分发，主循环不变。子 Agent 有独立 `SUB_SYSTEM`（明确"直接完成，别再委派"）。
5. **子 Agent 工具受限**：有 bash/read/write/edit/glob，**无 `task`**（禁递归）。仍受权限 hook 保护。
6. **安全限制**：30 轮上限（`for _ in range(30)`）防止子 Agent 无限循环。
7. **CC 对比（进阶）**：
   - **三种模式**：Normal Subagent（全新 messages，只有 prompt）、Fork Subagent（fork gate 开启，`buildForkedMessages()` 构造 cache-friendly 前缀，共享 prompt cache）、General-Purpose（fork gate 关闭，同 Normal）。
   - **Fork 模式本质**：不创建全新上下文，而是构造 cache-friendly 消息前缀，保留父 assistant message + placeholder tool results。目的不是隔离，而是让父子 Agent 的 system prompt/tools/messages 前缀**字节级一致**，命中 Anthropic API 的 prompt cache。缓存命中五要素：system prompt、tools、model、messages 前缀、thinking config。
   - **Context Isolation 精确粒度**：子 Agent 不是完全隔离——`readFileState` 从父克隆（避免重复读相同文件）；`abortController` 父向子传播；`queryTracking.depth = parentDepth+1`。
   - **递归防护**：教学版用"子无 task"；真实用 `isInForkChild()` 检查 `FORK_BOILERPLATE_TAG` 拒绝，Agent 工具默认在所有 agent 禁用集合里，teammate 场景特殊放行。
   - **Permission Bubbling**：Fork Agent `permissionMode='bubble'`，权限弹窗冒泡到父终端。
   - **Async**：教学版只展示同步；CC 还支持异步（`run_in_background` 等），s13 展开。

## 二、自测题

1. （动机）主 Agent 自己读 30 文件追踪调用链为什么会"越来越健忘"？s06 怎么解决？
2. （设计）子 Agent 跑完后回传给主 Agent 的是什么？为什么不是整个 messages 列表？
3. （设计）子 Agent 的工具集和主 Agent 有什么不同？为什么没有 `task`？
4. （判断）"上下文隔离 = 权限隔离"对吗？子 Agent 的工具调用还要不要过权限 hook？
5. （副作用）子 Agent 的对话上下文被丢弃了，它写的文件/跑的命令还在吗？为什么？
6. （CC对比）CC 的 Fork 模式和教学版"全新 messages"本质区别是什么？Fork 的目的是什么？

完成后查看[参考答案](answers/lcc-s06.md)。


