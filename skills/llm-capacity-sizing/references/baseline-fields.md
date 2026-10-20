# 统一基线字段规范 v1.0

后续新基线使用同一份JSON契约：[字段Schema](../schemas/baseline-import-v1.schema.json)、[完整示例](../examples/baselines.standard-v1.json)。示例来自记录182930及用户确认，负载仍未知、verified仍为false，不能当作已核验的达标基线。

## 文件结构

文件顶层固定包含`type`、`schemaVersion`、`records`。type固定为`llm-capacity-baselines`，schemaVersion固定为`1.0`。records为数组，一项对应一个**同一模型、同一部署、同一负载、同一并发档位的测试点**。不同并发或不同长度应另建记录，不能混取各次测试的最好指标。

每项分为`raw`与`meta`：raw保存基线事实，meta保存测试口径和核对依据。新格式中的内嵌字段使用JSON对象，数值使用JSON数字，不再用字符串包裹JSON或数字。原性能地图格式继续走兼容导入。

## raw：基线事实

下列路径均相对于每项记录的raw。

| 字段路径 | 类型、单位 | 要求与说明 |
| --- | --- | --- |
| id | 字符串或整数 | 必填，稳定唯一标识；同ID重新导入会覆盖旧记录 |
| modelName | 字符串 | 必填，完整模型名称和版本 |
| modalityType | 字符串 | 必填，本工具当前核算范围为文本 |
| bizLoadFeature.输入输出序列长度 | 字符串 | 必填，如`16000/1000`；优先填完整词元数。保留`16K/1K`时必须明确meta.kBase才可核算 |
| deployConfig.芯片型号 | 字符串 | 必填，完整型号，如`A3-560T`，不能仅写A3 |
| deployConfig.CPU架构 | 字符串 | 必填，如ARM |
| deployConfig.部署卡数 | 正整数，卡 | 必填；用于核算时必须是完整部署组总卡数，范围由meta.cardCountScope确认 |
| deployConfig.部署形态 | 字符串 | 必填，保留原测试名称，如PD分离；与需求匹配 |
| deployConfig.量化格式 | 字符串 | 必填，包含权重、激活和缓存格式，如W8A8C16 |
| deployConfig.推理框架 | 字符串 | 必填，框架名称及完整版本 |
| perfData.并发数 | 正整数，请求数 | 必填，与本条延迟、吞吐来自同一测试点 |
| perfData.Prefix Cache命中率 | 数字0～100或null，百分数 | 字段必填；0代表确实为零，null代表未知 |
| perfData.TTFT(ms) | 正数，毫秒 | 必填，首词元延迟；统计方式由meta.ttftStat声明 |
| perfData.TPOT(ms) | 正数，毫秒/词元 | 必填，逐词元生成耗时；统计方式由meta.tpotStat声明 |
| perfData.单卡输出吞吐TPS / 单卡E2E吞吐TPS | 非负数或null，词元/秒/卡 | 可选，仅保留来源指标，不作为请求吞吐 |
| perfData.E2E时延(ms) | 非负数或null，毫秒 | 可选，端到端请求时延 |
| optimization.并行策略 | 字符串 | 字段必填；未知可空，不从总卡数反推。应能复现原并行方式 |
| tuningStatus | 字符串 | 字段必填，保留“性能调优中”等真实状态，未知可空 |
| updateTime | 字符串 | 可选，原记录更新时间；保留原时间口径，不擅自加时区 |

raw允许保留镜像、报告地址、原始扁平字段和其他来源信息。若保留了扁平字段，它们必须与内嵌字段一致，否则不能采用该记录。保留来源链接不代表工具会访问内网或执行启动命令。

## meta：测试口径与人工确认

下列字段固定为同一套枚举，不能将“低时延”填写为统计方式。

| 字段 | 允许值 | 含义 |
| --- | --- | --- |
| ttftStat | unknown / mean / p95 / p99 / max | TTFT统计方式，字段必填 |
| tpotStat | unknown / mean / p95 / p99 / max | TPOT统计方式，字段必填；与TTFT分别确认 |
| load | unknown / closed / burst / arrival | 未知 / 固定并发闭环 / 同批突发 / 持续请求到达，字段必填 |
| kBase | unknown / 1000 / 1024 | 字符串枚举，字段必填；完整词元数无需K换算 |
| lengthStat | unknown / fixed / max / mean | 长度统计：未知 / 固定 / 最大 / 平均，字段必填 |
| reasoning | unknown / included / excluded | 输出是否包含全部推理词元，字段必填 |
| cardCountScope | unknown / total / per_stage | 卡数范围：未知 / 两侧总计 / 仅单侧，字段必填；只有total能直接用于整组复制 |
| qps | 正数或null，请求/秒 | 字段必填；须为同测试点请求吞吐，未知填null，不能填0或用词元吞吐代替 |
| source | 字符串 | 字段必填；报告编号、材料路径或用户确认来源。未确认时可空 |
| verified | 布尔值true/false | 字段必填；整体核对完成才置true，且source不能为空；不能自动写true |
| prefillCards | 正整数或null，卡 | 可选，输入侧实际卡数；未知填null |
| decodeCards | 正整数或null，卡 | 可选，生成侧实际卡数；已知两侧卡数且cardCountScope=total时，相加必须等于总卡数 |
| rawHash | 64位小写十六进制字符串 | 可选，标准化后raw对象的内容摘要；与旧字符串包裹格式的摘要不同，不直接复用旧值 |

unknown是一个真实状态。缺少口径允许入库，但**导入成功不等于可以核算**。数据与需求不匹配时仅作参考；口径未确认时保留待确认；不会默认采用P95、K=1024、固定长度或闭环压测。

## 使用与维护

```bash
python scripts/sizing.py prepare --baselines examples/baselines.standard-v1.json --out work/library.json
python scripts/sizing.py assess --library work/library.json --request request.json --out work/report
```

新格式由schemas/baseline-import-v1.schema.json校验字段类型、必填项、枚举与范围，再检查原始字段冲突及卡数关系。顶层、记录包装和meta不接受未定义字段，防止拼写错误被静默忽略；raw保留扩展来源信息。

字段中文名、JSON路径、单位和枚举在v1.0内保持一致。未来需要不兼容修改时新增schemaVersion及映射，不能悄悄改现有字段含义。旧性能地图、JSONL和网页导出项目保持兼容，口径仍通过独立annotations补齐。导入目录应只放基线数据，Schema与用户需求不要混入该目录。
