# LCC s02 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s02.md)，再核对。

1. 用 bash 读文件要拼 `cat path`、写要 `echo > file`，多一层翻译，浪费 token 还容易拼错。专用工具让模型直接表达意图（`read_file path=...`），准、省、稳。
2. 工具执行时，先用 `TOOL_HANDLERS[block.name]` 查表，再以 `**block.input` 传入参数。
3. 两件事：① `TOOLS` 数组加一条工具描述 ② `TOOL_HANDLERS` 字典加一行 name→handler 映射。循环不用改。
4. 教学版按 `response.content` 的原始顺序逐个执行。CC 按"连续块分批"：并发安全的连续调用编入同一 batch 并发执行，遇到非并发安全的开新 batch 串行，batch 间严格顺序。
5. file tools 受 `safe_path` 校验（限制在工作区内）；bash 不受限制，`rm -rf /` 仍能跑 → 留给 s03 权限系统解决。
6. 不是简单"只读=可并发"，而是按具体输入判断。反例：`TaskCreate` 改了状态（写）但每次写不同文件，仍可并发；Bash 的 `ls` 只读可并发但 `rm` 写不可并发。

