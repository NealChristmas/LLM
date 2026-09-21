# LCC s10 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s10.md)，再核对。

1. TodoWrite 是"当前任务"的执行清单，存在进程内存里，关了就没了。Task System 是"整个项目"的任务状态机，跨会话持久化，有依赖图和认领机制。两者不替代：TodoWrite 管"当前任务怎么做"，Task System 管"项目有哪些任务、谁在做、做完没"。

2. `create_task` 的 ID 是运行时随机生成的（`secrets.token_hex(4)`），Agent 在调用前不知道 ID。如果在一个 response 里同时调 `create_task("API")` 和 `update_task(???, ["schema_id"])`，`update_task` 需要的 ID 还没返回。所以必须分两阶段：先创建拿 ID，再用 ID 加依赖。

3. 只检查直接依赖不够。假设已有 A→B→C（A 依赖 B，B 依赖 C），现在想加 C→A。如果只检查直接依赖，C 的直接依赖是 A，A 的直接依赖是 B，没有直接冲突。但加上 C→A 后形成 A→B→C→A 的环，三个任务互相等待永远无法开始。传递闭包沿 `blockedBy` 链向上追溯，发现 A 最终依赖 C → 拒绝。

4. `ready_before` 记录完成前已经可认领的任务。去掉差集的话，每次 `complete_task` 都会列出所有 pending 且依赖满足的任务——包括那些本来就解锁的、和这次完成无关的任务。差集保证只通知"因我而解锁"的下游，信息更精准。

5. 两层校验：① `TASK_ID_PATTERN.fullmatch(task_id)` — 只接受 `task_[0-9a-f]{8}` 格式，防止 `../../../etc/passwd` 路径注入；② `is_relative_to(root)` — 即使 ID 格式合法，解析后的绝对路径也必须在工作区内，防止符号链接等绕过。

6. JSON 文件：简单，零依赖，可跨语言/跨平台读，git 可 diff，运维友好。SQLite：需要额外依赖，多进程并发写需要锁，但查询更快、支持事务。内存+定期落盘：崩溃丢数据，且需要序列化/反序列化逻辑。教学版选 JSON 文件是因为"简单即正确"，CC 真实实现也用的 JSON 文件。

