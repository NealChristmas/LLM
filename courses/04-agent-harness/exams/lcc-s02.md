# LCC s02 考点与自测

## 一、知识点 / 考点

1. 动机：s01 只有 bash，读文件要 `cat`、写要 `echo >`，多一层翻译浪费 token 易错 → 给专用工具。
2. 核心变更：s01 循环完全保留；唯一改动是先用 `TOOL_HANDLERS[block.name]` 查表，再以 `**block.input` 传入参数。
3. 加一个工具 = 两件事：① `TOOLS` 数组加一条描述 ② `TOOL_HANDLERS` 字典加一行映射。循环不变。
4. 工具定义 = 告诉模型"我能做什么"的 JSON schema（`name`/`description`/`input_schema`）。`description` 让模型判断何时用。
5. 多工具调用：模型可一次返回多个 `tool_use`；教学版按 `response.content` 原始顺序逐个执行。
6. 路径安全：file tools 受 `safe_path` 校验，bash 不受限（`rm -rf /` 仍能跑）→ 留给 s03。
7. CC 对比（进阶）：每个工具是 `buildTool()` 对象；`isConcurrencySafe()` 按具体输入判断（不是简单只读 vs 写）；`partitionToolCalls()` 按连续块分批，batch 内并发、batch 间串行；5 步验证管线；`StreamingToolExecutor` 流式并行执行；结果超 `maxResultSizeChars` 落盘（FileRead 设 `Infinity` 防无限落盘循环）。

## 二、自测题

1. （动机）有了 bash 还要加 read_file/write_file 等专用工具，理由是什么？
2. （代码）s01→s02 循环里唯一改的是哪一行？改成什么？
3. （流程）加一个新工具要做哪两件事？循环要不要改？
4. （细节）模型一次返回多个 tool_use 时，教学版按什么顺序执行？CC 更优的做法是什么？
5. （安全）s02 的 file tools 受什么保护？bash 呢？这个缺口留给哪章？
6. （进阶）CC 的 `isConcurrencySafe` 是不是"只读=可并发"？举一个反例。

完成后查看[参考答案](answers/lcc-s02.md)。


