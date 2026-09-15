# 学习进度

更新：2026-09-15。

## 已确认的学习约束

- 每天可安排 4 小时。
- 当前快速知识学习，不做实验；每章以助记卡片和自测题收尾。D01～D17 为章节编号，可一天多章。
- 先从整体介绍大模型涉及的环节与流程，再补基础；每章完成整体知识脉络的一块拼图，随后深入。
- 后续学习资料由助手生成并沉淀在本目录。
- 有 3 年 C++ 和 JavaScript 开发经验，具备通用编码基础；非必要的编码知识不进入学习资料。
- Python/PyTorch 的特殊用法只按实验需要简述；用户略懂数学，涉及梯度等概念时优先直接给出规范数学推导；机器学习基础与 GPU 条件尚未确认。
- 正文以问题和因果承接展开；新概念按“已有问题 → 旧方法不足 → 所需机制 → 概念名称”自然引入，避免先抛术语再补定义。用户反馈初版冗余且张量引入突兀；学习安排与验收矩阵移至附页。
- 排版采用连贯段落，减少冗余换行；重点加粗，复杂关系配图。公式使用 Markdown 原生可读的 Unicode 写法，不依赖 LaTeX 渲染；助记卡使用原生 Markdown，不使用 HTML 折叠标签。变量在首次使用处就近解释，只有符号很多且反复使用时才列符号表；公式变形前说明目的。D01 第 4 节已加入逐行计算图。

## 当前状态

| 项目 | 资料准备 | 学习状态 | 证据 |
| --- | --- | --- | --- |
| 写作规范、教学方法、课时模板 | 已建立 | 不适用 | standards/ 与 templates/ |
| 学习路线 | 已建立 | 尚未开始记录 | roadmap.md |
| 整体知识地图 | 三张 Mermaid 图与 D01～D17 逐章脉络已生成 | 作为持续导航，不单独判定掌握 | [知识地图](knowledge-map.md) |
| D01：大模型内部究竟在计算什么 | 快速版已生成；已澄清矩阵与形状，并在回顾审查中移除未展开的提前术语和失效的折叠提示 | 用户已读完正文；卡片表述反馈已处理，自测未提交，未验收 | [讲义](courses/00-foundations/d01-tensors/README.md)、[自测答案](courses/00-foundations/d01-tensors/quiz-answers.md) |
| D02：参数怎样从数据中学出来 | 正文、图示、8 张卡片与 7 道自测及答案已生成；已补齐 D01 的 y 到 D02 的 ŷ/y 符号转换，第三节采用原生 Markdown 数学推导 | 用户正在阅读第三节；已确认略懂数学，希望直接阅读数学推导；理解情况与自测待反馈 | [讲义](courses/00-foundations/d02-learning/README.md)、[答案](courses/00-foundations/d02-learning/quiz-answers.md) |
| D03：怎样判断模型有没有学好 | 正文、图示、8 张卡片与 7 道自测及答案已生成；变量就近解释，交叉熵、泛化及评估风险均由已有问题自然引出 | 用户正在阅读；第三、四节反馈已处理，理解情况与自测待反馈 | [讲义](courses/00-foundations/d03-probability-generalization/README.md)、[答案](courses/00-foundations/d03-probability-generalization/quiz-answers.md) |
| D04：文字怎样变成模型的输入 | 正文、两张流程图、8 张卡片与 7 道自测及答案已生成 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d04-text-input/README.md)、[答案](courses/01-llm-overview/d04-text-input/quiz-answers.md) |
| D05：模型怎样结合上下文处理信息 | 正文、五张机制图、11 张卡片与 8 道自测及答案已生成；已根据反馈补充 Transformer 全貌、Q/K/V 的端到端训练，以及 FFN、残差连接和 LayerNorm 的机制 | 用户已阅读初版并反馈上述概念晦涩；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d05-attention-transformer/README.md)、[答案](courses/01-llm-overview/d05-attention-transformer/quiz-answers.md) |
| D06：模型怎样一个接一个生成 Token | 正文、四张流程图、9 张卡片与 8 道自测及答案已生成 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d06-autoregressive-generation/README.md)、[答案](courses/01-llm-overview/d06-autoregressive-generation/quiz-answers.md) |
| D07：基础模型的能力从哪里来 | 正文、四张机制图、9 张卡片与 8 道自测及答案已生成；已根据“晦涩难懂”的反馈改为从单次预测、训练步到规律沉淀的连续例子 | 用户已阅读初版；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d07-pretraining/README.md)、[答案](courses/01-llm-overview/d07-pretraining/quiz-answers.md) |
| D08：怎样让模型更适合指令和任务 | 正文、五张机制图、9 张卡片与 8 道自测及答案已生成；已根据“晦涩难懂”的反馈拆分训练阶段与参数更新方式，并简化 LoRA 解释 | 用户已阅读初版；修订版理解情况与自测待反馈，未验收 | [讲义](courses/01-llm-overview/d08-post-training/README.md)、[答案](courses/01-llm-overview/d08-post-training/quiz-answers.md) |
| D09：不改参数，怎样影响这一次回答 | 正文、三张机制图、9 张卡片与 8 道自测及答案已生成；已根据审查统一总结示例、澄清 Prompt/Context 边界并修正窗口超限表述 | 尚未收到阅读或作答反馈，未验收 | [讲义](courses/01-llm-overview/d09-prompt-context/README.md)、[答案](courses/01-llm-overview/d09-prompt-context/quiz-answers.md) |
| D10～D17 | 已规划，未生成 | 未确认开始 | 无 |

生成讲义不等于完成学习。只有用户反馈或作答结果支持时才更新完成情况；运行示例成功也不直接代表已理解。

## 后续学习记录格式

| 日期 / 课时 | 实际用时 | 独立完成的任务 | 尚未掌握的问题 | 证据文件 | 复习安排 |
| --- | --- | --- | --- | --- | --- |

已创建 [D01 学习记录模板](notes/d01.md)，原内容保留。现在可直接在聊天中回答章末自测，不要求填旧实验栏目；卡片及资料已生成不等于已掌握。
