# LCC s01 考点与自测

> 学完一章后用：先看「知识点」回顾，再答「自测题」，答完展开「参考答案」对答案。跨章累积、复习用。

## 一、知识点 / 考点

1. **解决的问题**：模型能产出命令但不会自己执行、看不到结果、不能继续推理；手动跑命令 + 粘贴结果回去 = 把人当中间层。自动化这个来回 = agent loop。
2. **循环的两个信号**：`stop_reason == "tool_use"` → 执行工具 → 结果喂回 → 继续；`stop_reason != "tool_use"` → 退出循环。
3. **5 步流程**：①用户问题入 `messages` ②`messages` + `tools` 一起发给 LLM ③追加 assistant 回答，没调工具就 `return` ④遍历 `response.content` 执行 `tool_use` block、收 `tool_result` ⑤`tool_result` 作为新 `user` 消息追加，回 ②。
4. **角色分工**：模型管决策（要不要调、调哪个、参数填啥），harness 管执行（跑命令、把结果喂回去）。harness 不是智能本身，是让智能能持续行动的最小框架。
5. **content 是 block 列表**：`text` block 和 `tool_use` block 混在一起；`tool_use` block 带 `name` / `id` / `input`。
6. **tool_result 三要素 + role**：`type="tool_result"`、`tool_use_id`（关联对应 tool_use）、`content`（执行输出）；以 **`role:"user"`** 追加（环境反馈对模型而言是"输入"，不是 assistant 输出）。
7. **tool_use_id 的意义**：一次循环模型可能调多个工具，回填时靠 id 把每条结果对应到正确的 tool_use，模型才知道哪条结果回答的是哪次调用。
8. **安全**：bash 工具执行模型生成的 shell 命令，应在临时目录跑（s01 用 sandbox）；真正的权限系统在 **s03**。
9. **CC 源码对比（进阶）**：教学版靠 `stop_reason` 判断；CC 用 `needsFollowUp` 标志（流式时 `stop_reason` 不可靠，改成"检测到 tool_use 块就继续"）。教学版 1 条退出路径，生产版多条（blocking limit / prompt too long / model error / max turns / token budget continuation / reactive compact retry 等）。1729 行 `query.ts` 的核心就是这 30 行 `while True`，其余都是保护机制。

## 二、自测题

1. （理解）s01 的 agent loop 自动化的是原来要人手动做的哪件具体的事？
2. （代码）循环靠 `response` 的哪个字段决定继续还是退出？两种情况分别做什么？
3. （细节）`tool_result` 为什么要带 `tool_use_id`？假如一次循环模型调了两个工具、回填时不带 id，会怎样？
4. （陷阱）`tool_result` 作为什么 role 的消息追加？为什么不是 assistant？
5. （设计）"模型负责决策、harness 负责执行"——能不能反过来让 harness 决策、模型只执行？为什么 LCC 开篇批判这种做法？
6. （进阶）教学版看 `stop_reason` 判断要不要继续，CC 为什么不直接这么干？它用什么替代？

<details>
<summary>参考答案（先自己答完再展开）</summary>

1. 把模型输出的命令手动跑一遍、把输出粘贴回对话框让它继续——这个"中间层"来回。loop 自动执行命令 + 把结果喂回模型，省掉人。
2. `response.stop_reason`。`"tool_use"` → 执行工具 → 结果喂回 → 继续循环；非 `"tool_use"` → `return` 退出循环。
3. 一次循环可能有多个 `tool_use` block，回填时 id 用来把每条 `tool_result` 对应到正确的 `tool_use`，模型靠 id 知道哪条结果回答的是哪次调用。不带 id 模型无法对应，结果错位、推理崩。
4. `role:"user"`。tool_result 是"给模型的输入"（环境对模型的反馈），和 user 消息一样是喂给模型的信息；assistant 角色是模型自己的输出，结果不是模型产出的。
5. 不能。agency（感知 + 推理 + 决策）是模型训练出来的能力；harness 是死代码，没有判断力。让 harness 用 if-else 决策 = LCC 开篇批判的"提示词水管工"，脆弱、不可泛化。
6. 流式响应里 `stop_reason` 可能还没更新，但内容里已经有 `tool_use` 块了，不可靠。CC 用 `needsFollowUp` 标志：流式接收时只要检测到 `tool_use` 块就置 true，靠它决定是否继续。

</details>
