# LCC s09 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s09.md)，再核对。

1. 压缩是有损的——偏好从"User prefers tabs, not spaces. Why: consistency. How: always use tabs." 退化成摘要里一句模糊的 "User prefers tabs"。且跨会话连摘要都没了。Memory 是不参与压缩、跨会话保留的持久层。

2. 路径一：索引常驻 SYSTEM — `MEMORY.md` 全文（所有记忆的名字+一行描述），极轻量。路径二：内容按需注入 — LLM side-query 选最多 5 条记忆，完整正文注入 user turn。两条缺一不可：索引让 LLM 知道"有哪些记忆存在"（即使 side-query 没选中），内容提供具体细节。

3. 压缩会删内容：snip 裁掉中间消息，micro 把旧 tool_result 替换成占位符。如果从压缩后的 messages 提取，原始对话可能已不完整，偏好信息随压缩丢失。`pre_compress` 保留了完整、未修改的对话，提取质量最高。

4. `messages` 是持久化的对话历史，记忆内容只是本轮临时注入。如果直接改 `messages`，记忆会永远留在对话历史里——后续压缩会把记忆当对话内容处理，下一轮的 tool_result 也会被记忆污染。`request_messages = messages.copy()` 保证记忆只用于本轮 LLM 调用，不污染历史。

5. `write_memory_file` 写完后自动调用 `_rebuild_index()` 重建 `MEMORY.md`。如果不重建，索引和实际文件不一致——新记忆文件在磁盘上，但 SYSTEM 的 "Memories available" 里没有它，LLM 不知道它存在，`select_relevant_memories` 也扫不到它。

6. `select_relevant_memories` 是**检索**：从已有记忆里选当前对话相关的（记忆 → 对话）。`extract_memories` 是**抽取**：从对话里识别/概括/去重，产出新记忆（对话 → 记忆）。两者都调 LLM 但干的活完全不同——前者做语义匹配，后者做信息抽取+结构化。

