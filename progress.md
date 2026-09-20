# 学习进度

更新：2026-09-20。

## 已确认的学习约束

- 每天可安排 4 小时。
- D01～D32 的快速知识学习已读完正文，每章以助记卡片和自测题收尾；D33 起进入推理工程实战，增加可复现实验、原始结果和验收记录。
- 先从整体介绍大模型涉及的环节与流程，再补基础；每章完成整体知识脉络的一块拼图，随后深入。
- 后续学习资料由助手生成并沉淀在本目录。
- 学习正文须脱离视频、输入摘要和聊天记录独立阅读，直接讲解知识，不包含来源纠错或待确认名称说明；三份补充讲义已按此要求修订，名称疑点移至[制作记录](standards/supplement-editorial-notes.md)。
- 有 3 年 C++ 和 JavaScript 开发经验，具备通用编码基础；非必要的编码知识不进入学习资料。
- Python/PyTorch 的特殊用法只按实验需要简述；用户略懂数学，涉及梯度等概念时优先直接给出规范数学推导。D33 已只读检测当前主机：无 NVIDIA GPU，后续 GPU 实验环境尚未最终确认。
- 正文以问题和因果承接展开；新概念按“已有问题 → 旧方法不足 → 所需机制 → 概念名称”自然引入，避免先抛术语再补定义。用户反馈初版冗余且张量引入突兀；学习安排与验收矩阵移至附页。
- 排版采用连贯段落，减少冗余换行；重点加粗，复杂关系配图。公式使用 Markdown 原生可读的 Unicode 写法，不依赖 LaTeX 渲染；助记卡使用原生 Markdown，不使用 HTML 折叠标签。变量在首次使用处就近解释，只有符号很多且反复使用时才列符号表；公式变形前说明目的。D01 第 4 节已加入逐行计算图。

## 当前状态

