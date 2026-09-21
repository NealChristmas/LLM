# Learn Claude Code 迁移说明

## 来源与版本

- 旧项目：`C:\Users\朱春杰\Desktop\study\ai-agent-lab`
- 主要来源：`projects\learn-claude-code`
- 固定提交：`69c83c0e52969223821ad6c4a77ad5e6174ef8fe`
- 迁移日期：2026-09-21
- 许可证：MIT，版权声明与完整条款见 [LICENSE](learn-claude-code/LICENSE)

## 已迁入

- 当前 s01～s17 的多语言讲义、Python 代码、图示和章节示例。
- s07 与 s15 需要的 `skills/` 示例。
- 上游 README、依赖清单、示例环境变量和许可证。
- 旧项目 s01～s10 的逐章考点与自测；原始版本保存在 `history/exams-original/`，当前学习入口使用拆分后的题目与答案。
- 旧项目进度日志的只读副本，以及根据日志整理的[继承进度](progress.md)。

## 未迁入

- `.env`、API Key、虚拟环境、缓存和任何本机认证信息。
- `.memory/`、`.tasks/`、`.task_outputs/`、`.transcripts/` 等运行时产物。
- `web/` 生成站点及依赖，源目录约 416 MB，不是学习主线所需内容。
- `docs/` 与 `agents/` 中的旧 12 章兼容线，避免与当前 17 章编号混用。
- 旧项目 `roadmap/README.md` 和 `lcc-simple-guide.md` 的 20 章版本。这两份文件在上游改为 17 章后没有同步，直接迁入会把 s10～s20 的编号和主题教错。
- `deepseek-harness`、旧九周路线、求职规划和机器环境配置；它们不属于本次以 LCC 为主的融合范围。

## 融合原则

上游章节作为固定快照保存，不直接改写正文，以便继续对照原始代码和许可证。当前项目负责维护入口、与 D09/D12/D13 的知识衔接、继承进度、自测导航和后续实际学习记录。将来若更新上游版本，先比较章节编号、代码行为和迁移说明，再决定是否替换快照；不能只覆盖文件后继续沿用旧进度。

