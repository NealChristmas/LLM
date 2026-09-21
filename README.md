# 大模型学习资料库

这里保存后续生成的大模型学习资料、示例代码、练习与复盘。学习顺序是：整体知识地图 → 最小深度学习基础 → 逐章补全大模型脉络；主线随后进入推理工程，也可以从 D12/D13 分出 Agent Harness 工程支线，并按兴趣继续深入平台或底层性能。

已确认每天可安排 4 小时，有 3 年 C++ 和 JavaScript 开发经验。D01～D32 采用 **正文与图示 → 助记卡片 → 自测题**；后续进入 D33～D47 推理工程实战，实验阶段增加可复现实验、原始结果与验收记录。

## 入口

- [补充：Ollama 怎样在 CPU 上完成一次大模型推理？](supplements/ollama-cpu-inference/README.md)：沿请求进入、N 层 Transformer、CPU 线程与向量 Kernel 串起 Prefill、KV Cache 和逐 Token Decode。
- [昇腾专项：一套 AI 任务怎样从模型落到行业系统？](supplements/ascend-special-topic/README.md)：沿硬件产品形态、CANN 基础软件、训推框架、MindStudio 工具链和行业使能建立昇腾全栈地图；官方版本信息核对至 2026-09-21。
- [补充：同一个模型，为什么能答得更好或运行得更快？](supplements/llm-inference-control/README.md)：沿一次请求串起上下文、Prefill/Decode、生成控制、连续批处理、KV Cache、量化与 Test-Time Scaling，并区分质量、延迟、吞吐、显存和成本。
- [补充：一份资料，怎样变成大模型真正能学习的数据？](supplements/llm-training-data/README.md)：区分语料、预训练数据、SFT、偏好、RL 与蒸馏数据，串起清洗、去重、配比、数据单位和污染控制。
- [补充：同一个出差助手，是怎样一步步训练出来的？](supplements/training-to-agentic-ai/README.md)：沿同一出差任务串起下一 Token 预测、SFT、RLHF、DPO、GRPO、轨迹训练与 Agent 系统边界。
- [MoE 推理专题：为什么参数很多，却只计算一部分？](courses/02-inference/moe-special-topic/README.md)：补齐专家路由、总参数与激活参数、显存估算和多卡通信，再进入实战。
- [推理实战入口 D33：环境能否完成推理实战？](courses/03-inference-practice/d33-environment/README.md)：解释硬件与软件栈，记录当前主机环境，并选择本机或云端路线。
- [D33～D47 推理工程实战规划](courses/03-inference-practice/README.md)：环境与基线 → 服务与压测 → 单项优化 → 多卡、可靠性与综合交付。
- [Agent Harness 工程学习入口](courses/04-agent-harness/README.md)：从旧项目继承 Learn Claude Code 17 章讲义、代码、图示和 s01～s10 自测；旧日志记录 s01～s10 已学习，掌握情况待复核，下一章为 s11 Background Tasks。
- [D18～D32 推理工程原理课程](courses/02-inference/README.md)：GPU 与性能判断 → 单卡优化机制 → 引擎调度与选型；已读完正文，可按需返回具体章节复习或完成自测。
- [D13：多步骤任务怎样组织和停止？](courses/01-llm-overview/d13-agent-workflow/README.md)：区分工作流与 Agent，串起状态、反馈、循环和停止条件。
- [D14：模型推理为什么占显存，响应为什么会变慢？](courses/01-llm-overview/d14-inference-memory/README.md)：串起权重、KV Cache、GPU、Prefill 与 Decode。
- [D15：推理引擎怎样让更多请求更快完成？](courses/01-llm-overview/d15-serving-engine/README.md)：串起连续批处理、PagedAttention、前缀缓存、量化、延迟与吞吐。
- [D16：怎样知道回答和服务真的变好了？](courses/01-llm-overview/d16-evaluation/README.md)：串起评测集、评分标准、组件评测、性能指标、对照与回归。
- [D17：遇到问题时，应该改模型还是改系统？](courses/01-llm-overview/d17-system-diagnosis/README.md)：用全栈诊断图完成 D01～D17 的方案选择与知识收束。
- [D01～D17 阶段总结](courses/01-llm-overview/stage-summary/README.md)：用一条完整系统链串起训练、生成、RAG、工具、Agent、推理服务与评测，并附阶段自测。
- [D11：检索到资料后，模型怎样生成答案？](courses/01-llm-overview/d11-rag/README.md)：串起 RAG 请求、上下文组装、证据引用、分层诊断与方案选择。
- [D10：怎样从大量资料中找到相关内容？](courses/01-llm-overview/d10-retrieval/README.md)：串起文档切分、检索向量、相似度、索引、召回、重排与混合检索。
- [D09：不改参数，怎样影响这一次回答？](courses/01-llm-overview/d09-prompt-context/README.md)：串起提示词、少样本示例、消息与历史、上下文窗口及方案边界。
- [D08：怎样让模型更适合指令和任务？](courses/01-llm-overview/d08-post-training/README.md)：区分 SFT、RLHF、DPO、全量微调与 LoRA，建立训练信号和参数更新方式两条轴。
- [D07：基础模型的能力从哪里来？](courses/01-llm-overview/d07-pretraining/README.md)：串起训练数据、自监督目标、训练循环、能力形成与基础模型边界。
- [D06：模型怎样一个接一个生成 Token？](courses/01-llm-overview/d06-autoregressive-generation/README.md)：串起因果遮罩、输出概率、贪心与采样、自回归循环和停止条件。
- [D05：模型怎样结合上下文处理信息？](courses/01-llm-overview/d05-attention-transformer/README.md)：Transformer、Q/K/V 训练、Attention、FFN、残差连接与 LayerNorm；修订版理解情况待反馈。
- [D04：文字怎样变成模型的输入？](courses/01-llm-overview/d04-text-input/README.md)：串起 Token、Token ID、Embedding 与位置信息；资料已生成，学习反馈待确认。
- [D03：怎样判断模型有没有学好？](courses/00-foundations/d03-probability-generalization/README.md)：串起 Logit、Softmax、交叉熵、数据划分与泛化；正在阅读，理解情况与自测待反馈。
- [D02：参数怎样从数据中学出来？](courses/00-foundations/d02-learning/README.md)：沿用 D01 的例子串起损失、梯度、反向传播与更新；阅读已开始，自测尚未提交。
- [大模型知识脉络图](knowledge-map.md)：大模型全貌与推理工程原理的课程顺序、系统流程和逐章问题。
- [开始 D01](courses/00-foundations/d01-tensors/README.md)：重写版“大模型内部究竟在计算什么”，直接从开篇顺序阅读。
- D01 助记卡片与自测题已放在正文末尾；[参考答案](courses/00-foundations/d01-tensors/quiz-answers.md)单独查看。
- [D01 学习安排](courses/00-foundations/d01-tensors/study-guide.md)及[学习记录](notes/d01.md)：按实际阅读与答题进展使用。
- [D01 课程大纲](courses/00-foundations/d01-tensors/outline.md)：保留课程设计供回顾。
- [学习路线](roadmap.md)：D01～D17 为全貌速成，D18～D32 为推理工程原理，按理解情况调整。
- [学习进度](progress.md)：区分资料准备、实际学习和掌握情况。
- [资料制作规范](standards/material-guide.md)：写作、教学、代码与质量要求。
- [参考依据](standards/sources.md)：已查阅的写作与教学设计资料及采用方式。
- [课时模板](templates/lesson-template.md)：后续讲义的通用结构。
- [学习资料 Skills](skills/README.md)：写作与质量审查 Skill 的可版本管理源码。
- [本目录协作约定](AGENTS.md)：让后续在该目录中的工作延续已确认的偏好。

