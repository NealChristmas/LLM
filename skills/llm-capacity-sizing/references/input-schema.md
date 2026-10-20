# 输入与命令

## 基线

新数据优先使用[统一基线字段规范v1.0](baseline-fields.md)与对应Schema，含raw事实和meta口径；prepare自动识别`llm-capacity-baselines/1.0`并校验。下述性能地图与网页项目为兼容导入方式。

支持当前性能地图JSON：单条、数组、逐行JSON、data/list/records/items/rows/results分页包装；`bizLoadFeature`、`deployConfig`、`perfData`、`optimization` 可为JSON字符串或对象。也支持实测网页导出的 `baseline-sizing-project` 项目，保留原记录及人工核对信息。新原始记录同ID覆盖旧记录并重置核对信息；匿名记录按完整内容SHA-256去重。原始数据和扁平key字段冲突时不能作为达标证据。

准备：

```bash
python scripts/sizing.py prepare --baselines data/a.json data/b.jsonl --annotations annotations.json --out work/library.json
```

基线资料没有明确的口径通过独立注释提供，不修改原数据：

```json
{
  "id:182930": {
    "ttftStat": "p95",
    "tpotStat": "p95",
    "load": "closed",
    "kBase": "1024",
    "lengthStat": "fixed",
    "reasoning": "included",
    "qps": "",
    "source": "填写真实报告编号及核对依据",
    "verified": false
  }
}
```

上例只演示格式，不能作为真实记录的口径结论。`verified` 由用户或材料确认后改为true；source不能为空。可增加 `rawHash` 绑定工具准备结果中的源记录摘要，不一致时拒绝套用。

枚举：统计 `p95/mean/p99/max/unknown`；负载 `closed/burst/arrival/unknown`；长度 `fixed/max/mean/unknown`；推理Token `included/excluded/unknown`；K `1000/1024/unknown`。P95表示压测样本中约95%的请求延迟不高于该值、约5%更慢；P95 TTFT/TPOT必须来自相应统计分位数，不能用平均值换算或替代。`qps` 必须是同测试点实测请求/秒，不是Token吞吐。

## 用户需求

用 `request-template` 生成空模板。必填为 `model,input,output,concurrency,ttft,tpot,ttftStat,tpotStat,load,lengthStat,reasoning,prefix`。input/output单位Token，ttft毫秒，tpot毫秒/Token，prefix为0～100百分数。模型并发已包含业务内部同时调用，不再乘串行调用次数。

可选限制 `chip,quant,framework,form,cpu,parallel`，留空表示接受基线原有配置；`modality` 默认文本。`rate` 可空，填写单位请求/秒；`growth` 为增长百分数默认0，`spare` 为额外备用完整部署组默认0。可选 `theoryServer` 用于明确理论文件中的硬件配置身份，不能仅凭芯片系列认定服务器配置相同。

实测网页项目的demand对象可直接作为需求输入。字段规范与现有网页一致；CLI允许硬件等限制为空。

## 自动理论预算

模型仓库配置可另用 `--model-config` 导入，身份绑定、上下文及KV辅助检查见[模型配置规则](model-config.md)。它是理论测算的结构输入，不要求用户另行提供理论JSON。工具1.5.0兼容以前1.0.0至1.4.0支持的证据库；旧库未包含配置时保持原有核算方式。自动提取、计算命令和支持边界见[自动理论测算](automatic-theory.md)。

仅为历史兼容及工具内部中间结果保留理论网页导入，不作为用户输入要求。接受理论网页导出 `calculationVersion=1.1.0`，含 `inputs,units,results`；单位至少明确parameters=B (10^9)、cacheBudget=KiB/Token、memory=GiB、latency=ms、compute=TFLOPS。脚本重算原输入，不擅自修改为新用户需求。来源摘要、原假设、原结果和重算结果同时保留。不支持的版本保留为未解析参考，不用于给卡数。

核算并输出内部依据及客户说明：

```bash
python scripts/sizing.py assess --library work/library.json --request work/request.json --out work/report
python scripts/sizing.py assess --library work/library.json --request work/request.json --allow-near --out work/near-report
```

除内部JSON/Markdown外，默认生成同前缀`.client.md`客户正文和`.evidence.md`依据附录，沿用已确认的Markdown模板v1.0；仅明确需要时用`--html`额外导出HTML。客户交付标准见[客户交付规范](customer-deliverable.md)。

交互入口发现需求或必要证据不完整时，先向用户集中请求补充输入并等待回复；用户明确无法提供且不调整范围后才中止。等待补充期间不调用assess生成客户报告。脚本仍保留诊断输出兼容性；意外产生的不足报告仅作内部诊断，不交付、不代表允许继续。错误JSON或非法数值退出码2，不产生半份准备数据。Python 3.10及以上，无第三方依赖。
