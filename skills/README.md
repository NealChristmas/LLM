# 学习资料 Skills

本目录保存课程资料制作过程中使用的Codex Skill 源码，便于版本管理、审查和在其他环境中复用。仓库内副本不表示已经自动安装；需要使用时，将对应目录放入 Codex 的 skills 目录。

- [learning-material-writing](learning-material-writing/SKILL.md)：编写中文技术学习资料，控制概念引入、推理链、公式、图示和练习闭环。
- [learning-material-review](learning-material-review/SKILL.md)：审查正确性、教学连贯性、跨章重复、认知负荷、练习一致性与 Markdown 格式。

写作流程先生成正文、卡片和自测，随后调用审查流程复核；审查中的机械检查脚本只提供线索，不能替代人工判断。

## 视频分析与图文教程

- [bilibili-analyzer](bilibili-analyzer/SKILL.md)：连续抽帧与完整字幕联合分析，保留来源、分 P 身份检查及时间证据；支持字幕缓存和 SRT 导入。
- [video-textbook-writer](video-textbook-writer/SKILL.md)：将已有视频证据写成可独立学习的 Markdown 教程，用贯穿例子和机制图补足推理。

这两套技能可依次使用：先分析，再写作。视频教程写作不默认叠加课程资料的助记卡片、自测题或学习计划。