## 后续资料组织

课时按需生成，不预先填充空白课程。新增时采用以下路径规则：

| 路径规则 | 内容 |
| --- | --- |
| courses/00-foundations/d01-tensors/ | 深度学习基础课时 |
| courses/01-llm-overview/d04-text-input/ | 大模型结构与生成课时 |
| courses/02-inference/ | 后续推理工程课程 |
| courses/03-inference-practice/ | D33～D47 推理部署、压测、优化与交付实战 |
| courses/04-agent-harness/ | 从旧项目继承的 Learn Claude Code 17 章 Agent Harness 工程课程、代码、自测与进度 |
| supplements/ascend-special-topic/ | 昇腾硬件、CANN、训推框架、MindStudio 与行业应用专项 |
| 每课 README.md | 连贯讲解、必要图示、章末助记卡片和自测题 |
| 每课 quiz-answers.md | 当前快速学习自测答案 |
| 每课 assets/ | 本地图示 |
| 既有 code/、lab/、practice.md、exercises.md、solutions.md | 历史实操资料，当前不要求完成 |
| notes/ | 用户作答、复盘、错题与问题记录 |

文档内部使用相对链接便于移动目录；聊天交付使用绝对路径链接。所有学习必需内容在本地讲义中讲清楚，外部资料用于溯源或选读。
