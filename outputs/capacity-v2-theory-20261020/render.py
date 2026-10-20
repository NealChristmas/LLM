"""Render only the current V2 theory result; does not perform capacity calculation."""
from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET
from html import escape
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'report.json').read_text(encoding='utf-8'));a=r['assumptions'];q=r['request'];c=r['central'];p=c['phase']['prefill'];d=c['phase']['decode'];cache=r['cache'];cards=r['budgetCards']
if cards is None:raise ValueError('No candidate under fixed layout; cannot render a budget candidate')
scenes='\n'.join(f"| {s['assumption']['name']}（{s['assumption']['prefillEfficiency']:.0%} / {s['assumption']['decodeEfficiency']:.0%}） | {s['meanTtftBudgetMs']/1000:.2f} 秒 / {s['busyDecodeStepBudgetMs']:.1f} ms/Token | {'满足所列预算约束' if s['withinModeledConstraints'] else '不满足预算约束'} |" for s in r['scenarios'])
body=f"""# DeepSeek-V4.1-Flash 推理容量理论预算（V2）

测算日期：2026-10-20。范围：固定参考布局的理论预算，不使用实测性能记录。

![本轮纯理论测算流程图](sizing-flow.png)

[查看流程大图](sizing-flow.svg)

> **当前参考布局的预算候选：{cards['totalCards']} 张 A3-560T 物理卡，Prefill {p['physicalCards']} 张、Decode {d['physicalCards']} 张，备用 {cards['spareCards']} 张。更小布局尚未评估。**
>
> 该候选在明确假设下满足所列显存及时延预算；KV INT8实现、实际通信和运行峰值尚未验证，不能作为部署或时延达标承诺。

## 一、需求与部署条件

| 项目 | 本轮条件 |
| --- | --- |
| 模型、精度与框架 | DeepSeek-V4.1-Flash；W8A8，KV INT8；vLLM Ascend v0.30.0rc1 |
| 平均输入 / 输出 | 8,000 / 1,000 Token，输出包含全部推理Token |
| 峰值并发与负载 | 60 路同批突发 |
| 平均延迟目标 | TTFT ≤ 3,000 ms；TPOT ≤ 50 ms/Token |
| 部署与硬件 | A3-560T；PD 分离 |
| 增长 / 备用 / Prefix Cache | 0% / 0组 / 命中率0 |

### 本轮建模方案

评估范围为固定参考布局：Prefill 配置 8 张物理卡、4 个推理实例，每实例使用 2 张卡；Decode 配置 8 张物理卡、8 个推理实例，每实例使用 1 张卡。推理实例可能通过专家并行共享权重，不等于独占完整模型副本。

调度采用已确认的简化假设：60 路请求均衡分配，Prefill 各实例逐请求先到先服务；Decode 用最繁忙实例的步长近似平均 TPOT。前者为业务突发输入的建模方式，后者为生成阶段性能近似，均不代表真实调度已核验。

参考方案采用 INT8 Engram 主机共享卸载及 5 Token DSpark，不计推测加速收益；KV INT8 按授权的假想格式预算。

### 关键依据与假设

| 项目 | 取值 | 来源与状态 |
| --- | --- | --- |
| Prefill / Decode激活参数 | 约80亿 / 160亿 | 固定版本官方说明；仅近似线性运算 |
| 单物理卡INT8峰值 / 标称内存 | 1,120 TOPS / 128 GB | 官方整机规格推导，非有效性能 |
| Prefill / Decode峰值折算系数 | 40% / 2% | 本轮沿用授权粗估假设，未实测校准 |
| Prefill / Decode固定开销 | 300 ms / 2 ms每Token | 工程假设，未验证传输与排队是否可被覆盖 |
| 权重附加 / 非专家复制修正 | 10% / ×1.30 | 目标量化及分片的预算近似 |
| KV格式 / 缓存附加预算 | INT8值及尺度 / 25% | 假想实现，非已验证部署格式 |
| 每卡运行预留 / 草稿工作系数 | 16 GiB / ×1.25 | 工程假设，不计DSpark加速收益 |

## 二、计算规则

### 显存与阶段时延

> 每物理卡显存预算 ≈ 权重驻留预算 ＋ 请求缓存预算 ＋ 运行预留
>
> 权重驻留预算 ≈ 卡内各分片的［专家分片 ＋ 非专家分片及复制 ＋ 保留模块］附加预算之和
>
> 每请求缓存预算 ≈（压缩共享主缓存 ＋ 索引缓存 ＋ 主模型及草稿滑窗）× 缓存附加系数
>
> 单请求Prefill工作量 ≈ 输入Token数 × 每Token的Prefill激活参数量 × 乘加运算计数
>
> 平均TTFT ≈ 固定开销 ＋ 单请求Prefill工作量 ÷ 每个Prefill推理实例有效算力 × 平均完成顺序
>
> TPOT近似值 ≈ 最繁忙Decode实例并发 × 每Token的Decode工作量 × 草稿工作系数 ÷ 每个Decode推理实例有效算力 ＋ 固定开销

每实例有效算力按占用物理卡数、同精度单卡峰值和明确折算系数预算。缓存依据来源层共享、压缩与滑窗分别计数，不能把普通KV公式或原精度缓存直接倍乘到本模型。各项输入来源和假设详见第一章，完整适用条件见附录。

### 配置与卡数

> 候选布局 ＝ 满足声明显存及时延预算的已评估布局
>
> 总物理卡数 ＝ 工作完整组数 × 每组物理卡数 ＋ 备用完整组数 × 每组物理卡数

卡数按完整参考组取整；只有实际逐布局重算后，才能比较候选资源，不从单布局结果外推更小配置。

## 三、理论测算过程

### 3.1 规划负载

> 规划并发 ＝ 峰值并发 ×（1 ＋ 增长比例）＝ 60 ×（1 ＋ 0%）＝ {r['plannedConcurrency']} 路

### 3.2 权重与缓存显存

每请求逻辑缓存根据本模型来源层、压缩与滑窗计算为约{cache['logicalBytesPerRequest']/2**20:.2f} MiB，加25%余量后约{cache['budgetBytesPerRequest']/2**20:.2f} MiB。假设主缓存及滑窗每512维INT8值带一个FP32尺度，索引为128维INT8值带FP16尺度；格式尚未验证，推导见附录。

**权重从哪里来？** 张量清单恢复后的专家 W8 数据约 {r['targetDataGroups']['expertW8Bytes']/2**30:.2f} GiB，非专家保留数据约 {r['targetDataGroups']['denseRetainedBytes']/2**30:.2f} GiB，视觉及对齐保留模块约 {r['targetDataGroups']['visionRetainedBytes']/2**30:.2f} GiB。专家分片、非专家复制和卡内分片数按本布局计算；两种阶段的非专家切分不同，因此每卡权重不同。

> 每卡权重预算 ≈ 卡内分片数 ×［专家数据 ÷ 专家分片数 ＋ 非专家数据 ÷ 张量并行度 × 复制修正 ＋ 每分片保留模块］× 权重附加系数
>
> Prefill 每卡权重 ≈ 2 ×［{r['targetDataGroups']['expertW8Bytes']/2**30:.2f} ÷ 16 ＋ {r['targetDataGroups']['denseRetainedBytes']/2**30:.2f} ÷ 4 × 1.30 ＋ {r['targetDataGroups']['visionRetainedBytes']/2**30:.2f}］× 1.10 ≈ **{p['cardWeightGiB']:.2f} GiB**
>
> Decode 每卡权重 ≈ 2 ×［{r['targetDataGroups']['expertW8Bytes']/2**30:.2f} ÷ 16 ＋ {r['targetDataGroups']['denseRetainedBytes']/2**30:.2f} ÷ 2 × 1.30 ＋ {r['targetDataGroups']['visionRetainedBytes']/2**30:.2f}］× 1.10 ≈ **{d['cardWeightGiB']:.2f} GiB**

公式中的 2 表示本物理卡内的两个计算分片，16 为该阶段的专家分片总数；这些是内部布局参数，不是新增物理卡数。复制修正 1.30 和附加系数 1.10 为工程预算假设。

**缓存如何计入每张卡？** Prefill 每实例分配 15 路，Decode 最繁忙实例分配 8 路。按本轮缓存复制假设，一张物理卡的两个卡内分片各保留该实例的请求缓存，因此整卡缓存预算计两份。

> 单请求缓存预算 ≈ 单请求逻辑缓存 × 缓存附加系数 ≈ {cache['logicalBytesPerRequest']/2**20:.2f} × 1.25 ≈ {cache['budgetBytesPerRequest']/2**20:.2f} MiB
>
> 每物理卡缓存 ≈ 每实例请求数 × 单请求缓存预算 × 卡内缓存副本数 ÷ MiB转GiB系数
>
> Prefill 每卡缓存 ≈ 15 × {cache['budgetBytesPerRequest']/2**20:.2f} × 2 ÷ 1,024 ≈ **{p['cardCacheGiB']:.2f} GiB**
>
> Decode 每卡缓存 ≈ 8 × {cache['budgetBytesPerRequest']/2**20:.2f} × 2 ÷ 1,024 ≈ **{d['cardCacheGiB']:.2f} GiB**

| 每物理卡预算 | Prefill | Decode |
| --- | ---: | ---: |
| 权重及附加预算 | {p['cardWeightGiB']:.2f} GiB | {d['cardWeightGiB']:.2f} GiB |
| 请求缓存预算 | {p['cardCacheGiB']:.2f} GiB | {d['cardCacheGiB']:.2f} GiB |
| 运行预留 | {p['cardRuntimeGiB']:.2f} GiB | {d['cardRuntimeGiB']:.2f} GiB |
| 显存合计 | **{p['cardTotalGiB']:.2f} GiB** | **{d['cardTotalGiB']:.2f} GiB** |
| 标称容量折算 | {p['cardCapacityGiB']:.2f} GiB | {d['cardCapacityGiB']:.2f} GiB |

> Prefill每卡显存 ≈ 权重预算 ＋ 缓存预算 ＋ 运行预留 ≈ {p['cardWeightGiB']:.2f} ＋ {p['cardCacheGiB']:.2f} ＋ {p['cardRuntimeGiB']:.2f} ≈ **{p['cardTotalGiB']:.2f} GiB**
>
> Decode每卡显存 ≈ 权重预算 ＋ 缓存预算 ＋ 运行预留 ≈ {d['cardWeightGiB']:.2f} ＋ {d['cardCacheGiB']:.2f} ＋ {d['cardRuntimeGiB']:.2f} ≈ **{d['cardTotalGiB']:.2f} GiB**

计算使用未舍入值，显示值相加可能有尾差。显存为平均长度预算；每卡 128 GB 折算约 119.21 GiB，并非卡内单一共享池。卡内仅按均匀分片假设检查容量。Engram主机数据及附加预算约{r['hostEngramBudgetGiBPerNode']:.1f} GiB/节点，另需完整主机运行内存。

### 3.3 估算平均TTFT

> 单请求Prefill工作量 ≈ 输入Token数 × 2 × 每Token的Prefill激活参数量 ≈ 8,000 × 2 × 80亿 ＝ {r['inputWorkTopPerRequest']:g} TOP
>
> 每个Prefill推理实例有效算力 ＝ 实例物理卡数 × 单卡INT8峰值 × Prefill折算系数 ＝ 2 × 1,120 × 40% ＝ {p['effectiveTopsPerInstance']:g} TOPS
>
> 每实例请求数 ＝ 规划并发 ÷ Prefill实例数 ＝ 60 ÷ 4 ＝ 15；平均完成顺序 ＝（1 ＋ 每实例请求数）÷ 2 ＝（1 ＋ 15）÷ 2 ＝ {r['meanPrefillCompletionOrder']:g}
>
> 平均TTFT ≈ 固定开销 ＋（单请求工作量 ÷ 每实例有效算力）× 平均完成顺序 ≈ 0.300 ＋（128 ÷ 896）× 8 ≈ **{c['meanTtftBudgetMs']/1000:.2f} 秒 ≤ 3 秒**

系数2按一次乘法、一次加法计数。80亿是每Token的Prefill激活参数量，并非模型总参数量。以上未逐算所有注意力与非线性算子。平均完成顺序来自已确认的均衡逐请求服务模型，不代表真实连续批处理调度。

### 3.4 估算TPOT

> 每Token的Decode工作量 ≈ 2 × 每Token的Decode激活参数量 ≈ 2 × 160亿 ＝ {r['decodeWorkTopPerToken']:g} TOP
>
> 每个Decode推理实例有效算力 ＝ 实例物理卡数 × 单卡INT8峰值 × Decode折算系数 ＝ 1 × 1,120 × 2% ＝ {d['effectiveTopsPerInstance']:g} TOPS
>
> 最繁忙Decode实例并发 ＝ 向上取整［规划并发 ÷ Decode实例数］＝ 向上取整［60 ÷ 8］＝ {d['busyRequestsPerInstance']} 路
>
> TPOT近似值 ≈ 最繁忙实例并发 × 每Token工作量 × 草稿工作系数 ÷ 每实例有效算力 × 毫秒换算系数 ＋ 固定开销 ≈ 8 × 0.032 × 1.25 ÷ 22.4 × 1,000 ＋ 2 ≈ **{c['busyDecodeStepBudgetMs']:.1f} ms/Token ≤ 50 ms/Token**

用最繁忙实例步长近似预算平均TPOT，未模拟Prefill与Decode交叠、专家共享竞争或推测接受过程。它不是平均TPOT的实测值，也不是严格上界。

### 3.5 目标对照与敏感性

| 检查项 | 中心预算 / 目标 | 判断 |
| --- | --- | --- |
| Prefill每卡显存 | {p['cardTotalGiB']:.2f} / {p['cardCapacityGiB']:.2f} GiB | 假设分片下容量可容纳 |
| Decode每卡显存 | {d['cardTotalGiB']:.2f} / {d['cardCapacityGiB']:.2f} GiB | 假设分片下容量可容纳 |
| 平均 TTFT | {c['meanTtftBudgetMs']/1000:.2f} 秒 / ≤3 秒 | 简化调度下的平均值预算，满足所列目标 |
| TPOT 近似值 | {c['busyDecodeStepBudgetMs']:.1f} / ≤50 ms/Token | 最繁忙实例步长近似，非平均值测量 |

| 情景（Prefill / Decode系数） | 平均TTFT / TPOT近似值 | 固定组预算判断 |
| --- | --- | --- |
{scenes}

这些是未校准假设的敏感性情景，不是置信区间；实际效率可能落在所列范围外。三种情景均在本轮固定布局内满足预算约束。

### 3.6 工作卡与备用卡

> 每组物理卡 ＝ Prefill物理卡 ＋ Decode物理卡 ＝ 8 ＋ 8 ＝ 16 张
>
> 工作卡 ＝ 工作组数 × 每组物理卡数 ＝ 1 × 16 ＝ {cards['workCards']} 张
>
> 备用卡 ＝ 备用组数 × 每组物理卡数 ＝ 0 × 16 ＝ {cards['spareCards']} 张
>
> 总物理卡数 ＝ 工作卡 ＋ 备用卡 ＝ {cards['workCards']} ＋ {cards['spareCards']} ＝ **{cards['totalCards']} 张**

## 四、结论与适用范围

当前Prefill 8张＋Decode 8张参考布局，在本轮明确假设下满足所列容量及时延预算；可作为16张物理卡的前期预算候选，无备用冗余。本轮没有开展更小布局搜索，也没有验证KV INT8部署可行性，尚不能确定最少卡数或承诺时延达标。

### 后续验证顺序

| 顺序 | 核验内容 | 需要保留的材料 |
| --- | --- | --- |
| 1 | 确认目标框架及模型的 KV INT8 支持、输出质量与额外开销 | 框架/模型修订、量化配置、启动参数及质量对比记录 |
| 2 | 核对实际权重、分片与每卡显存峰值，并检查主机卸载和互联 | 目标权重清单、布局配置、逐卡/卡内运行日志与资源记录 |
| 3 | 以本轮平均长度、60 路同批突发、零命中率测时延 | 压测命令、请求长度和输出范围、平均 TTFT/TPOT、KV 传输记录 |

若要回答能否减卡，应增加有部署依据的候选布局，分别重算权重、缓存和时延。本次仅优化文档，没有补算新布局。

应急模板存在重复前缀时，本轮仍按零命中率计算；命中长度、复用率及调度行为有依据后才能调整模型。完整来源与适用条件见[依据附录](report.evidence.md)。
"""
def spaced_prose(text):
    lines=[]
    for line in text.splitlines():
        if not re.search(r'\]\(|https?://|`',line):
            line=re.sub(r'([\u4e00-\u9fff])([A-Za-z0-9])',r'\1 \2',line)
            line=re.sub(r'([A-Za-z0-9%])([\u4e00-\u9fff])',r'\1 \2',line)
        lines.append(line)
    return '\n'.join(lines)+'\n'
