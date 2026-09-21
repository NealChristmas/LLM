# 学习进度日志

格式：每天学习结束前更新，写到 opencode 能直接读的程度（学了什么 / 产出 / 问题 / 明天计划）。新对话里问"今天学到哪了"，opencode 会读此文件。

---

## 2026-08-10（周一 · 环境与仓库收官）
- 完成 GitHub 仓库 `ai-agent-lab`（私有）创建与推送，25 个文件
- 仓库根目录 = `code\`：`roadmap/`（学习文档）+ `AGENTS.md` + `ai-agent-lab/`（实验代码区）
- `projects/learn-claude-code` 以 submodule 加入（指针 7b564c3）
- 装了 GitHub CLI（gh 2.97.0）、修了 git PATH 问题
- 问题：公司电脑尚未准备环境

## 2026-08-11（周二 · 公司机环境就绪 + 学习计划改版为 LCC 主线）
- 公司机按 AGENTS.md 清单配齐：git 仓库级身份、执行策略放宽、gh(待 auth login)、venv、.env(填 DashScope key)、Chromium、冒烟(alibaba/glm-5.2 三项全过)
- 修坑：`.env.example` 原缺默认必需的 ARK_API_KEY，已补；给 `llm.py` 加 alibaba provider + `LLM_PROVIDER` 切换，公司机走 DashScope/glm-5.2，家里仍走 ark
- 拉了 LCC 子仓 `projects/learn-claude-code`（7b564c3）
- **改学习方案**：先按 LCC 20 章逐章学，旧 9 周自研路线归档；`roadmap/README.md` 重写为 v2
- 协议：LCC 用 Anthropic 协议；实测发现**火山方舟 ARK 原生支持 Anthropic 端点**（`/api/plan`，工具调用正常），DashScope 没有。故 LCC 直连 ARK，不需要 adapter
- 子仓建 `.env`（ARK Anthropic 配置，被 .gitignore 忽略）；`run_lcc.py` 载它 + sandbox + 直连；`cc_adapter.py` 已删
- s01 已端到端跑通（直连 ARK，doubao 模型发起 bash 工具调用 `echo hello` 并回填，loop 正常）
- 明天：正式开始 LCC s01——读 README + 手写 `my_s01_agent_loop.py`

## 2026-08-12（周三 · LCC s01-s07 学完，s08 进行中）
- LCC s01-s05 学完，每章考点+自测题存档 `roadmap/exams/lcc-s01~s05.md`（opencode 出题+批改）
- s06 Subagent、s07 Skill Loading 学完，存档 `lcc-s06.md` / `lcc-s07.md`
- s08 Context Compact 没完全看懂，opencode 详细讲了：四层压缩（L1 snip 裁中间 / L2 micro 旧结果占位 / L3 budget 大结果落盘 / L4 LLM 摘要）+ 应急 reactive；执行顺序 budget→snip→micro→auto，**budget 必须在 micro 前**（防丢内容）
- s05 `code.py` 临时加了 `print(history)` 看数据流，子仓仍 modified（未提交，仅公司机本地）
- 下一步（家里）：继续 s08，看懂后做 s08 自测，再 s09

## 2026-08-13（周四 · s08 自测存档 + s09/s10/s12 讲解 + 简明教程 + 沙箱修正）
- s08 学完，考点+自测存档 `roadmap/exams/lcc-s08.md`
- s09 Memory / s10 System Prompt / s12 Task System 没完全看懂，opencode 逐章详细讲了（数据流+CC对比）；s06/s07 还带读了代码（整体注释）
- 写了 LCC 20 章简明教程 `roadmap/lcc-simple-guide.md`（每章 干啥/为啥/好处，建地图用）
- 修 `run_lcc.py` + `.vscode/launch.json`：cwd 从 sandbox 改到子仓根（s07 才能找到 `skills/`、s05 找到 `example/`）；launch 的 `justMyCode` 改 true（false 会插桩 httpx/httpcore 导致导入极慢、报 KeyboardInterrupt）
- s05/s07 `code.py` 临时加了 print(history) 看数据流，子仓仍 modified（未提交，仅公司机本地）
- 下一步（家里）：继续 s09/s10/s12（看懂后做自测），再 s11、s13+

## 2026-08-24（周一 · LCC 子仓更新 + s09 Memory 学完 + s10 Task System 学完）
- 子仓 `projects/learn-claude-code` 从 7b564c3 更新至 a32a73f（29 个新 commit），课程从 20 章重构为 17 章：s10 System Prompt / s11 Error Recovery 被砍，s12 Task System→s10，新增 s16 Workflow Runtime / s17 Goal Loop
- **s09 Memory 学完**：详细走读 code.py（655行），聚焦记忆系统数据流（两条路径 + 压缩前快照 + 浅拷贝注入），自测6题存档 `roadmap/exams/lcc-s09.md`
- **s10 Task System 学完**：按背景→原理→代码顺序讲解，核心：两阶段构建（先create拿ID再update加依赖）、环检测（传递闭包）、解锁差集（ready_before）、TaskStore安全设计（ID校验+独占创建）。自测6题存档 `roadmap/exams/lcc-s10.md`
- **规则落地**：AGENTS.md 写入讲解顺序规则（背景→原理→代码），后续学习资料统一遵守
- 环境：`opencode.json` 加入 .gitignore（含 API key）；`run_lcc.py`/`launch.json` 加 `PYTHONUTF8` 环境变量
- 子仓 5 个 code.py 的 debug print 已随子仓更新丢弃（无价值保留）
- 下一步：继续 s11 Background Tasks