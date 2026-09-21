# LCC s09 考点与自测

## 一、知识点 / 考点

1. **动机**：压缩是有损的（偏好从详细说明退化成摘要里一句模糊描述），且跨会话连摘要都没了。Memory 是不参与压缩、跨会话保留的持久层。
2. **两条加载路径**：路径一（索引常驻 SYSTEM）— `MEMORY.md` 注入 SYSTEM，极轻量，让 LLM 知道有哪些记忆存在；路径二（内容按需注入）— LLM side-query 选相关记忆，完整内容注入 user turn。两者缺一不可：索引提供"目录"，内容提供"正文"。
3. **存储**：`.memory/` 下 Markdown + YAML frontmatter（`name`/`description`/`type`），`MEMORY.md` 为索引。`write_memory_file` 写完自动 `_rebuild_index()` 保持索引与文件一致。
4. **选择（select_relevant_memories）**：LLM side-query 语义匹配（对话 vs 记忆 name+description），最多 5 条；失败降级到关键词匹配。本质是**检索**任务。
5. **提取（extract_memories）**：循环结束后调 LLM 从对话中识别/概括/去重偏好，写入新记忆文件。本质是**抽取**任务。两个都调 LLM 但干的活完全不同。
6. **压缩前快照（pre_compress）**：提取时传压缩前的 `messages` 副本，因为压缩会删内容（snip 裁消息、micro 替换 tool_result），传压缩后的会丢失对话信息。
7. **浅拷贝注入（request_messages）**：记忆内容注入到 user turn 时用 `messages.copy()`，不修改原始 `messages`。记忆只是本轮临时注入，不应污染持久化的对话历史。
8. **整理（consolidate_memories）**：文件数 ≥ 10 触发，LLM 去重合并淘汰，全量替换。教学版用文件数阈值，CC 真实实现有四层门控（时间/扫描/会话/文件锁）。
9. **四种记忆类型**：user（偏好）、feedback（做事方式）、project（项目事实）、reference（外部引用）。
10. **CC 对比**：真实 CC 用 Sonnet side-query 选记忆（非 embedding）；提取通过 forked agent（受限权限）；Dream 四层门控；记忆预算 200 行/4096 字节每文件、60KB/session。

## 二、自测题

1. （动机）s08 已经有压缩了，为什么还要 s09 的 Memory？压缩解决不了什么问题？
2. （架构）Memory 系统有两条加载路径，分别是什么？各放什么内容？为什么需要两条而不是一条？
3. （数据流）`extract_memories` 为什么传 `pre_compress`（压缩前快照）而不是压缩后的 `messages`？反过来会怎样？
4. （设计）记忆内容注入到 user turn 时，为什么用 `request_messages = messages.copy()` 浅拷贝，而不是直接改 `messages`？
5. （写入）`write_memory_file` 写完文件后做了什么？为什么必须做这件事？
6. （选择 vs 提取）`select_relevant_memories` 和 `extract_memories` 都是调 LLM，它们各自做什么？为什么一个叫"选择"一个叫"提取"？

<details>
<summary>参考答案（先答完再展开）</summary>

1. 压缩是有损的——偏好从"User prefers tabs, not spaces. Why: consistency. How: always use tabs." 退化成摘要里一句模糊的 "User prefers tabs"。且跨会话连摘要都没了。Memory 是不参与压缩、跨会话保留的持久层。

2. 路径一：索引常驻 SYSTEM — `MEMORY.md` 全文（所有记忆的名字+一行描述），极轻量。路径二：内容按需注入 — LLM side-query 选最多 5 条记忆，完整正文注入 user turn。两条缺一不可：索引让 LLM 知道"有哪些记忆存在"（即使 side-query 没选中），内容提供具体细节。

3. 压缩会删内容：snip 裁掉中间消息，micro 把旧 tool_result 替换成占位符。如果从压缩后的 messages 提取，原始对话可能已不完整，偏好信息随压缩丢失。`pre_compress` 保留了完整、未修改的对话，提取质量最高。

4. `messages` 是持久化的对话历史，记忆内容只是本轮临时注入。如果直接改 `messages`，记忆会永远留在对话历史里——后续压缩会把记忆当对话内容处理，下一轮的 tool_result 也会被记忆污染。`request_messages = messages.copy()` 保证记忆只用于本轮 LLM 调用，不污染历史。

5. `write_memory_file` 写完后自动调用 `_rebuild_index()` 重建 `MEMORY.md`。如果不重建，索引和实际文件不一致——新记忆文件在磁盘上，但 SYSTEM 的 "Memories available" 里没有它，LLM 不知道它存在，`select_relevant_memories` 也扫不到它。

6. `select_relevant_memories` 是**检索**：从已有记忆里选当前对话相关的（记忆 → 对话）。`extract_memories` 是**抽取**：从对话里识别/概括/去重，产出新记忆（对话 → 记忆）。两者都调 LLM 但干的活完全不同——前者做语义匹配，后者做信息抽取+结构化。

</details>