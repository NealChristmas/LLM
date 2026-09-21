# LCC s07 自测参考答案

这份答案从旧项目的逐章自测中继承。先完成[题目](../lcc-s07.md)，再核对。

1. 每次 LLM 调用都带这 6500 行，改 CSS 颜色也带 SQL 文档，99% 无关，白耗 token，还稀释 system prompt 影响力。
2. 第一级：目录在 system prompt，启动时注入，~100 tokens/skill，每轮都带；第二级：内容在 tool_result，Agent 调 `load_skill` 时注入，~2000 tokens/skill，按需。
3. Agent 每轮从 SYSTEM 里的目录（`list_skills` 注入）知道有哪些技能。`load_skill` 的内容作为 **tool_result** 进入当前 messages，不是塞进 system prompt。
4. 通过注册表查找，模型只给技能名（不给文件路径），避免路径遍历攻击——模型不能靠 `../../etc/passwd` 之类读任意文件。
5. 按需加载解决"不该提前带的不要带"（只在该用技能时才花 token）；compact 解决"该丢的怎么丢"（旧 tool_result 占着上下文没价值时压缩/丢弃）。配合：`load_skill` 进来的内容随历史携带，到该压缩时交给 compact 处理。
6. `context: fork` 表示该技能作为**子 Agent** 运行（不是 inline 展开进当前上下文）。教学版省略因为它只展示 inline 技能加载，fork 涉及子 Agent（s06 概念）更复杂，留给进阶。

