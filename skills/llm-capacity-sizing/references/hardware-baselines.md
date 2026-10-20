# 昇腾硬件规格基线

资料核对日期：2026-10-20。来源为华为官方产品页，仅作为硬件规格基线；采购BOM、固件版本、实际内存可用量和实测推理性能仍须按客户设备核验。

## Atlas 800I A3：物理卡与Device

华为官方产品页将 Atlas 800I A3 定位为风冷推理超节点，列出单机8个昇腾910处理器、8 × 128 GB片上内存、整机FP16峰值4.48 PFLOPS、INT8峰值8.96 POPS、双向D2D互联784 GB/s。[华为 Atlas 800I A3 产品规格](https://e.huawei.com/cn/products/computing/ascend/atlas-800i-a3)

昇腾官方CANN文档明确指出，Atlas A3训练/推理系列产品一个NPU有两个Device。[昇腾CANN性能指标说明](https://www.hiascend.com/doc_center/source/zh/CANNCommunityEdition/910/acce/dvpp/aclpythondevg_01_0550.html) 用户也确认本例A3单机8张物理卡、每卡两个die。Device为软件设备口径；并行rank如何映射到Device仍按启动配置核验。

| 计量对象 | 标称内存 | FP16峰值 | INT8峰值 |
| --- | --- | --- | --- |
| 官方整机：8个NPU | 8 × 128 GB | 4.48 PFLOPS | 8.96 POPS |
| 每物理卡/NPU：整机数值÷8 | 128 GB | 560 TFLOPS | 1.12 POPS |
| 每Device：假设双die规格对称，物理卡数值÷2 | 64 GB | 280 TFLOPS | 0.56 POPS |

后两行是规格换算，最后一行还依赖对称分配假设，均非独立实测。可用显存、算子精度支持和有效吞吐须以对应Device和实际部署核验，不能将128 GB或560 TFLOPS重复计入每个Device。

该型号对应 Atlas 800I A3 推理服务器。不要与 Atlas 800T A3 训练超节点混淆：后者产品页列出的处理器规格与整机用途不同。[华为 Atlas 800T A3 产品规格](https://e.huawei.com/cn/products/computing/ascend/atlas-800t-a3)

客户基线中的 `A3-560T` 可与上述每物理卡560 TFLOPS的规格比对，但仅凭芯片字段不能断定实际服务器BOM或计量对象。需要在来源中确认部署卡数是物理卡还是Device，以及并行rank映射。

记录182930的用户已确认总数16卡及每物理卡2个die。若`1P:DP4+TP4/1D:DP8+TP2`各rank使用一个Device，则P侧4×4＝16 Device＝8张物理卡，D侧8×2＝16 Device＝8张物理卡，合计32 Device＝16张物理卡。该解释能使数量一致；它是基于rank映射假设的推导，不冒充启动配置核验，也不是把总卡数简单对半分。未确认rank映射前，不将P/D推导数标记为实测已核验。

[vLLM-Ascend的V4.1-Flash部署指南](https://github.com/vllm-project/vllm-ascend/blob/releases/v0.30.0/docs/source/tutorials/models/DeepSeek-V4.1-Flash.md)也列出A3单机8个NPU、16个逻辑Device，以及双机P侧DP4/TP4、D侧DP8/TP2的布局。这验证了该计量解释的合理性，不能代替记录182930的原始启动配置。指南还使用INT8 Engram存储和主机内存卸载；若采用该布局，须把卸载内存和卡上权重分别预算，不能把全部模型参数都视为卡上常驻。

## 用于计算时的边界

- FP16和INT8是各自精度下的官方峰值，不能相互替代，也不能当成W8A8实测有效能力。
- 128 GB为产品页所列片上内存规格。理论预算需留出权重格式、KV结构、框架工作区、通信缓冲、缓存元数据及系统占用；生产可用值应以实际设备/部署测量为准。
- 规格基线不含TTFT、TPOT、并发或QPS保证。容量与延迟候选必须由与目标口径匹配的实际性能测试支持。
- 若测试记录的芯片型号、整机型号或规格版本与本基线不一致，应先核对客户BOM；不要仅凭“A3”字样套用。
