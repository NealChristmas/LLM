# 大模型学习资料库

这里保存后续生成的大模型学习资料、示例代码、练习与复盘。学习顺序是：整体知识地图 → 最小深度学习基础 → 逐章补全大模型脉络 → 推理工程 → 按兴趣深入平台或性能优化。

已确认每天可安排 4 小时，有 3 年 C++ 和 JavaScript 开发经验。当前先快速理解大模型相关知识，采用 **正文与图示 → 助记卡片 → 自测题**，不做实验或编码。D01～D09 已生成正文、卡片、自测及答案；原有实验保留为后续深入资料。

## 入口

- [当前开始 D09：不改参数，怎样影响这一次回答？](courses/01-llm-overview/d09-prompt-context/README.md)：串起提示词、少样本示例、消息与历史、上下文窗口及方案边界；章末有 9 张助记卡和 8 道自测题，[答案另页](courses/01-llm-overview/d09-prompt-context/quiz-answers.md)。
- [D08：怎样让模型更适合指令和任务？](courses/01-llm-overview/d08-post-training/README.md)：区分 SFT、RLHF、DPO、全量微调与 LoRA，建立训练信号和参数更新方式两条轴。
- [D07：基础模型的能力从哪里来？](courses/01-llm-overview/d07-pretraining/README.md)：串起训练数据、自监督目标、训练循环、能力形成与基础模型边界。
- [D06：模型怎样一个接一个生成 Token？](courses/01-llm-overview/d06-autoregressive-generation/README.md)：串起因果遮罩、输出概率、贪心与采样、自回归循环和停止条件。
- [D05：模型怎样结合上下文处理信息？](courses/01-llm-overview/d05-attention-transformer/README.md)：Transformer、Q/K/V 训练、Attention、FFN、残差连接与 LayerNorm；修订版理解情况待反馈。
- [D04：文字怎样变成模型的输入？](courses/01-llm-overview/d04-text-input/README.md)：串起 Token、Token ID、Embedding 与位置信息；资料已生成，学习反馈待确认。
- [D03：怎样判断模型有没有学好？](courses/00-foundations/d03-probability-generalization/README.md)：串起 Logit、Softmax、交叉熵、数据划分与泛化；正在阅读，理解情况与自测待反馈。
- [D02：参数怎样从数据中学出来？](courses/00-foundations/d02-learning/README.md)：沿用 D01 的例子串起损失、梯度、反向传播与更新；阅读已开始，自测尚未提交。
- [大模型知识脉络图](knowledge-map.md)：领域全景、课程顺序、实际工作流程三张 Mermaid 图，以及 D01～D17 每章要回答的问题。
- [开始 D01](courses/00-foundations/d01-tensors/README.md)：重写版“大模型内部究竟在计算什么”，直接从开篇顺序阅读。
- D01 助记卡片与自测题已放在正文末尾；[参考答案](courses/00-foundations/d01-tensors/quiz-answers.md)单独查看。
- [D01 学习安排](courses/00-foundations/d01-tensors/study-guide.md)及[学习记录](notes/d01.md)：按实际阅读与答题进展使用。
- [D01 课程大纲](courses/00-foundations/d01-tensors/outline.md)：保留课程设计供回顾。
- [学习路线](roadmap.md)：D01～D17 为章节编号，第一轮暂按约 8～10 个学习日安排，按理解情况调整。
- [学习进度](progress.md)：区分资料准备、实际学习和掌握情况。
- [资料制作规范](standards/material-guide.md)：写作、教学、代码与质量要求。
- [参考依据](standards/sources.md)：已查阅的写作与教学设计资料及采用方式。
- [课时模板](templates/lesson-template.md)：后续讲义的通用结构。
- [本目录协作约定](AGENTS.md)：让后续在该目录中的工作延续已确认的偏好。

## 后续资料组织

课时按需生成，不预先填充空白课程。新增时采用以下路径规则：

| 路径规则 | 内容 |
| --- | --- |
| courses/00-foundations/d01-tensors/ | 深度学习基础课时 |
| courses/01-llm-overview/d04-text-input/ | 大模型结构与生成课时 |
| courses/02-inference/ | 后续推理工程课程 |
| 每课 README.md | 连贯讲解、必要图示、章末助记卡片和自测题 |
| 每课 quiz-answers.md | 当前快速学习自测答案 |
| 每课 assets/ | 本地图示 |
| 既有 code/、lab/、practice.md、exercises.md、solutions.md | 历史实操资料，当前不要求完成 |
| notes/ | 用户作答、复盘、错题与问题记录 |

文档内部使用相对链接便于移动目录；聊天交付使用绝对路径链接。所有学习必需内容在本地讲义中讲清楚，外部资料用于溯源或选读。
