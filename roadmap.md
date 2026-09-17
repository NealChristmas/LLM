# 大模型学习路线

当前方式是 **阅读讲解与图示 → 助记卡片 → 自测题**，不做实验、不写代码。每天可安排 4 小时，通常学习 2 章，难点放慢；第一轮先按约 8～10 个学习日安排，这是可调整的预算，不是掌握保证。

**D01～D17 继续作为稳定章节编号，不再与日历天数绑定。** D01 正文已读，D02、D03 的自测尚未提交；不因进入下一章而自动判定前章已经掌握。以下阶段后的实操成果不属于本轮要求。

图形总览及逐章选题见[知识脉络图](knowledge-map.md)：区分领域分类、学习顺序和实际工作流程，以下保留阶段摘要。

| 章节 | 主要问题 | 本轮学习成果 |
| --- | --- | --- |
| D01 | 模型内部怎样计算？ | 解释输入、参数、张量、shape 与前向计算 |
| [D02](courses/00-foundations/d02-learning/README.md) | 参数怎样学出来？ | 解释损失、梯度、反向传播与更新之间的关系 |
| [D03](courses/00-foundations/d03-probability-generalization/README.md) | 怎样判断预测与学习效果？ | 区分概率、交叉熵、过拟合、训练与验证 |
| [D04](courses/01-llm-overview/d04-text-input/README.md) | 文字怎样变成模型的输入？ | 串联 Token、Token ID、Embedding 与位置信息 |
| [D05](courses/01-llm-overview/d05-attention-transformer/README.md) | 模型怎样结合上下文处理信息？ | 串联 Q/K/V、自注意力、多头注意力与 Transformer 层 |
| [D06](courses/01-llm-overview/d06-autoregressive-generation/README.md) | 模型怎样逐步生成文本？ | 串联因果遮罩、Logit、采样、自回归循环与停止条件 |
| [D07](courses/01-llm-overview/d07-pretraining/README.md)～[D08](courses/01-llm-overview/d08-post-training/README.md) | 模型能力怎样形成和调整？ | 区分预训练、SFT、偏好优化与 LoRA |
| [D09](courses/01-llm-overview/d09-prompt-context/README.md)～[D10](courses/01-llm-overview/d10-retrieval/README.md)～[D11](courses/01-llm-overview/d11-rag/README.md) | 如何利用外部知识？ | 解释提示词、上下文、检索与 RAG，判断典型错误来源 |
| [D12](courses/01-llm-overview/d12-tool-calling/README.md)～[D13](courses/01-llm-overview/d13-agent-workflow/README.md) | 如何使用工具完成任务？ | 理解工具调用、执行反馈与 Agent 循环 |
| [D14](courses/01-llm-overview/d14-inference-memory/README.md)～[D15](courses/01-llm-overview/d15-serving-engine/README.md) | 模型服务为什么慢或占显存？ | 认识 GPU、Prefill、Decode、KV Cache 和推理服务 |
| [D16](courses/01-llm-overview/d16-evaluation/README.md)～[D17](courses/01-llm-overview/d17-system-diagnosis/README.md) | 怎样选择改进方案？ | 用整体地图区分模型、检索、工具与服务层的问题 |

阅读[整体地图](knowledge-map.md)后按主线推进。每章围绕一块知识拼图，章末提供约 6～10 张卡片、5～8 道自测题和独立答案。

每章可用 60～100 分钟：正文与图示约 40～60 分钟，卡片约 10 分钟，自测与核对约 15～25 分钟；按内容调整。每天余下时间用于休息、前章卡片和错题，不把一章强行拉长到四小时。

## 深入阶段

第一轮后进入推理工程原理，仍不安排实验。D18～D32 共 15 章，建议每天约两章，预计 8～10 个学习日；能复述原理不等于已经具备工程实践能力。

| 章节 | 主线问题 | 阶段成果 |
| --- | --- | --- |
| [D18](courses/02-inference/d18-gpu-execution/README.md)～[D22](courses/02-inference/d22-performance-diagnosis/README.md) | 推理怎样在 GPU 上执行，瓶颈怎样定位？ | 连接算子、Kernel、存储层级、Roofline、显存估算与分阶段诊断 |
| [D23](courses/02-inference/d23-quantization-execution/README.md)～[D27](courses/02-inference/d27-speculative-decoding/README.md) | 单卡优化分别减少了什么成本？ | 区分量化、融合、FlashAttention、KV 优化和推测解码的作用边界 |
| [D28](courses/02-inference/d28-request-lifecycle/README.md)～[D32](courses/02-inference/d32-engine-selection/README.md) | 引擎怎样管理请求并完成选型？ | 解释生命周期、混合调度、抢占、公平性、负载建模与引擎选择 |

## 实战阶段

D33～D47 将使用同一个模型和一套固定负载，依次完成**环境与基线 → 推理服务 → 压测与诊断 → 单项优化 → 多卡与可靠性 → 综合交付**。每章按一个 4 小时实践单元设计，具体命令和模型在 D33 确认硬件后再固定。

| 章节 | 主线问题 | 阶段成果 |
| --- | --- | --- |
| [D33～D35](courses/03-inference-practice/README.md#第一阶段建立可复现基线) | 环境、模型和基线怎样固定？ | 环境清单、模型清单、可复现的单请求基线 |
| [D36～D39](courses/03-inference-practice/README.md#第二阶段从模型运行到可测量服务) | 怎样部署、压测并定位瓶颈？ | 可调用服务、固定负载、监控证据与诊断报告 |
| [D40～D44](courses/03-inference-practice/README.md#第三阶段一次只验证一种优化) | 优化是否在目标负载下真正有效？ | 批处理、KV Cache、量化、前缀优化和引擎对比数据 |
| [D45～D47](courses/03-inference-practice/README.md#第四阶段从单卡实验走向可交付系统) | 怎样扩展并形成生产级结论？ | 多卡设计、故障恢复记录和最终部署选型报告 |

完整章节与验收产物见[推理工程实战规划](courses/03-inference-practice/README.md)。Kubernetes、多租户平台和 CUDA/Triton 留到完成 D47 后按职业方向选择，避免同时展开三条实践线。
