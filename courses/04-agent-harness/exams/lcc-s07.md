# LCC s07 考点与自测

## 一、知识点 / 考点

1. **动机**：项目有 React 规范/SQL 风格/API 文档，全塞进 system prompt → 6500 行。Agent 每次调 LLM 都带着，改 CSS 颜色也带 SQL 文档，99% 无关，白耗 token，还稀释 system prompt 影响力。
2. **核心方案：两层设计**：
   - **第一级：目录** 在 system prompt，启动时注入（harness 扫 `skills/`），~100 tokens/skill，每轮都带——Agent 知道"有哪些技能可用"
   - **第二级：内容** 在 tool_result，Agent 调 `load_skill` 时注入，~2000 tokens/skill，按需——用到才花 token
3. **工作原理**：`skills/` 目录每个技能一个子目录含 `SKILL.md`；启动时 `_scan_skills()` 扫描、解析 YAML frontmatter（`name`/`description`）、存入 `SKILL_REGISTRY`；`list_skills()` 从注册表生成目录注入 SYSTEM；`load_skill(name)` 通过注册表查找返回 SKILL.md 内容。
4. **关键区别**：技能内容**不是 system prompt 的一部分**，而是作为一次 **tool_result** 进入当前 messages，随历史携带直到压缩/截断/会话结束。和 s08 compact 自然衔接：按需加载解决"不该提前带的不要带"，compact 解决"该丢的怎么丢"。
5. **安全**：`load_skill` 通过 `SKILL_REGISTRY` 查找（模型只给技能名，不给文件路径），无路径遍历风险。
6. **dispatch 不变**：`load_skill` 走 `TOOL_HANDLERS` 分发。
7. **相对 s06**：工具 7→8（+load_skill）；SYSTEM 静态字符串 → 启动时扫描 `skills/` 注入目录；新增 `SKILL_REGISTRY`。
8. **CC 对比（进阶）**：
   - 技能来源不止 `skills/`：从 user/project/`--add-dir`、legacy commands、bundled skills、MCP skills 等多来源加载。
   - frontmatter 字段更多：`name`/`description`/`when_to_use`/`allowed-tools`/`context`（`inline` 默认或 `fork` 作为子 Agent）/`model`/`hooks`/`paths`（条件激活 glob）/`user-invocable`。
   - 两级精确实现：Catalog（注册为 Command 对象只含元数据，格式化为附件，预算 ~1% 上下文窗口，上限 8000 字符）；Load（模型调 Skill 工具输入 `skill`+可选 `args`，`SkillTool` 返回的 tool_result 展示文本只是 `"Launching skill: {name}"`，真正内容通过 `newMessages` 注入）。
   - 教学版简化：多来源→1 目录；多字段→只 name/description；`context:fork` 省略；Skill 工具输入 `skill`+`args`→用 `name`。

## 二、自测题

1. （动机）把 React/SQL/API 三份规范全塞进 system prompt 有什么问题？
2. （两层设计）s07 的两级加载分别是什么？各花多少 token、什么时候花？
3. （机制）Agent 怎么知道"我有哪些技能"？`load_skill` 的内容通过什么方式进入对话——system prompt 还是 tool_result？
4. （安全）`load_skill` 为什么通过 `SKILL_REGISTRY` 查找而不是让模型给文件路径？避免了什么风险？
5. （衔接）按需加载和 s08 compact 各解决什么问题？怎么配合？
6. （CC对比）CC 的 SKILL.md frontmatter 里 `context: fork` 是什么意思？教学版为什么省略？

完成后查看[参考答案](answers/lcc-s07.md)。


