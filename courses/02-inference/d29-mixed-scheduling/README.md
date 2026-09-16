# D29：Prefill 和 Decode 怎样共享一张 GPU？

D28 中，调度器一轮可能同时面对长 Prompt 和正在生成的请求。若整段长 Prefill 一次占用 GPU，已有请求的下一个 Token 会等待；若永远优先 Decode，新请求又迟迟看不到首 Token。

## 1. 为什么完整 Prefill 会阻塞 Decode？

假设请求 A 正在 Decode，每隔一轮应产生一个 Token；此时请求 B 携带 8000 Token 的 Prompt 到达。若引擎一次完成 B 的全部 Prefill，这次 GPU 工作很长，A 在此期间无法得到下一 Token，流式输出出现停顿。这种现象常被称为 Prefill 对 Decode 的干扰。

固定地“先 Prefill 后 Decode”或“先 Decode 后 Prefill”都无法兼顾两类目标。引擎需要把本轮资源按 Token 而不只是按请求进行分配。

## 2. 把长 Prompt 切成块

**Chunked Prefill（分块预填充）**把长 Prompt 拆成多个 Token 块，每轮只处理其中一块，并在块之间穿插运行中的 Decode。请求 B 完成所有块后才获得完整 Prompt 的 KV Cache，并进入正常生成。

```mermaid
flowchart LR
    R1["第 1 轮"] --> A1["A Decode 1 Token"] --> B1["B Prefill 第 1 块"]
    R2["第 2 轮"] --> A2["A Decode 1 Token"] --> B2["B Prefill 第 2 块"]
    R3["第 3 轮"] --> A3["A Decode 1 Token"] --> B3["B Prefill 第 3 块"]
    B3 --> G["B 开始 Decode"]
```

图是逻辑顺序示意，具体引擎可能将不同请求 Token 打包进同一次执行，而不是逐框单独启动。

## 3. Token 预算怎样控制一轮工作？

调度器通常设置一轮最多处理的总 Token 数。正在 Decode 的每个请求通常先占少量 Token，剩余预算用于一个或多个 Prefill 块。预算太大，单轮执行时间变长，Decode 可能抖动；预算太小，GPU 工作规模不足，长 Prompt 完成 Prefill 的轮数增多。

因此块大小不是越小越公平、也不是越大越高效。它要在 **Decode 连续性、Prefill TTFT、总体吞吐和 Kernel 效率**之间取舍。

## 4. Continuous Batching 在这里做了什么？

D15 已说明连续批处理会让已完成请求退出、新请求进入。深入来看，它依赖调度器在每轮重新构造活动 Token 集合：一些 Token 属于新请求的 Prefill 块，另一些属于运行请求的单步 Decode。底层通过请求 ID、位置和 KV 块映射保证它们互不干扰。

连续批处理回答“哪些请求进入本轮”，Chunked Prefill 回答“一个长 Prompt 本轮只进入多少 Token”。两者结合才能避免长 Prefill 长时间独占，同时维持较大的 GPU 工作批次。

## 5. 混合调度有哪些边界？

Prefill 与 Decode 的计算形状不同，混在一轮需要后端支持相应的打包和 Kernel。Prefill 太多会增加运行请求的 Token 间延迟；Decode 太多会让新请求排队。KV Cache 接近满时，即使 Token 预算有空位，也可能无法接纳新 Prompt。

这说明调度至少受两类预算约束：本轮计算 Token 预算与跨轮保留的 KV Cache 预算。只增大前者不一定增加可并发请求数，只增大缓存也不保证每轮能及时计算。

## 6. 下一步为什么需要抢占与公平性？

当所有请求都能逐轮推进时，混合调度已足够；但缓存耗尽或高优先级请求到来时，引擎必须决定谁等待、谁暂停、谁释放部分状态。D30 将解释抢占、优先级和公平性如何处理这种资源冲突。

## 助记卡片

**卡片 1：长 Prefill 为什么会影响正在 Decode 的请求？**

> **答案：** 一次完整 Prefill 可能形成很长的 GPU 工作，使运行请求等待下一次 Decode。

**卡片 2：Chunked Prefill 做了什么？**

> **答案：** 把长 Prompt 分成多个 Token 块，在多轮中处理，并允许其间穿插 Decode。

**卡片 3：一轮 Token 预算控制什么？**

> **答案：** 控制本轮所有 Prefill 与 Decode 合计最多处理多少 Token。

**卡片 4：块太大有什么风险？**

> **答案：** 单轮时间变长，运行请求的后续 Token 可能停顿。

**卡片 5：块太小有什么风险？**

> **答案：** GPU 工作规模不足，调度轮次增加，长 Prompt 完成 Prefill 更慢。

**卡片 6：Continuous Batching 与 Chunked Prefill 的区别是什么？**

> **答案：** 前者动态选择本轮活动请求，后者限制长 Prompt 每轮处理的 Token 数。

**卡片 7：调度为什么同时受计算与缓存预算限制？**

> **答案：** Token 预算决定本轮算多少，KV 预算决定跨轮能保留多少活动请求状态。

## 自测题

1. 正在生成的 A 遇到 8000 Token 的新 Prompt B，完整 Prefill B 可能造成什么体验？
2. Chunked Prefill 为什么不会让 B 在第一块完成后立即开始生成？
3. 为什么将块无限缩小不是最佳方案？
4. 一轮 Token 预算有剩余，为什么新请求仍可能无法加入？
5. Continuous Batching 与固定批处理相比，调度决定发生在什么粒度？
6. 若目标是降低运行请求的 Token 间抖动，调整 Prefill 预算时应关注什么代价？

完成后再看[参考答案](quiz-answers.md)。返回[D28](../d28-request-lifecycle/README.md)，或继续学习[D30](../d30-preemption-fairness/README.md)。