| 项目 | 资料准备 | 学习状态 | 证据 |
| --- | --- | --- | --- |
| 写作规范、教学方法、课时模板 | 已建立 | 不适用 | standards/ 与 templates/ |
| 学习路线 | 已建立 | 尚未开始记录 | roadmap.md |
| 整体知识地图 | 已扩展至 D01～D32，包含大模型全貌与推理工程原理逐章脉络 | 作为持续导航，不单独判定掌握 | [知识地图](knowledge-map.md) |
| D01：大模型内部究竟在计算什么 | 快速版已生成；已澄清矩阵与形状，并在回顾审查中移除未展开的提前术语和失效的折叠提示 | 用户已读完正文；卡片表述反馈已处理，自测未提交，未验收 | [讲义](courses/00-foundations/d01-tensors/README.md)、[自测答案](courses/00-foundations/d01-tensors/quiz-answers.md) |
| D02：参数怎样从数据中学出来 | 正文、图示、8 张卡片与 7 道自测及答案已生成；已补齐 D01 的 y 到 D02 的 ŷ/y 符号转换，第三节采用原生 Markdown 数学推导 | 用户正在阅读第三节；已确认略懂数学，希望直接阅读数学推导；理解情况与自测待反馈 | [讲义](courses/00-foundations/d02-learning/README.md)、[答案](courses/00-foundations/d02-learning/quiz-answers.md) |
| D03：怎样判断模型有没有学好 | 正文、图示、8 张卡片与 7 道自测及答案已生成；变量就近解释，交叉熵、泛化及评估风险均由已有问题自然引出 | 用户正在阅读；第三、四节反馈已处理，理解情况与自测待反馈 | [讲义](courses/00-foundations/d03-probability-generalization/README.md)、[答案](courses/00-foundations/d03-probability-generalization/quiz-answers.md) |
| D04：文字怎样变成模型的输入 | 正文、两张流程图、8 张卡片与 7 道自测及答案已生成 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d04-text-input/README.md)、[答案](courses/01-llm-overview/d04-text-input/quiz-answers.md) |
| D05：模型怎样结合上下文处理信息 | 正文、五张机制图、11 张卡片与 8 道自测及答案已生成；已根据反馈补充 Transformer 全貌、Q/K/V 的端到端训练，以及 FFN、残差连接和 LayerNorm 的机制 | 用户已阅读初版并反馈上述概念晦涩；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d05-attention-transformer/README.md)、[答案](courses/01-llm-overview/d05-attention-transformer/quiz-answers.md) |
| D06：模型怎样一个接一个生成 Token | 正文、四张流程图、9 张卡片与 8 道自测及答案已生成 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d06-autoregressive-generation/README.md)、[答案](courses/01-llm-overview/d06-autoregressive-generation/quiz-answers.md) |
| D07：基础模型的能力从哪里来 | 正文、四张机制图、9 张卡片与 8 道自测及答案已生成；已根据“晦涩难懂”的反馈改为从单次预测、训练步到规律沉淀的连续例子 | 用户已阅读初版；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d07-pretraining/README.md)、[答案](courses/01-llm-overview/d07-pretraining/quiz-answers.md) |
| D08：怎样让模型更适合指令和任务 | 正文、五张机制图、9 张卡片与 8 道自测及答案已生成；已根据“晦涩难懂”的反馈拆分训练阶段与参数更新方式，并简化 LoRA 解释 | 用户已阅读初版；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d08-post-training/README.md)、[答案](courses/01-llm-overview/d08-post-training/quiz-answers.md) |
| D09：不改参数，怎样影响这一次回答 | 正文、三张机制图、9 张卡片与 8 道自测及答案已生成；已根据审查统一总结示例、澄清 Prompt/Context 边界并修正窗口超限表述 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d09-prompt-context/README.md)、[答案](courses/01-llm-overview/d09-prompt-context/quiz-answers.md) |
| D10：怎样从大量资料中找到相关内容 | 正文、四张机制图、9 张卡片与 8 道自测及答案已生成；生成后已按完整清单自审 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d10-retrieval/README.md)、[答案](courses/01-llm-overview/d10-retrieval/quiz-answers.md) |
| D11：检索到资料后，模型怎样生成答案 | 正文、两张机制图、7 张卡片与 7 道自测及答案已生成；已根据重复性审查合并可靠性边界、压缩 D09/D10 回顾并重组错误定位链 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d11-rag/README.md)、[答案](courses/01-llm-overview/d11-rag/quiz-answers.md) |
| D12：模型怎样使用外部工具完成动作 | 正文、三张机制图、8 张卡片与 7 道自测及答案已生成；生成后已按完整清单审查并修订 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d12-tool-calling/README.md)、[答案](courses/01-llm-overview/d12-tool-calling/quiz-answers.md) |
| D13：多步骤任务怎样组织和停止 | 正文、三张机制图、8 张卡片与 7 道自测及答案已生成；生成后已按完整清单审查并修订 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d13-agent-workflow/README.md)、[答案](courses/01-llm-overview/d13-agent-workflow/quiz-answers.md) |
| D14：模型推理为什么占显存，响应为什么会变慢 | 正文、三张机制图、8 张卡片与 7 道自测及答案已生成；已根据反馈补充 Query/Key/Value 的职责、无缓存与有缓存的对比，以及从 Prompt 首个 Token 经多层网络逐步生成到 EOS 的全流程图 | 用户反馈第 2 节不易理解；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d14-inference-memory/README.md)、[答案](courses/01-llm-overview/d14-inference-memory/quiz-answers.md) |
| D15：推理引擎怎样让更多请求更快完成 | 正文、五张机制图、8 张卡片与 7 道自测及答案已生成；已根据反馈补充量化推导，并将慢请求优化改为“拆分耗时—定位瓶颈—选择旋钮”的诊断流程 | 用户反馈量化概念引入突兀且第 7 节难懂；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d15-serving-engine/README.md)、[答案](courses/01-llm-overview/d15-serving-engine/quiz-answers.md) |
| D16：怎样知道回答和服务真的变好了 | 正文、三张机制图、8 张卡片与 8 道自测及答案已生成；重复性审查后不再重讲 D15 指标定义，改为强调公平测试条件与分位数 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d16-evaluation/README.md)、[答案](courses/01-llm-overview/d16-evaluation/quiz-answers.md) |
| D17：遇到问题时，应该改模型还是改系统 | 正文、四张机制图、8 张卡片与 8 道自测及答案已生成；重复性审查后将定义型卡片改为跨层场景判断 | 用户已反馈学习完正文；自测尚未提交，未验收 | [讲义](courses/01-llm-overview/d17-system-diagnosis/README.md)、[答案](courses/01-llm-overview/d17-system-diagnosis/quiz-answers.md) |
| D01～D17 阶段总结 | 跨章总结、六张关系图、10 张阶段卡片、10 道阶段自测及答案已生成；以请假制度场景串起模型与系统两条时间线 | 尚未收到阅读或作答反馈，未验收 | [总结](courses/01-llm-overview/stage-summary/README.md)、[答案](courses/01-llm-overview/stage-summary/quiz-answers.md) |
| D18～D22：GPU 与性能判断 | 5 章正文、图示、36 张卡片、31 道自测及答案已生成；D18 已用 2×2 矩阵重写 GPU、算子与 Kernel，D20 第 2 节已用“计算上限—数据供给上限”及单位消除过程重写 Roofline，D21 已加入 Qwen2.5-7B-Instruct 的 BF16 权重、KV Cache 与 24 GiB 显存预算算例 | 用户已读完本阶段正文；期间提出的 D18、D20、D21 疑问已修订或解答，自测尚未提交，未验收 | [阶段入口](courses/02-inference/README.md) |
| D23～D27：单卡优化机制 | 5 章正文、图示、35 张卡片、30 道自测及答案已生成；第二轮审查已补全缩放点积公式并复核五种优化的作用边界 | 用户已读完本阶段正文；自测尚未提交，未验收 | [阶段入口](courses/02-inference/README.md) |
| D28～D32：引擎调度与选型 | 5 章正文、图示、36 张卡片、31 道自测及答案已生成；第二轮审查已移除答案中的未定义缩写，D32 易变能力已按 2026-09-16 官方文档核对 | 用户已读完本阶段正文；自测尚未提交，未验收 | [阶段入口](courses/02-inference/README.md) |
| 训练流程与 Agentic AI 补充 | 已基于视频摘要生成补充讲解、7 张卡片、6 道自测及答案；已区分 RLHF、DPO、GRPO、轨迹 SFT 与 Agent 强化学习，并记录 RETO / TestR-One 名称待核实；根据“概念枯燥、内容重复”的反馈，以出差助手为连续情境完成两轮修订，保留开头四版本导航表，删除正文复述和重复总结，并用四问法收束 | 尚未收到阅读或作答反馈，未验收 | [讲解](supplements/training-to-agentic-ai/README.md)、[答案](supplements/training-to-agentic-ai/quiz-answers.md) |
| 大模型训练数据补充 | 已基于视频摘要生成补充讲解、10 张卡片、8 道自测及答案；已区分语料、预训练、SFT、偏好、RL 与蒸馏数据，补充自动化采集、书籍 OCR、数据处理、配比、参数量与 Token 量、规模单位和污染控制，并说明整本书如何按训练上下文切分、拼接和分批训练；已记录 ReCoMix、MySQL 模型等名称待核实 | 用户正在阅读；已提出数据单位、互联网采集、书籍转换和整本书输入方式等问题，并指出首节概念分类引入突兀；相关解释和章节过渡已补入正文，后续理解情况待反馈，未验收 | [讲解](supplements/llm-training-data/README.md)、[答案](supplements/llm-training-data/quiz-answers.md) |
| 大模型推理控制补充 | 已基于视频摘要重新组织并生成补充讲解、9 张卡片、8 道自测及答案；沿一次请求区分上下文控制、Prefill/Decode、生成控制、连续批处理、KV Cache、量化与 Test-Time Scaling，并记录 IAG、WQ 名称待原视频确认 | 尚未收到阅读或作答反馈，未验收 | [讲解](supplements/llm-inference-control/README.md)、[答案](supplements/llm-inference-control/quiz-answers.md) |
| D33：实验环境是否满足推理要求 | 正文、两张图、7 张卡片、7 道自测及答案、环境盘点任务、采集脚本和当前主机报告已生成 | 尚未开始学习；当前主机已由助手只读盘点，环境路线等待用户确认 | [讲义](courses/03-inference-practice/d33-environment/README.md)、[任务](courses/03-inference-practice/d33-environment/lab.md) |
| D34～D47：推理工程实战 | 已完成 14 章课程规划，覆盖模型基线、服务、压测、诊断、优化、多卡、可靠性和综合交付；具体讲义与实验尚未生成 | 尚未开始 | [实战规划](courses/03-inference-practice/README.md) |

生成讲义不等于完成学习。只有用户反馈或作答结果支持时才更新完成情况；运行示例成功也不直接代表已理解。

## 后续学习记录格式

| 日期 / 课时 | 实际用时 | 独立完成的任务 | 尚未掌握的问题 | 证据文件 | 复习安排 |
| --- | --- | --- | --- | --- | --- |

已创建 [D01 学习记录模板](notes/d01.md)，原内容保留。现在可直接在聊天中回答章末自测，不要求填旧实验栏目；卡片及资料已生成不等于已掌握。
