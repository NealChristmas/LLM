# 模型配置输入及理论预算

导入本地JSON，不执行仓库代码、auto_map、trust_remote_code，也不自动下载权重或访问链接。配置及相关实现资料是否必要取决于当前理论测算；必要结构依据缺失时暂停并请用户补充，不自行跳过理论阶段。

## 单文件及批量

```bash
python scripts/sizing.py prepare --baselines baseline.json --model-config config.json --config-model DeepSeek-V4.1-Flash --config-revision REVISION --out work/library.json
```

`--config-model`是使用者提供的模型身份绑定，不能误写为架构或系列。revision不知道可省略，文件/配置内容SHA-256仍会保留。绑定名称一致也不能证明基线所用权重修订一致。

批量配置用包装对象分别标注身份：

```json
{
  "modelName": "DEMO-Llama-Config（仅格式演示）",
  "revision": "synthetic-example",
  "config": {
    "model_type": "llama",
    "max_position_embeddings": 32768,
    "num_hidden_layers": 32,
    "hidden_size": 4096,
    "num_attention_heads": 32,
    "num_key_value_heads": 8,
    "head_dim": 128
  }
}
```

`--model-config`可给多个文件。目录仅递归查找config.json，不把generation_config、tokenizer配置或权重索引当模型结构。多个文件不要共用--config-model。一个模型存在不同内容配置时，需求中填写`modelConfigHash`选择prepare结果中的内容摘要，或只导入本次所需的一份；否则暂停采用候选。

## 做什么，不做什么

- 上下文：比较input+output与配置声明max_position_embeddings。超过时提示核对扩展依据并暂停采用；未超过也不证明框架已支持。不会重复乘rope_scaling。
- 标准缓存：当前仅允许model_type为llama/qwen2/mistral且无compress_ratios、kv_lora_rank或有效sliding_window等特殊机制时尝试估算。必须明确层数、KV头数、注意力头数和head_dim（或可整除的hidden_size/heads），并在需求量化中明确C8/C16/C32。
- 公式：每Token标准K/V张量Byte=2×层数×KV头数×head_dim×缓存位宽/8。仅估张量，不含复制、分页、索引、元数据、工作区或其他状态，不直接改写每组实测并发与吞吐。
- DeepSeek压缩、MLA、滑窗及未支持架构：只提取字段和标记未识别项，不使用普通KV公式。需要进一步提供对应实现、部署布局或缓存测量依据。
- 参数量：工具读取配置显式num_parameters/num_active_parameters（单位为参数个数），按目标权重位宽估算纯权重张量占用，按两倍激活参数量估算每词元线性层计算量。不包含额外算子、量化元数据及运行开销。没有声明则由智能体核对同版本实现或张量清单，不粗乘结构尺寸。
- 完整理论卡数：还需要硬件、有效能力与部署布局；由智能体取得有来源的参数并调用工具，用户无需预计算或上传理论JSON。步骤见[自动理论测算](automatic-theory.md)。
- 精度：torch_dtype/quantization_config/expert_dtype是配置声明，不能据此直接确认实际驻留显存、KV精度或部署可用性。源权重与目标量化不同需验证转换，不自动否定适配权重。
- text_config：可展示子配置，但不计多模态额外模块与图像/音频Token；不能宣称完整多模态容量已覆盖。

所有字段与结果均进入JSON及Markdown“模型配置依据”部分。配置与基线、理论依据分开，不把理论张量占用当完整实测显存，更不把配置文件当性能测试。
