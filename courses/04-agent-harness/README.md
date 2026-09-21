# Agent Harness 工程学习入口

这条课程从旧项目 `ai-agent-lab` 继承，核心材料是 **Learn Claude Code（LCC）17 章新版教程**。它不重新讲一套抽象的 Agent 架构，而是沿同一个可运行的 Agent Loop，逐章加入工具、权限、Hook、任务、上下文压缩、记忆、后台执行、团队、MCP、工作流和目标闭环。

旧项目的进度日志记录：**s01～s10 已学习，s11 尚未开始。** 当前项目继承这个进度，但不把“学过”自动写成“已掌握”：旧资料保存了逐章自测题和参考答案，没有保存独立作答、得分或本项目中的复运行结果。因此下一步从 [s11：后台任务](learn-claude-code/s11_background_tasks/README.zh.md)继续；需要复习时再按[继承进度](progress.md)中的链接定向回看。

## 这条课程怎样接到现有知识上

当前项目的 D01～D32 负责建立模型、上下文、工具调用、Agent 和推理服务的整体认识；LCC 则把其中的 Agent 部分落到 Harness 代码。两者不是从头再学一次，而是下面这种关系：

| 已有课程 | LCC 中继续深入的章节 | 新增的工程视角 |
| --- | --- | --- |
| [D09：提示词与上下文](../01-llm-overview/d09-prompt-context/README.md) | s07～s09 | 技能按需加载、上下文压缩、跨会话记忆 |
| [D12：工具调用](../01-llm-overview/d12-tool-calling/README.md) | s01～s04、s14 | Agent Loop、工具分发、权限、Hook、MCP 工具接入 |
| [D13：Agent 与工作流](../01-llm-overview/d13-agent-workflow/README.md) | s05、s06、s10～s13、s15～s17 | 任务、子 Agent、后台与定时执行、团队、工作流恢复和目标闭环 |

LCC 的重点是 Harness 机制和代码，不系统覆盖 Agent 质量评测、生产观测、提示注入测试或行业任务设计。以后需要这些内容时，应在已有 Harness 基线上增加专项资料，而不是假定 17 章已经覆盖全部生产问题。

## 17 章路线与当前进度

课程版本固定为旧项目中的提交 `69c83c0e52969223821ad6c4a77ad5e6174ef8fe`，迁入日期为 2026-09-21。

| 阶段 | 章节 | 解决的问题 | 状态 |
| --- | --- | --- | --- |
| 最小循环 | s01 Agent Loop、s02 Tool Use | 模型怎样反复调用工具并取得结果 | 旧项目已学习 |
| 控制与扩展 | s03 Permission、s04 Hooks | 工具执行前怎样限制风险，循环怎样保持可扩展 | 旧项目已学习 |
| 复杂任务 | s05 TodoWrite、s06 Subagent、s07 Skill Loading | 怎样保留计划、隔离子任务并按需加载知识 | 旧项目已学习 |
| 上下文与持久状态 | s08 Context Compact、s09 Memory、s10 Task System | 长会话怎样压缩，信息怎样跨会话保存，任务怎样落盘 | 旧项目已学习 |
| 长时间运行 | [s11 Background Tasks](learn-claude-code/s11_background_tasks/README.zh.md)、[s12 Cron Scheduler](learn-claude-code/s12_cron_scheduler/README.zh.md) | 慢操作怎样不阻塞，任务怎样按时间触发 | **下一步从 s11 开始** |
| 协作 | [s13 Agent Teams](learn-claude-code/s13_agent_teams/README.zh.md) | 多个 Agent 怎样共享任务、通信并隔离工作目录 | 尚未开始 |
| 外部能力与集成 | [s14 MCP Plugin](learn-claude-code/s14_mcp_plugin/README.zh.md)、[s15 Integrated Harness](learn-claude-code/s15_integrated_harness/README.zh.md) | 外部工具怎样进入工具池，各机制怎样回到同一循环 | 尚未开始 |
| 确定性编排与结束判断 | [s16 Workflow Runtime](learn-claude-code/s16_workflow_runtime/README.zh.md)、[s17 Goal Loop](learn-claude-code/s17_goal_loop/README.zh.md) | 固定流程怎样续跑，系统怎样判断目标是否真正完成 | 尚未开始 |

## 资料怎样组织

- [继承进度](progress.md)：逐章状态、证据和下一步。
- [LCC 中文总览](learn-claude-code/README-zh.md)：上游对 17 章的完整介绍。
- `learn-claude-code/s01_*`～`s17_*`：上游讲义、代码和图示的固定快照。
- [s01～s10 继承自测](exams/README.md)：从旧项目迁入，并把折叠答案拆成独立页面。
- [迁移说明](migration-notes.md)：迁入范围、排除内容、版本与许可证。
- [运行器](run_lcc.py)：从当前目录选择章节，并把运行时文件限制在 `runtime-workspace/`。

上游讲义保持原貌，便于对照代码和继续同步；当前项目只在这一入口、进度页和自测导航中完成融合，不把旧的 20 章路线强行套到新的 17 章版本上。

## 继续学习 s11

s11 要解决的是一个很具体的问题：完整测试或安装过程持续几分钟时，同步工具调用会让 Agent Loop 一直等待。章节加入后台任务管理器，先返回任务标识，让循环继续处理其他工作；后续轮次再把完成结果作为独立通知注入。

建议按当前每天 4 小时的节奏完成：先读 [s11 中文讲义](learn-claude-code/s11_background_tasks/README.zh.md)，再对照 `code.py` 找到后台任务进入循环的位置。只有在准备好隔离环境和模型配置后才运行代码；完成后保留原始输出，再补 s11 自测与实际学习记录。

注意：LCC 示例会执行模型生成的 Shell 命令。`run_lcc.py` 会把当前工作目录切到 `runtime-workspace/`，但这只是降低误操作范围，不是操作系统级沙箱，也不能阻止绝对路径访问。不要在含生产数据、密钥或不可恢复文件的环境中运行。
