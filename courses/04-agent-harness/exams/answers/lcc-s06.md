# LCC s06 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s06.md)，再核对。

1. 中间过程（读文件、60 轮对话）全堆在主 `messages` 里，占满上下文，最初目标被挤出注意力，Agent 健忘。s06：用 `task` 工具 spawn 子 Agent，给它全新 `messages[]` 专心做子任务，结束只回传结论，中间过程不污染主对话。
2. 只回传最后的文本结论（`extract_text(last_message)`）。不回传整个 messages——整个 messages 就是中间过程，回传等于没隔离，照样塞爆主上下文。
3. 子 Agent 有 bash/read/write/edit/glob，但没有 `task`——禁止递归 spawn 新子 Agent（防止套娃失控）。子 Agent 也有独立 `SUB_SYSTEM`（"直接完成，别再委派"）。
4. 不对。上下文隔离 ≠ 权限隔离。子 Agent 的工具调用照样走 `PreToolUse` hook，安全策略不因上下文隔离而跳过（否则子 Agent 能绕过权限干危险操作）。
5. 还在。文件系统副作用（写/改文件、跑命令）保留在工作目录，只有对话上下文被丢弃。因为副作用是对真实世界的改变，不是上下文里的文本。
6. 教学版是全新 messages[]（从头开始，纯隔离）；Fork 模式不创建全新上下文，而是用 `buildForkedMessages()` 构造 cache-friendly 前缀（保留父 assistant message + placeholder tool results），目的是让父子 Agent 的 system prompt/tools/messages 前缀字节级一致，命中 Anthropic API 的 prompt cache 省算力。Fork 目的不是隔离而是缓存复用。