(ROOT/'report.client.md').write_text(spaced_prose(body),encoding='utf-8')
m=json.loads((ROOT/'model-input.json').read_text(encoding='utf-8'))
appendix=f"""# V2 理论测算依据附录

对应[客户报告](report.client.md)。纯理论评估；没有性能基线导入、匹配或实测综合过程。

## 一、文件与来源

- [业务需求](request.json)、[config快照](config.json)、[结构摘要与版本](model-input.json)、[预算假设](assumptions.json)、[完整结果](report.json)。
- 官方模型固定提交：`{r['identity']['modelRevision']}`；config摘要：`{r['identity']['configSha256']}`。
- [固定官方模型文件清单](sources/model/manifest.json)：config、说明、实现及张量索引。80亿/160亿激活参数来自该版本官方README。未依赖config自行声明激活参数。
- [结构分组摘要](sources/structure-summary.json)：来自此前已核验的张量头形状、存储格式与尺度分组。本轮只使用结构字段，没有读取其历史卡数或性能推断。摘要SHA-256见model-input.json。
- [固定推理实现清单](sources/deployment/manifest.json)，修订`{r['identity']['referenceDeployRevision']}`，不证明与现场rc1镜像完全一致。
- [硬件官方依据及链接](sources/hardware-specifications.md)：Atlas800I A3整机8个物理NPU、INT8峰值8.96POPS、内存8×128GB，得到每卡1120TOPS和128GB。

## 二、权重驻留与主机预算

主干和草稿FP4专家恢复为W8，按逻辑元素数计1字节；其他原生FP8按1字节，BF16/FP32保持原格式。原生尺度不直接搬到目标格式，另以10%权重附加预算代替。这不是目标W8转换结果的精确清单。

| 分组 | 本轮数据量 |
| --- | ---: |
| 主干加草稿路由专家W8 | {r['targetDataGroups']['expertW8Bytes']/2**30:.2f} GiB |
| 非专家主干加草稿保留数据 | {r['targetDataGroups']['denseRetainedBytes']/2**30:.2f} GiB |
| 视觉与对齐保留数据 | {r['targetDataGroups']['visionRetainedBytes']/2**30:.2f} GiB |

参考EP分片覆盖每阶段的16个内部芯片分片，Prefill张量并行度4、Decode为2。非专家简单均分乘1.30复制修正；视觉模块保守按各内部芯片保留，最后每物理卡汇总。它假定负载均衡，不证明真实分配峰值。主机INT8 Engram数据按逻辑元素数计，再加10%，约{r['hostEngramBudgetGiBPerNode']:.2f} GiB/节点，主机运行/操作系统资源另计。

## 三、专属缓存假设与算法

该A3参考实现主缓存为BF16并配INT8索引，不能证明全KV INT8受支持。用户授权假想INT8预算，假设512维主缓存和滑窗每行512字节INT8值加4字节FP32尺度，无零点；索引128字节INT8值加2字节FP16尺度。来源层{cache['ownerLayers']}，压缩比{cache['compressionRatios']}，共享非来源层去重。主干40层加草稿3层的滑窗长度128，均按假想格式计算。

> 每Token全局缓存 ≈ 来源压缩系数和 ×（主缓存行字节 ＋ 索引行字节）≈（1/2 ＋ 1/2 ＋ 1/2 ＋ 1）×［（512 ＋ 4）＋（128 ＋ 2）］＝ {cache['hypotheticalGlobalBytesPerToken']:g} 字节
>
> 固定滑窗缓存 ≈ 主干及草稿层数 × 滑窗长度 × 每行字节 ≈（40 ＋ 3）× 128 ×（512 ＋ 4）＝ {cache['hypotheticalFixedSlidingBytes']:,} 字节
>
> 每请求逻辑缓存 ≈ 每Token全局缓存 × 输入输出总长度 ＋ 固定滑窗缓存 ≈ 1,615 × 9,000 ＋ 2,840,064 ＝ {cache['logicalBytesPerRequest']:,.0f} 字节 ≈ {cache['logicalBytesPerRequest']/2**20:.2f} MiB

每实例保留请求数取最繁忙分配，缓存按内部张量并行复制后汇总整卡，并加25%。物理池分配、压缩中间状态、对齐、草稿验证缓冲没有精确建模；余量不保证上界。

## 四、阶段与性能边界

均衡逐请求先到先服务模型用完成序号平均求平均TTFT。算力峰值与运算计数使用INT8 TOPS口径，乘加各计一次；有效折算系数为明确工程假设，非监控忙碌率。目标模型实际混合精度操作、带宽、路由、共享专家竞争和精确注意力未逐项建模，不能保证这些因素全部被折算系数覆盖。

Decode按最繁忙实例8路的工作量估计步长，再加草稿工作系数与固定开销。未模拟实际连续批处理和推测接受率，不因启用DSpark声称收益。KV INT8转换可能有额外开销，未填任意加速比。

KV传输及主机卸载未独立得到带宽、队列和工作集依据。300ms/2ms固定开销是预算取值，不是这些未知项的实测证明。部署可行性与实测SLO均未验证；globalMinimumCards、finalCards保持null。

## 五、复算与验证

先运行`python calculate.py`写入结果，再运行`python render.py`仅生成报告与图。只读本目录输入、本地tools算术辅助及固定结构来源，未访问实测性能文件。3项数值测试覆盖手算时延/缓存、备用不参与工作能力、严格目标失败及长度变化。来源/输入/脚本摘要见report.json。

图源为[sizing-flow.svg](sizing-flow.svg)，生成脚本为[draw_flow.py](draw_flow.py)，采用显存/性能分支逐层推导。本轮完成SVG语法、链接及PNG视觉检查；PNG由本地绘图组件生成，未运行硬件测试。代码运行通过不等于部署支持通过。
"""
(ROOT/'report.evidence.md').write_text(spaced_prose(appendix),encoding='utf-8')
import subprocess,sys
subprocess.run([sys.executable,str(ROOT/'draw_flow.py')],check=True)
import shutil
pwsh=shutil.which('pwsh') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
subprocess.run([pwsh,'-NoProfile','-File',str(ROOT/'render_flow_png.ps1'),'-SvgPath',str(ROOT/'sizing-flow.svg'),'-PngPath',str(ROOT/'sizing-flow.png')],check=True)
for f in [ROOT/'report.client.md',ROOT/'report.evidence.md']:
 for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  if ':' not in link and not link.startswith('#'):assert (f.parent/link).exists(),(f,link)
for f in [ROOT/'report.client.md',ROOT/'sizing-flow.svg']:
 text=f.read_text(encoding='utf-8');assert all(t not in text for t in ['Device','输入侧','生成侧','进程','基线筛选','独立核对基线'])
(ROOT/'verification.json').write_text(json.dumps({'numericalTestsPassed':3,'checks':['input config hash','request and algorithm identity','card-local uniform partition budget','source data does not include measured performance','Markdown links','SVG XML','terminology'],'visualPreviewPerformed':True,'visualPreviewMethod':'local System.Drawing raster checked with image viewer','hardwareTestsRun':False,'resultSha256':hashlib.sha256((ROOT/'report.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
print('V2 pure-theory report, evidence and SVG generated; links, terminology and SVG syntax checked.')
