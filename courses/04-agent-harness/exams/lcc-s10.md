# LCC s10 考点与自测

## 一、知识点 / 考点

### 1. 动机：TodoWrite 不够用

- TodoWrite 是"当前任务"的执行清单，存在进程内存里，关了就没了
- 真实项目有多个任务、有依赖关系（A 做完 B 才能做）、有认领需求（谁做哪个）
- Task System 解决：**跨会话持久化**、**依赖图**、**任务认领**三个问题

### 2. 核心数据结构

- 每个任务 = 一个 JSON 文件，存于 `.tasks/{id}.json`
- Task 字段：`id`（`task_` + 8 位随机 hex）、`subject`、`description`、`status`（pending/in_progress/completed）、`owner`、`blockedBy`
- 磁盘本身就是真相源，不需要数据库、不需要缓存

### 3. 两阶段构建

- **问题**：`create_task` 的 ID 是运行时随机生成的，Agent 调用前不知道 ID
- **阶段一**：先 `create_task` 创建所有节点，拿到返回的 ID
- **阶段二**：再用 `update_task` + 返回的 ID 添加依赖边
- SYSTEM prompt 明确指令 LLM 按这个顺序

### 4. 依赖检查与环检测

- `can_start(task_id)`：检查 `blockedBy` 里所有任务是否都是 completed
- `_depends_on(task_id, target_id)`：传递闭包，沿 `blockedBy` 链向上追溯，检测环
- 环检测阻止 A→B→C→A 的死锁

### 5. 任务生命周期

- `pending` —创建→ `pending(有依赖)` —依赖满足→ `claim_task` → `in_progress` —`complete_task` → `completed`
- 状态机两个动作：`claim`（pending→in_progress，设置 owner）和 `complete`（in_progress→completed，解锁下游）

### 6. 解锁机制

- `complete_task` 用 `ready_before` 差集：记录完成前已可认领的任务，完成后只通知"新解锁的"
- 不重复通知本来就解锁的任务

### 7. TaskStore 安全设计

- ID 格式校验：`task_[0-9a-f]{8}`，拒绝路径注入
- `open("x")` 独占创建：防 ID 碰撞，碰撞自动重试（最多 100 次）
- `secrets.token_hex(4)`：密码学安全随机，非时间戳

### 8. TodoWrite vs Task System

| | TodoWrite | Task System |
|---|---|---|
| 定位 | 当前任务执行清单 | 可恢复的任务系统 |
| 存储 | 进程内存 | `.tasks/{id}.json` |
| 依赖 | 无 | `blockedBy` DAG + 环检测 |
| 认领 | 无 | `owner` + `claim_task` |
| 关系 | 不替代，可共存 | — |

### 9. 与 LangGraph 的区别

- LangGraph：流程编排引擎（节点是计算步骤，边是控制流）
- Task System：项目看板（节点是任务卡片，边是依赖关系）
- 两者层级不同，不冲突，可同时使用

## 二、自测题

1. （动机）TodoWrite 已经有了任务列表，为什么还要 Task System？两者各自解决什么问题？
2. （两阶段）为什么 `create_task` 和 `update_task` 要分成两个阶段？不能在一个 tool call 里同时创建并设置依赖吗？
3. （环检测）`_depends_on` 为什么需要传递闭包？如果只检查直接依赖不检查传递依赖，会有什么问题？
4. （解锁）`complete_task` 里 `ready_before` 差集的作用是什么？如果去掉差集，直接返回所有 can_start 的任务会怎样？
5. （安全）TaskStore 的 `_path` 方法做了哪些安全校验？各自防什么攻击？
6. （设计）Task System 为什么选 JSON 文件持久化，而不是用 SQLite 或内存+定期落盘？说说各自的优劣。

完成后查看[参考答案](answers/lcc-s10.md)。


