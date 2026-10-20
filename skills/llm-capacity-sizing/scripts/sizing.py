#!/usr/bin/env python3
"""Offline inference sizing. Python standard library only; never executes record contents."""
import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.5.0"
SAFE = 2**53 - 1
ENUMS = {
    "ttftStat": {"unknown", "mean", "p95", "p99", "max"},
    "tpotStat": {"unknown", "mean", "p95", "p99", "max"},
    "load": {"unknown", "closed", "burst", "arrival"},
    "kBase": {"unknown", "1000", "1024"},
    "lengthStat": {"unknown", "fixed", "max", "mean"},
    "reasoning": {"unknown", "included", "excluded"},
}
REQUIRED = ["model", "input", "output", "concurrency", "ttft", "tpot",
            "ttftStat", "tpotStat", "load", "lengthStat", "reasoning", "prefix"]


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(v):
    return "" if v is None else str(v).strip()


def num(v, name, minimum=0, strict=True, integer=False):
    if isinstance(v, bool) or v is None or clean(v) == "":
        raise ValueError(f"{name}缺少有效数值")
    try:
        n = float(v)
    except (ValueError, TypeError):
        raise ValueError(f"{name}不是数值") from None
    if not math.isfinite(n) or (n <= minimum if strict else n < minimum):
        raise ValueError(f"{name}超出有效范围")
    if integer:
        if not n.is_integer() or abs(n) > SAFE:
            raise ValueError(f"{name}必须为安全整数")
        return int(n)
    return n


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def record_key(raw):
    return "id:" + clean(raw["id"]) if clean(raw.get("id")) else "content:" + digest(raw)


def read_json(path):
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = [x for x in text.splitlines() if x.strip()]
        if len(lines) < 2:
            raise ValueError(f"{path}: JSON格式错误") from None
        try:
            return [json.loads(x) for x in lines]
        except json.JSONDecodeError:
            raise ValueError(f"{path}: JSON/JSONL格式错误") from None


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(p)


def embedded(raw, field):
    v = raw.get(field)
    if v is None or v == "":
        return {}
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            raise ValueError(field + "内嵌JSON格式错误") from None
    if not isinstance(v, dict):
        raise ValueError(field + "应为对象或JSON字符串")
    return v


def normalize(raw):
    if not isinstance(raw, dict):
        raise ValueError("基线记录必须为对象")
    dep, perf, biz, opt = [embedded(raw, x) for x in
                            ("deployConfig", "perfData", "bizLoadFeature", "optimization")]
    conflicts = []

    def pick(field, nested):
        a, b = clean(raw.get(field)), clean(nested)
        if a and b and a != b:
            try:
                equal = math.isfinite(float(a)) and float(a) == float(b)
            except ValueError:
                equal = False
            if not equal:
                conflicts.append(field + "与内嵌字段冲突")
        return a or b

    fields = {
        "chip": ("keyChipModel", dep.get("芯片型号")),
        "quant": ("keyQuantizationFormat", dep.get("量化格式")),
        "framework": ("keyInferenceFramework", dep.get("推理框架")),
        "form": ("keyDeploymentForm", dep.get("部署形态")),
        "io": ("keyIoSeqLen", biz.get("输入输出序列长度")),
        "cards": ("keyDeploymentCardCount", dep.get("部署卡数")),
        "concurrency": ("keyConcurrency", perf.get("并发数")),
        "ttft": ("keyTtft", perf.get("TTFT(ms)")),
        "tpot": ("keyTpot", perf.get("TPOT(ms)")),
        "prefix": ("keyPrefixCacheHitRate", perf.get("Prefix Cache命中率")),
    }
    b = {k: pick(*v) for k, v in fields.items()}
    b.update(model=clean(raw.get("modelName")), cpu=clean(dep.get("CPU架构")),
             modality=clean(raw.get("modalityType")), parallel=clean(opt.get("并行策略")),
             status=clean(raw.get("tuningStatus")) or "未提供",
             updated=clean(raw.get("updateTime")) or clean(raw.get("releaseDate")),
             conflicts=conflicts)
    if not b["model"]:
        raise ValueError("缺少modelName")
    for k in ("cards", "concurrency", "ttft", "tpot"):
        b[k] = num(b[k], k, integer=k in {"cards", "concurrency"})
    b["prefix"] = num(b["prefix"].rstrip("%"), "prefix", strict=False) if b["prefix"] else None
    if b["prefix"] is not None and b["prefix"] > 100:
        raise ValueError("缓存命中率不能大于100%")
    return b


def meta_defaults():
    return dict.fromkeys(ENUMS, "unknown") | {"qps": "", "source": "", "verified": False}


def validate_meta(v):
    if not isinstance(v, dict):
        raise ValueError("核对信息必须为对象")
    m = meta_defaults() | v
    for k, values in ENUMS.items():
        if m[k] not in values:
            raise ValueError(k + "口径枚举无效")
    if type(m["verified"]) is not bool or not isinstance(m["source"], str):
        raise ValueError("verified必须为布尔值，source必须为文本")
    if clean(m["qps"]):
        num(m["qps"], "实测请求吞吐")
    return m


def unpack(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if value.get("modelName"):
            return [value]
        for key in ("data", "records", "list", "items", "rows", "results"):
            if key in value:
                try:
                    return unpack(value[key])
                except ValueError:
                    pass
    raise ValueError("没有找到基线记录列表")


def files(paths):
    found = []
    for name in paths or []:
        p = Path(name)
        candidates = sorted(x for x in p.rglob("*") if x.suffix.lower() in {".json", ".jsonl", ".ndjson"}) if p.is_dir() else [p]
        found.extend(candidates)
    return list(dict.fromkeys(x.resolve() for x in found))


def import_model_config(path, model="", revision=""):
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError("模型配置必须为JSON对象: " + str(path))
    config = value.get("config", value)
    if not isinstance(config, dict):
        raise ValueError("模型config必须为对象")
    identity = clean(value.get("modelName")) if "config" in value else ""
    if model and identity and model != identity:
        raise ValueError("配置绑定的模型名与--config-model冲突")
    model = model or identity
    return {"modelName": model, "revision": revision or (clean(value.get("revision")) if "config" in value else ""),
            "config": config, "source": {"path": str(Path(path).resolve()),
                                          "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()},
            "configHash": digest(config)}


def model_config_evidence(item, d, missing):
    raw = item["config"]
    config = raw.get("text_config", raw)
    evidence = {"source": item["source"], "modelName": item.get("modelName", ""),
                "revision": item.get("revision", ""), "configHash": digest(raw),
                "state": "reference", "notes": [], "fields": {}, "checks": {}, "derived": {}}
    if not isinstance(config, dict):
        evidence["notes"].append("text_config不是对象，不能分析")
        return evidence
    relevant = ["model_type", "architectures", "max_position_embeddings", "num_hidden_layers",
                "hidden_size", "intermediate_size", "num_attention_heads", "num_key_value_heads", "head_dim",
                "n_routed_experts", "num_local_experts", "num_experts_per_tok", "n_shared_experts",
                "moe_intermediate_size", "sliding_window", "compress_ratios", "kv_lora_rank", "torch_dtype",
                "dtype", "quantization_config", "expert_dtype", "num_parameters", "num_active_parameters", "rope_scaling", "auto_map"]
    evidence["fields"] = {k: config[k] for k in relevant if k in config}
    if config is not raw:
        evidence["fields"].update({"root." + k: raw[k] for k in ("model_type", "architectures", "dtype", "quantization_config") if k in raw})
        if "quantization_config" in raw:
            evidence["notes"].append("根配置的源权重量化格式已保留；不等于目标部署量化，转换及框架支持须另行核对")
        evidence["notes"].append("读取text_config子配置；多模态额外输入和模块不在本次估算范围内")
    if not item.get("modelName"):
        evidence["notes"].append("没有显式模型身份绑定，不能仅凭model_type或文件夹名认定对应用户模型")
        return evidence
    if missing or item["modelName"] != d.get("model"):
        evidence["notes"].append("模型配置身份与用户需求不同或需求未补齐，仅作参考")
        return evidence
    evidence["state"] = "associated"
    evidence["notes"].append("模型名称绑定一致不等于权重修订一致；需核对基线实际权重revision或摘要")
    limit = config.get("max_position_embeddings")
    if limit is not None:
        try:
            limit = num(limit, "max_position_embeddings", integer=True)
            requested = d["input"] + d["output"]
            evidence["checks"]["context"] = {"requested": requested, "declaredLimit": limit,
                                               "withinDeclaredLimit": requested <= limit}
            if requested > limit:
                evidence["state"] = "context_conflict"
                evidence["notes"].append("输入加输出超过配置声明上下文；需提供上下文扩展及部署支持依据，当前候选暂停采用")
            else:
                evidence["notes"].append("长度未超过配置声明；不代表推理框架、位置编码或部署已支持该长度")
        except ValueError as exc:
            evidence["notes"].append(str(exc) + "，不进行上下文上限判断")
    else:
        evidence["notes"].append("未声明上下文上限，不推断无限上下文")
    special = any(config.get(k) for k in ("compress_ratios", "kv_lora_rank", "sliding_window", "auto_map")) or bool(raw.get("auto_map"))
    model_type = clean(config.get("model_type"))
    expected_arch = {"llama": "LlamaForCausalLM", "qwen2": "Qwen2ForCausalLM", "mistral": "MistralForCausalLM"}
    if config.get("architectures") and config["architectures"] != [expected_arch.get(model_type)]:
        special = True
    if special or model_type not in {"llama", "qwen2", "mistral"}:
        evidence["notes"].append("特殊或未支持的缓存架构：不套通用KV公式，需模型实现/压测缓存依据")
    else:
        precision = re.search(r"C(8|16|32)$", d.get("quant", ""))
        try:
            if not precision:
                raise ValueError("需求量化未明确缓存位宽，不从torch_dtype推定KV精度")
            layers = num(config.get("num_hidden_layers"), "层数", integer=True)
            kv_heads = num(config.get("num_key_value_heads"), "KV头数", integer=True)
            heads = num(config.get("num_attention_heads"), "注意力头数", integer=True)
            if kv_heads > heads or heads % kv_heads:
                raise ValueError("注意力头数与KV头数不满足标准分组关系")
            dim = config.get("head_dim")
            if dim is None:
                hidden = num(config.get("hidden_size"), "隐藏维度", integer=True)
                if hidden % heads:
                    raise ValueError("隐藏维度不能整除头数，不能推导head_dim")
                dim = hidden // heads
            dim = num(dim, "head_dim", integer=True)
            bits = int(precision[1])
            per_token = 2 * layers * kv_heads * dim * bits / 8
            evidence["derived"]["standardKv"] = {
                "formula": "2 × 层数 × KV头数 × head_dim × 缓存位宽/8",
                "substitution": f"2 × {layers} × {kv_heads} × {dim} × {bits}/8",
                "bytesPerToken": per_token, "bytesPerRequest": per_token * (d["input"] + d["output"]),
                "scope": "仅标准K/V张量，未计分页、索引、复制、对齐、量化元数据与其他状态，不用于替换实测能力"}
        except ValueError as exc:
            evidence["notes"].append(str(exc))
    # Only explicitly declared counts are usable here. Complex architecture counts
    # require a separate implementation/tensor inventory, never hidden*layers.
    try:
        counts = {}
        for key in ("num_parameters", "num_active_parameters"):
            if config.get(key) is not None:
                counts[key] = num(config[key], key, integer=True)
        if counts.get("num_active_parameters", 0) > counts.get("num_parameters", SAFE):
            raise ValueError("激活参数量超过总参数量")
        if counts:
            evidence["derived"]["declaredParameters"] = counts
        weight_bits = re.fullmatch(r"W(4|8|16)A\d+(?:C(?:8|16|32))?", d.get("quant", ""))
        if counts.get("num_parameters") and weight_bits:
            evidence["derived"]["weightTensorBytes"] = counts["num_parameters"] * int(weight_bits[1]) / 8
        if counts.get("num_active_parameters"):
            evidence["derived"]["linearFlopsPerToken"] = 2 * counts["num_active_parameters"]
    except ValueError as exc:
        evidence["notes"].append("参数量声明不可用：" + str(exc))
    evidence["notes"].append("理论预算自动读取显式参数量声明；不含声明时需核对模型实现或张量清单，不把结构尺寸粗乘当参数量")
    if config.get("quantization_config") or config.get("expert_dtype"):
        evidence["notes"].append("配置声明的是源权重格式；部署量化可能经过转换，需核对实际权重与后端支持")
    return evidence


def validate_import_schema(value, schema, path='$'):
    """Validate the concrete JSON Schema features used by the fixed v1 contract."""
    kinds = schema.get('type', [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    matches = {'null': value is None, 'boolean': type(value) is bool,
               'integer': type(value) is int, 'number': type(value) in (int, float) and math.isfinite(value),
               'string': isinstance(value, str), 'object': isinstance(value, dict), 'array': isinstance(value, list)}
    if kinds and not any(matches.get(k, False) for k in kinds):
        raise ValueError(f'{path}字段类型错误，应为{"/".join(kinds)}')
    if 'const' in schema and value != schema['const']:
        raise ValueError(f'{path}必须为{schema["const"]}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{path}枚举无效，允许值为{schema["enum"]}')
    if isinstance(value, dict):
        missing = set(schema.get('required', [])) - set(value)
        if missing:
            raise ValueError(f'{path}缺少字段：{", ".join(sorted(missing))}')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError(f'{path}含未定义字段：{", ".join(sorted(set(value) - set(props)))}')
        for k, v in value.items():
            if k in props:
                validate_import_schema(v, props[k], path + '.' + k)
    elif isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            raise ValueError(path + '记录列表不能为空')
        for index, item in enumerate(value):
            validate_import_schema(item, schema.get('items', {}), f'{path}[{index}]')
    elif isinstance(value, str):
        if len(value.strip()) < schema.get('minLength', 0):
            raise ValueError(path + '不能为空')
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            raise ValueError(path + '格式不符合约定')
    elif type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError(path + '必须为有限数值')
        if 'minimum' in schema and value < schema['minimum'] or 'maximum' in schema and value > schema['maximum'] or 'exclusiveMinimum' in schema and value <= schema['exclusiveMinimum']:
            raise ValueError(path + '数值超出允许范围')


def validate_standard_conditions(raw, meta):
    validate_meta(meta)
    if meta.get('rawHash') and meta['rawHash'] != digest(raw):
        raise ValueError('标准基线rawHash与当前raw内容摘要不一致')
    if meta['verified'] and not clean(meta['source']):
        raise ValueError('标准基线verified=true时，必须填写source核对依据')
    if not clean(raw.get('id')):
        raise ValueError('标准基线id不能为空')
    if io_lengths(embedded(raw, 'bizLoadFeature').get('输入输出序列长度', ''), meta['kBase']) is None and meta['kBase'] != 'unknown':
        raise ValueError('标准基线输入输出序列长度与K换算无效')
    pre, dec = meta.get('prefillCards'), meta.get('decodeCards')
    if meta['cardCountScope'] == 'total' and pre is not None and dec is not None and pre + dec != raw['deployConfig']['部署卡数']:
        raise ValueError('输入侧卡数＋生成侧卡数与总部署卡数冲突')


def prepare(args):
    records, sources, theories, configs = {}, [], [], []
    for path in files(args.baselines):
        data = read_json(path)
        source = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        sources.append(source)
        standard = isinstance(data, dict) and data.get('type') == 'llm-capacity-baselines'
        if standard:
            schema = read_json(Path(__file__).resolve().parent.parent / 'schemas/baseline-import-v1.schema.json')
            validate_import_schema(data, schema)
            incoming = [(x['raw'], x['meta']) for x in data['records']]
        elif isinstance(data, dict) and 'schemaVersion' in data:
            raise ValueError('无法识别的基线格式type或schemaVersion；请使用llm-capacity-baselines/1.0')
        elif isinstance(data, dict) and data.get("type") == "baseline-sizing-project":
            incoming = [(x["raw"], x.get("meta", {})) for x in data["records"]]
        else:
            incoming = [(x, {}) for x in unpack(data)]
        for raw, meta in incoming:
            if standard:
                validate_standard_conditions(raw, meta)
            b = normalize(raw)
            key = record_key(raw)
            records[key] = {"key": key, "raw": raw, "normalized": b, "rawHash": digest(raw),
                            "meta": validate_meta(meta), "source": source}
            if standard:
                records[key]['inputSchema'] = 'llm-capacity-baselines/1.0'
    if args.annotations:
        annotations = read_json(args.annotations)
        if not isinstance(annotations, dict):
            raise ValueError("annotations必须为按记录key索引的对象")
        for key, value in annotations.items():
            if key not in records:
                raise ValueError("注释找不到对应记录: " + key)
            if value.get("rawHash") and value["rawHash"] != records[key]["rawHash"]:
                raise ValueError("注释与记录内容摘要不一致: " + key)
            if records[key].get('inputSchema'):
                combined = records[key]['meta'] | value
                schema = read_json(Path(__file__).resolve().parent.parent / 'schemas/baseline-import-v1.schema.json')
                validate_import_schema(combined, schema['properties']['records']['items']['properties']['meta'])
                validate_standard_conditions(records[key]['raw'], combined)
                records[key]['meta'] = validate_meta(combined)
            else:
                records[key]["meta"] = validate_meta(value)
    for path in files(args.theory):
        theories.append({"source": {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
                         "raw": read_json(path)})
    paths = []
    for name in getattr(args, "model_config", None) or []:
        p = Path(name)
        paths.extend(sorted(p.rglob("config.json")) if p.is_dir() else [p])
    paths = list(dict.fromkeys(x.resolve() for x in paths))
    if len(paths) > 1 and getattr(args, "config_model", ""):
        raise ValueError("多配置请逐个用modelName包装，不能统一绑定同一模型")
    for path in paths:
        configs.append(import_model_config(path, getattr(args, "config_model", ""), getattr(args, "config_revision", "")))
    if not records and not theories and not configs:
        raise ValueError("至少提供实测基线、理论结果或模型配置之一")
    library = {"type": "capacity-evidence-library", "version": VERSION, "createdAt": now(),
               "records": list(records.values()), "theories": theories, "modelConfigs": configs, "sources": sources}
    write_json(args.out, library)
    missing = {k: sum(x["meta"][k] == "unknown" for x in records.values()) for k in ENUMS}
    return {"library": str(Path(args.out).resolve()), "records": len(records), "theories": len(theories), "modelConfigs": len(configs),
            "unknownMetadata": missing, "models": sorted({x["normalized"]["model"] for x in records.values()}),
            "configModels": sorted({x["modelName"] for x in configs if x["modelName"]})}


def request_template():
    return {"project": "", "model": None, "chip": "", "quant": "", "framework": "",
            "form": "", "cpu": "", "parallel": "", "modality": "文本", "input": None,
            "output": None, "concurrency": None, "ttft": None, "tpot": None,
            "ttftStat": "unknown", "tpotStat": "unknown", "load": "unknown",
            "lengthStat": "unknown", "reasoning": "unknown", "prefix": None,
            "rate": None, "growth": 0, "spare": 0, "theoryServer": "", "modelConfigHash": ""}


def demand(raw):
    if not isinstance(raw, dict):
        raise ValueError("用户规格必须为对象")
    raw = raw.get("demand", raw)
    d = request_template() | raw
    missing = [k for k in REQUIRED if d.get(k) is None or clean(d[k]) in {"", "unknown"}]
    if missing:
        return d, missing
    for k in ("input", "output", "concurrency", "ttft", "tpot", "prefix", "growth", "spare"):
        d[k] = num(d[k], k, strict=k not in {"prefix", "growth", "spare"},
                   integer=k in {"input", "output", "concurrency", "spare"})
    if d["prefix"] > 100:
        raise ValueError("prefix不能大于100%")
    for k, values in ENUMS.items():
        if k in d and d[k] not in values:
            raise ValueError("用户规格" + k + "无效")
    for k in ("model", "chip", "quant", "framework", "form", "cpu", "parallel", "modality", "theoryServer", "modelConfigHash"):
        d[k] = clean(d[k])
    d["rate"] = None if d["rate"] is None or clean(d["rate"]) == "" else num(d["rate"], "rate")
    d["plannedConcurrency"] = math.ceil(d["concurrency"] * (1 + d["growth"] / 100))
    d["plannedRate"] = None if d["rate"] is None else d["rate"] * (1 + d["growth"] / 100)
    if d["plannedConcurrency"] > SAFE or d["plannedRate"] is not None and not math.isfinite(d["plannedRate"]):
        raise ValueError("规划负载超出安全范围")
    return d, []


def io_lengths(text, base):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kKmM]?)/(\d+(?:\.\d+)?)([kKmM]?)", re.sub(r"\s", "", text))
    if not m or (m[2] or m[4]) and base not in {"1000", "1024"}:
        return None
    def cv(n, u):
        return float(n) * (1 if not u else int(base) ** (1 if u.lower() == "k" else 2))
    a, b = cv(m[1], m[2]), cv(m[3], m[4])
    return [int(a), int(b)] if all(math.isfinite(n) and n.is_integer() and 0 < n <= SAFE for n in (a, b)) else None


def evaluate(record, d, allow_near=False):
    b, m = normalize(record["raw"]), validate_meta(record.get("meta", {}))
    diff, pending, failed, notes = [], [], [], []
    if 'cardCountScope' in m or record.get('inputSchema'):
        if m.get('cardCountScope') != 'total':
            pending.append('部署卡数尚未确认是输入与生成两侧的总卡数')
        pre, dec = m.get('prefillCards'), m.get('decodeCards')
        if pre is not None and dec is not None and m.get('cardCountScope') == 'total' and pre + dec != b['cards']:
            pending.append('输入侧卡数＋生成侧卡数与总部署卡数冲突')
    for k in ("model", "chip", "quant", "framework", "form", "cpu", "modality"):
        if not b[k]:
            pending.append("基线缺少" + k)
        elif d[k] and d[k] != b[k]:
            diff.append(k + "不匹配: " + b[k])
    if d["parallel"]:
        if not b["parallel"]:
            pending.append("缺少并行策略")
        elif b["parallel"] != d["parallel"]:
            diff.append("并行策略不匹配")
    lengths = io_lengths(b["io"], m["kBase"])
    shorter = False
    if lengths is None:
        pending.append("输入输出长度或K换算未知")
    elif lengths != [d["input"], d["output"]]:
        shorter = d["input"] <= lengths[0] and d["output"] <= lengths[1]
        if shorter:
            notes.append(f"用户长度{d['input']}/{d['output']}短于基线{lengths[0]}/{lengths[1]}；不提高原并发容量")
        else:
            diff.append("用户至少一项长度超过基线，不能外推")
    if b["prefix"] is None:
        pending.append("缓存命中率未知")
    elif b["prefix"] != d["prefix"]:
        diff.append("缓存命中率不匹配")
    for key in ("ttftStat", "tpotStat", "load", "lengthStat", "reasoning"):
        if m[key] == "unknown":
            pending.append(key + "未知")
        elif m[key] != d[key]:
            diff.append(key + "不匹配")
    for metric in ("ttft", "tpot"):
        if m[metric + "Stat"] == d[metric + "Stat"] and b[metric] > d[metric]:
            failed.append(f"{metric}={b[metric]}超过目标{d[metric]}")
    if not m["verified"] or not clean(m["source"]):
        pending.append("缺少测试报告人工核对依据")
    pending.extend(b["conflicts"])
    qps = num(m["qps"], "qps") if clean(m["qps"]) else None
    if d["plannedRate"] is not None and qps is None:
        pending.append("缺少同测试点实测请求吞吐")
    state = "reference" if diff else "failed" if failed else "pending" if pending else "near_reference" if shorter else "measured_match"
    result = None
    if state == "measured_match" or state == "near_reference" and allow_near:
        cg = math.ceil(d["plannedConcurrency"] / b["concurrency"])
        rg = math.ceil(d["plannedRate"] / qps) if d["plannedRate"] is not None else 0
        work = max(1, cg, rg)
        cards = (work + d["spare"]) * b["cards"]
        if cards > SAFE:
            raise ValueError("核算卡数超出安全范围")
        result = {"concurrencyGroups": cg, "rateGroups": rg, "workGroups": work, "spareGroups": d["spare"],
                  "cardsPerGroup": b["cards"], "workCards": work * b["cards"],
                  "spareCards": d["spare"] * b["cards"], "totalCards": cards}
    elif state == "near_reference":
        notes.append("尚未启用--allow-near，仅列差异，不输出近似卡数")
    return {"key": record["key"], "baseline": b, "metadata": m, "source": record.get("source"),
            "rawHash": digest(record["raw"]), "state": state, "reasons": diff + failed + pending,
            "notes": notes, "result": result}


def theory_compute(v):
    positive = ["total", "active", "parallel", "bytes", "cache", "cacheLength", "memory", "usable",
                "peak", "prefillEfficiency", "decodeEfficiency", "timeBudget", "group", "slots",
                "concurrency", "input", "output", "ttft", "tpot"]
    ints = {"parallel", "group", "slots", "concurrency", "input", "output", "cacheLength"}
    x = {k: num(v.get(k), k, integer=k in ints) for k in positive}
    x.update({k: num(v.get(k), k, strict=False, integer=k == "spare")
              for k in ("growth", "weightExtra", "runtime", "spare")})
    if v.get("purpose") != "推理" or x["active"] > x["total"] or x["group"] > x["slots"]:
        raise ValueError("理论用途、参数量或部署分组无效")
    if any(x[k] > 100 for k in ("usable", "prefillEfficiency", "decodeEfficiency", "timeBudget")):
        raise ValueError("理论比例不能超过100%")
    bytes_map = {"INT8": 1, "FP8": 1, "FP16": 2, "BF16": 2}
    if v.get("kv") not in bytes_map or v.get("cachePrecision") not in bytes_map:
        raise ValueError("理论缓存精度未知")
    standard = {"W8A8": 1, "W4A16": .5, "FP16/BF16": 2}
    if v.get("quant") in standard and x["bytes"] != standard[v["quant"]]:
        raise ValueError("理论权重精度与字节数冲突")
    c = math.ceil(x["concurrency"] * x["parallel"] * (1 + x["growth"] / 100))
    f, t = 2 * x["active"] / 1000, x["ttft"] / 1000 * x["timeBudget"] / 100
    fp, fd = c * x["input"] * f / t, c * f * 1000 / x["tpot"]
    sp, sd = x["peak"] * x["prefillEfficiency"] / 100, x["peak"] * x["decodeEfficiency"] / 100
    compute_cards = math.ceil(fp / sp + fd / sd)
    weight = x["total"] * 1e9 * x["bytes"] * (1 + x["weightExtra"] / 100) / 2**30
    cache = x["cache"] * (x["input"] + x["output"]) / 1024**2 * bytes_map[v["kv"]] / bytes_map[v["cachePrecision"]]
    available = x["group"] * (x["memory"] * x["usable"] / 100 - x["runtime"])
    memory_capacity = max(0, math.floor((available - weight) / cache))
    compute_capacity = math.floor(1 / ((x["input"] * f / t) / (x["group"] * sp) + (f * 1000 / x["tpot"]) / (x["group"] * sd)))
    if memory_capacity < 1 or compute_capacity < 1:
        raise ValueError("理论完整副本不能承接至少一个请求")
    replicas = max(math.ceil(c / memory_capacity), math.ceil(compute_cards / x["group"]), math.ceil(c / compute_capacity))
    cards = (replicas + x["spare"]) * x["group"]
    if cards > SAFE:
        raise ValueError("理论结果超出安全范围")
    return {"c": c, "weight": weight, "cache": cache, "available": available, "fp": fp, "fd": fd,
            "computeCards": compute_cards, "memoryCapacity": memory_capacity, "computeCapacity": compute_capacity,
            "replicas": replicas, "cards": cards, "workCards": replicas * x["group"],
            "servers": math.ceil((replicas + x["spare"]) / math.floor(x["slots"] / x["group"]))}


def theory_evidence(item, d, missing):
    raw = item["raw"]
    evidence = {"source": item["source"], "state": "reference", "notes": [], "original": raw}
    units = {"parameters": "B (10^9)", "cacheBudget": "KiB/Token", "memory": "GiB", "latency": "ms", "compute": "TFLOPS"}
    if not isinstance(raw, dict) or raw.get("calculationVersion") != "1.1.0":
        evidence["notes"].append("不支持的理论公式版本，仅保留原始依据")
        return evidence
    if not isinstance(raw.get("units"), dict) or any(raw["units"].get(k) != v for k, v in units.items()):
        evidence["notes"].append("理论单位不完整或不匹配，不能定量复用")
        return evidence
    try:
        v = raw["inputs"]
        if not isinstance(v, dict) or not isinstance(raw.get("results", {}), dict):
            raise ValueError("理论inputs/results必须为对象")
        computed = theory_compute(v)
        evidence["recomputed"] = computed
        original = raw.get("results", {})
        for k, value in computed.items():
            if k in original and not math.isclose(num(original[k], k, strict=False), value, rel_tol=1e-8, abs_tol=1e-8):
                evidence["state"] = "inconsistent"
                evidence["notes"].append("原理论结果与当前重算不一致: " + k)
        if evidence["state"] == "inconsistent" or missing:
            return evidence
        diffs = []
        if v.get("model") != d["model"]:
            diffs.append("理论模型版本与需求不同")
        for k in ("input", "output", "ttft", "tpot"):
            if float(v[k]) != d[k]:
                diffs.append("理论" + k + "与需求不同")
        if computed["c"] != d["plannedConcurrency"]:
            diffs.append("理论规划模型并发与需求不同")
        # Theory 1.1.0 models a burst at maximum lengths, counts all generated tokens, and uses no prefix savings.
        expected = {"load": "burst", "lengthStat": "max", "reasoning": "included", "prefix": 0,
                    "ttftStat": "p95", "tpotStat": "p95", "modality": "文本"}
        for k, value in expected.items():
            if d[k] != value:
                diffs.append("理论适用口径与需求不同: " + k)
        declared = raw.get("configuration", {})
        if not isinstance(declared, dict):
            raise ValueError("理论configuration必须为对象")
        for k in ("chip", "framework", "form", "cpu", "parallel"):
            if d[k] and declared.get(k) != d[k]:
                diffs.append("理论缺少对应配置身份或不匹配: " + k)
        quant = v.get("quant", "")
        if quant in {"W8A8", "W4A16"}:
            quant += "C" + str({"INT8": 8, "FP8": 8, "FP16": 16, "BF16": 16}[v["kv"]])
        if d["quant"] and d["quant"] not in {quant, v.get("quant")}:
            diffs.append("理论量化与需求不同")
        if d["theoryServer"] and d["theoryServer"] != v.get("server"):
            diffs.append("理论服务器身份与需求不同")
        if d["rate"] is not None:
            diffs.append("原理论不覆盖持续请求速率")
        evidence["notes"].extend(diffs)
        evidence["state"] = "reference" if diffs else "compatible_assumptions"
        if not diffs:
            evidence["candidate"] = {"workCards": computed["workCards"], "spareCards": d["spare"] * v["group"],
                                     "totalCards": computed["workCards"] + d["spare"] * v["group"]}
        evidence["notes"].append("有效能力和KV预算仍为原理论假设，不是实测；不与基线结果机械平均或取最大值")
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError) as exc:
        evidence["state"] = "unusable"
        evidence["notes"].append("理论无法重算: " + str(exc))
    return evidence


def assess(library, request, allow_near=False):
    if library.get("type") != "capacity-evidence-library" or library.get("version") not in {"1.0.0", "1.0.1", "1.1.0", "1.2.0", "1.3.0", "1.4.0", VERSION}:
        raise ValueError("不兼容的证据库格式，请重新prepare")
    d, missing = demand(request)
    # Stage 1 is independent of baseline capacity: never backfill theoretical inputs.
    theories = [theory_evidence(x, d, missing) for x in library.get("theories", [])]
    configs = [model_config_evidence(item, d, missing) for item in library.get("modelConfigs", [])]
    config_issues = []
    if not missing:
        for item in configs:
            if d["modelConfigHash"] and item["configHash"] != d["modelConfigHash"]:
                item["state"] = "reference"
                item["notes"].append("未被用户指定的modelConfigHash选中")
        bound = [item for item in configs if item["state"] in {"associated", "context_conflict"}]
        if d["modelConfigHash"] and not bound:
            config_issues.append("用户指定的配置摘要未找到对应模型配置")
        if len({item["configHash"] for item in bound}) > 1:
            config_issues.append("存在多个同名但内容不同的模型配置，请明确modelConfigHash或只导入本次使用的一份")
        if any(item["state"] == "context_conflict" for item in bound):
            config_issues.append("需求长度超过所关联配置声明；需补充上下文扩展支持依据或修正配置/需求后重算")
    # Stage 2: reuse tested full deployment groups.
    evaluations = [] if missing else [evaluate(r, d, allow_near) for r in library["records"]]
    for e in evaluations:
        if config_issues:
            e["reasons"].extend(config_issues)
            if e["result"]:
                e["state"], e["result"] = "config_conflict", None
    exact = sorted([e for e in evaluations if e["state"] == "measured_match"], key=lambda e: e["result"]["totalCards"])
    near = sorted([e for e in evaluations if e["state"] == "near_reference" and e["result"]], key=lambda e: e["result"]["totalCards"])
    if config_issues:
        for t in theories:
            if t.get("candidate"):
                t.pop("candidate")
                t["state"] = "reference"
                t["notes"].extend(config_issues)
    compatible = [t for t in theories if t.get("candidate")]
    level = "measured_match" if exact else "near_reference" if near else "theory_only" if compatible else "insufficient"
    candidates = exact + near
    selected = exact[0] if exact else near[0] if near else None
    follow_up = (["补齐用户规格: " + ", ".join(missing)] if missing else []) + config_issues
    if not compatible:
        follow_up.append("补齐适用于当前需求的理论参数、模型专属缓存预算和部署有效能力，完成第一步及综合交叉校核")
    if not selected:
        follow_up.append("核对最接近记录的统计口径；缺少匹配测试时补做同配置长度/并发扫描")
    follow_up.extend(["验证多部署组流量分配、持续负载及相同分位数的TTFT/TPOT", "按实际部署位置核验备用组与故障域；未提供BOM不推算服务器数"])
    # Stage 3: compare evidence, not the arithmetic mean or maximum of card counts.
    theory_candidates = [dict(t["candidate"], source=t["source"]) for t in compatible]
    integration = {
        "status": "blocked" if config_issues or missing else "review_required" if selected and compatible else "baseline_only" if selected else "theory_only" if compatible else "insufficient",
        "theoryCandidates": theory_candidates,
        "baselineCards": selected["result"]["totalCards"] if selected else None,
        "provisionalCards": selected["result"]["totalCards"] if selected else None,
        "finalCards": None,
        "comparison": [{"theoryCards": t["totalCards"], "baselineCards": selected["result"]["totalCards"],
                        "theoryMinusBaseline": t["totalCards"] - selected["result"]["totalCards"],
                        "status": "counts_agree_pending_assumptions" if t["totalCards"] == selected["result"]["totalCards"] else "difference_requires_explanation"}
                       for t in theory_candidates] if selected else [],
        "rule": "理论先检查资源预算，基线再核算达标容量；同配置、同负载、同备用口径后解释差异，不取平均、不机械取最大值。存在两种依据时仍须核对权重布局、P/D分配与有效能力，不能自动视为交叉验证通过。",
        "conclusion": "配置或需求冲突，暂停综合建议" if config_issues or missing else "已有两类候选，须完成部署与差异核对后确定综合建议" if selected and compatible else "基线给出候选卡数；理论卡数未完成，综合校核待补充" if selected else "只有理论待验证方案，缺少达标基线" if compatible else "两类证据均不足，暂不确定卡数"
    }
    return {"toolVersion": VERSION, "createdAt": now(), "evidenceLevel": level, "demand": d,
            "workflow": {"order": ["theory", "baseline", "integration"],
                         "theory": {"status": "candidate" if compatible else "incomplete", "candidates": theory_candidates},
                         "baseline": {"selectedKey": selected["key"] if selected else None},
                         "integration": integration},
            "missingRequirements": missing, "selected": selected, "candidates": candidates,
            "calculationBasis": {
                "selectionRule": "精确匹配优先；其次为显式启用的保守近似；同等级默认选择总卡数最少的候选，不代表成本最优",
                "selectedKey": selected["key"] if selected else None,
                "allowNear": allow_near,
                "measuredEvidence": [{"key": e["key"], "source": e["source"], "rawHash": e["rawHash"],
                                      "testPoint": e["baseline"], "verifiedMetadata": e["metadata"],
                                      "state": e["state"], "differences": e["reasons"] + e["notes"]}
                                     for e in evaluations],
                "scope": "复制完整部署组，保留原并行策略；不按单卡Token吞吐任意外推；未填请求速率只覆盖并发预算",
                "noCandidateReason": None if selected else "不存在可直接采用的实测候选；查看缺项、差异及理论参考，不将参考卡数当实测结论"
            },
            "evaluations": evaluations, "theoryEvidence": theories, "modelConfigEvidence": configs,
            "modelConfigIssues": config_issues, "nextSteps": follow_up,
            "warnings": ["理论结果不覆盖实测结果；近似结果不等于达标证明", "卡数最少不代表成本或性能最优", "调优状态与原测试来源保留，复制预算不替代生产验收"]}


def cell(x):
    return clean(x).replace("|", "\\|").replace("\n", "；").replace("<", "&lt;").replace(">", "&gt;")


def markdown(r):
    lines = ["# LLM推理容量评估", "", "测算流程：理论测算 → 基线测算 → 综合判断。", "",
             "综合状态：" + r.get("workflow", {}).get("integration", {}).get("conclusion", "未记录") + "。", "", f"证据等级：**{r['evidenceLevel']}**；工具版本：{VERSION}。", "",
             "本报告为候选配置预算，不是性能或采购验收结论。", "", "## 用户要求", ""]
    lines.extend(f"- {k}：{cell(v)}" for k, v in r["demand"].items() if v is not None and clean(v))
    lines += ["", "## 测算依据", "", r["calculationBasis"]["selectionRule"] + "。", "",
              "### 引用的实测数据与适用性", ""]
    if not r["evaluations"]:
        lines.append("尚无可评估的实测记录；需求缺项或没有导入基线时不构造引用依据。")
    for e in r["evaluations"]:
        b, m, source, d = e["baseline"], e["metadata"], e.get("source") or {}, r["demand"]
        lines += [f"#### {cell(e['key'])}：{e['state']}", "",
                  f"- 原始文件：{cell(source.get('path', '未提供'))}",
                  f"- 文件SHA-256：{cell(source.get('sha256', '未提供'))}；记录SHA-256：{e['rawHash']}",
                  f"- 测试更新：{cell(b['updated']) or '未提供'}；状态：{cell(b['status'])}",
                  f"- 测试配置：{cell(b['model'])}；{cell(b['chip'])}；{cell(b['quant'])}；{cell(b['framework'])}；{cell(b['cpu'])}",
                  f"- 部署单位：{b['cards']}卡完整组；{cell(b['form'])}；并行策略：{cell(b['parallel']) or '未提供'}",
                  f"- 测试点：长度{cell(b['io'])}，并发{b['concurrency']}，Prefix Cache命中率{b['prefix']}%；K换算{cell(m['kBase'])}",
                  f"- 长度/负载口径：{cell(m['lengthStat'])}；推理Token {cell(m['reasoning'])}；负载 {cell(m['load'])}",
                  "", "|指标|基线实测值及口径|用户要求|", "|---|---|---|",
                  f"|TTFT|{b['ttft']} ms / {m['ttftStat']}|≤{d['ttft']} ms / {d['ttftStat']}|",
                  f"|TPOT|{b['tpot']} ms/Token / {m['tpotStat']}|≤{d['tpot']} ms/Token / {d['tpotStat']}|",
                  "", f"- 同点实测请求吞吐：{cell(m['qps']) or '未提供'} 次/秒（不使用单卡Token吞吐代替）",
                  f"- 人工核对依据：{cell(m['source']) or '未提供'}；完成核对：{'是' if m['verified'] else '否'}",
                  "- 采用/未采用原因：" + ("；".join(cell(x) for x in e["reasons"] + e["notes"]) or "配置、口径与延迟目标匹配"), ""]
    lines += ["### 本次采用的范围", "", r["calculationBasis"]["scope"] + "。", ""]
    if not r["selected"]:
        lines.append(r["calculationBasis"]["noCandidateReason"] + "。")
    lines += ["", "## 实测候选与差异", "", "|基线|状态|工作卡|备用卡|总卡|原部署配置|差异/依据|", "|---|---|---:|---:|---:|---|---|"]
    for e in r["evaluations"]:
        b, result = e["baseline"], e["result"]
        config = f"{b['model']} / {b['chip']} / {b['quant']} / {b['framework']} / {b['cards']}卡 {b['form']} / {b['parallel']} / {b['status']}"
        explanation = "; ".join(e["reasons"] + e["notes"]) or "口径依据: " + e["metadata"]["source"]
        lines.append("|" + "|".join(cell(v) for v in [e["key"], e["state"], result["workCards"] if result else "—", result["spareCards"] if result else "—", result["totalCards"] if result else "—", config, explanation]) + "|")
    if r["selected"]:
        e, d = r["selected"], r["demand"]
        b, result = e["baseline"], e["result"]
        lines += ["", "## 所选候选的计算", "", f"引用基线：{cell(e['key'])}；状态：{e['state']}。",
                  f"- 规划并发 = ceil({d['concurrency']} × (1 + {d['growth']}%)) = {d['plannedConcurrency']}",
                  f"- 并发组数 = ceil({d['plannedConcurrency']} / {b['concurrency']}) = {result['concurrencyGroups']}",
                  f"- 速率组数 = {result['rateGroups']}（未填写请求速率时记0，不构成持续吞吐保证）",
                  f"- 工作组数 = max({result['concurrencyGroups']}, {result['rateGroups']}) = {result['workGroups']}",
                  f"- 总卡数 = ({result['workGroups']} + {result['spareGroups']}) × {b['cards']} = {result['totalCards']}",
                  f"- 口径依据：{cell(e['metadata']['source'])}", f"- 记录摘要：{e['rawHash']}"]
        if d["plannedRate"] is not None:
            lines += [f"- 规划请求速率 = {d['rate']} × (1 + {d['growth']}%) = {d['plannedRate']} 次/秒",
                      f"- 速率组数 = ceil({d['plannedRate']} / {e['metadata']['qps']}) = {result['rateGroups']}"]
    lines += ["", "## 模型配置依据", ""]
    if not r["modelConfigEvidence"]:
        lines.append("未提供模型配置；不补造层数、上下文限制或KV精度，不影响既有基线核算。")
    for item in r["modelConfigEvidence"]:
        lines += [f"### {cell(item['modelName']) or '未绑定模型'}：{item['state']}", "",
                  "- 文件：" + cell(item["source"]["path"]),
                  "- 文件SHA-256：" + cell(item["source"]["sha256"]),
                  "- 配置内容SHA-256：" + item["configHash"],
                  "- 权重修订：" + (cell(item["revision"]) or "未提供，不能认定与基线修订一致"),
                  "", "|采用字段|原始值|", "|---|---|"]
        for key, value in item["fields"].items():
            lines.append("|" + key + "|" + cell(json.dumps(value, ensure_ascii=False)) + "|")
        check = item["checks"].get("context")
        if check:
            lines.append(f"\n上下文检查：输入＋输出={check['requested']} Token；配置声明上限={check['declaredLimit']} Token；未超出={'是' if check['withinDeclaredLimit'] else '否'}。")
        kv = item["derived"].get("standardKv")
        if kv:
            lines += ["", "- 标准KV理论公式：" + kv["formula"],
                      f"- 数值代入：{kv['substitution']} = {kv['bytesPerToken']} Byte/Token",
                      f"- 每请求理论K/V张量：{kv['bytesPerRequest']} Byte = {kv['bytesPerRequest']/2**30:.6f} GiB",
                      "- 适用边界：" + kv["scope"]]
        lines.extend("- " + cell(note) for note in item["notes"])
    lines += ["", "## 理论辅助依据", ""]
    if not r["theoryEvidence"]:
        lines.append("未提供；不影响有基线情况下的核算。")
    for t in r["theoryEvidence"]:
        lines.append(f"- 来源：{cell(t['source']['path'])}；状态：{t['state']}；摘要：{t['source']['sha256']}")
        raw = t["original"]
        if isinstance(raw, dict):
            lines.append("  - 原公式版本：" + cell(raw.get("calculationVersion", "未知")))
            inputs = raw.get("inputs", {})
            if isinstance(inputs, dict):
                for title, keys in [
                    ("模型与部署假设", ["model", "quant", "kv", "server", "group", "slots"]),
                    ("权重与缓存容量假设", ["total", "bytes", "weightExtra", "cache", "cacheLength", "cachePrecision", "memory", "usable", "runtime"]),
                    ("性能假设", ["active", "peak", "prefillEfficiency", "decodeEfficiency", "timeBudget"]),
                    ("原负载及目标", ["concurrency", "parallel", "growth", "input", "output", "ttft", "tpot", "spare"])
                ]:
                    lines.append("  - " + title + "：" + "；".join(k + "=" + cell(inputs.get(k, "未提供")) for k in keys))
            lines.append("  - 原单位声明：" + cell(json.dumps(raw.get("units", {}), ensure_ascii=False)))
        if "recomputed" in t:
            lines.append(f"  - 原假设重算：{t['recomputed']['cards']}卡；不自动当作当前需求结果。")
        if t.get("candidate"):
            lines.append(f"  - 同假设候选：{t['candidate']['totalCards']}卡，仅供待验证预算。")
        lines.extend("  - " + cell(note) for note in t["notes"])
    lines += ["", "## 综合建议与下一步", ""]
    lines.extend("- " + cell(x) for x in r["nextSteps"] + r["warnings"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="导入基线及模型配置")
    p.add_argument("--baselines", nargs="*")
    p.add_argument("--theory", nargs="*", help=argparse.SUPPRESS)
    p.add_argument("--model-config", nargs="*", help="模型config.json或包装配置；目录只查找config.json")
    p.add_argument("--config-model", default="", help="单配置显式绑定的完整模型名")
    p.add_argument("--config-revision", default="", help="记录权重修订信息，不自动认定为基线修订")
    p.add_argument("--annotations")
    p.add_argument("--out", required=True)
    p = sub.add_parser("request-template", help="生成待填写的需求模板")
    p.add_argument("--out", required=True)
    p = sub.add_parser("theory-calculate", help="由智能体传入已核对的数值计算理论预算，无需用户提供理论JSON")
    for key in ("total", "active", "parallel", "bytes", "cache", "cacheLength", "memory", "usable",
                "peak", "prefillEfficiency", "decodeEfficiency", "timeBudget", "group", "slots",
                "concurrency", "input", "output", "ttft", "tpot", "growth", "weightExtra", "runtime", "spare"):
        p.add_argument("--" + key, required=True, type=float)
    for key in ("model", "server", "quant", "kv", "cachePrecision"):
        p.add_argument("--" + key, required=True)
    for key in ("chip", "framework", "form", "cpu", "parallel"):
        p.add_argument("--config-" + key, default="")
    p.add_argument("--basis", action="append", required=True, help="各项来源或预算假设；可重复，不代表已核验")
    p.add_argument("--out", required=True, help="工具自动生成的中间结果，不是用户输入文件")
    p = sub.add_parser("assess", help="核算并输出内部JSON/Markdown及客户Markdown说明")
    p.add_argument("--library", required=True)
    p.add_argument("--request", required=True)
    p.add_argument("--allow-near", action="store_true")
    p.add_argument("--html", action="store_true", help="仅明确需要时额外导出旧版HTML；默认交付Markdown")
    p.add_argument("--out", required=True, help="报告路径前缀")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            summary = prepare(args)
        elif args.command == "request-template":
            write_json(args.out, request_template())
            summary = {"template": str(Path(args.out).resolve())}
        elif args.command == "theory-calculate":
            if args.config_form not in {"混合部署", "PD混合", "shared"}:
                raise ValueError("当前完整理论计算仅支持明确的输入/生成共享资源布局；PD分离须先实现两侧预算，不能套用")
            inputs = {k: v for k, v in vars(args).items()
                      if k not in {"command", "out", "basis"} and not k.startswith("config_")}
            inputs["purpose"] = "推理"
            result = theory_compute(inputs)
            output = {"calculationVersion": "1.1.0", "generatedBy": "sizing.py theory-calculate",
                      "units": {"parameters": "B (10^9)", "cacheBudget": "KiB/Token", "memory": "GiB", "latency": "ms", "compute": "TFLOPS"},
                      "configuration": {k: getattr(args, "config_" + k) for k in ("chip", "framework", "form", "cpu", "parallel")},
                      "inputs": inputs, "results": result, "basis": args.basis,
                      "scope": "共享资源预算，非延迟分位数预测；不证明P95达标，不覆盖PD分离"}
            if not all(x.strip() for x in args.basis):
                raise ValueError("理论来源与假设说明不能为空")
            write_json(args.out, output)
            summary = {"theoryOutput": str(Path(args.out).resolve()), "results": result, "scope": output["scope"]}
        else:
            report = assess(read_json(args.library), read_json(args.request), args.allow_near)
            prefix = Path(args.out)
            j, m = Path(str(prefix) + ".json"), Path(str(prefix) + ".md")
            write_json(j, report)
            m.write_text(markdown(report), encoding="utf-8")
            from client_report import client_markdown, client_evidence_markdown, client_html
            cm, ch = Path(str(prefix) + ".client.md"), Path(str(prefix) + ".client.html")
            em = Path(str(prefix) + ".evidence.md")
            em.write_text(client_evidence_markdown(report), encoding="utf-8")
            cm.write_text(client_markdown(report, em.name), encoding="utf-8")
            if args.html:
                ch.write_text(client_html(report), encoding="utf-8")
            summary = {"evidenceLevel": report["evidenceLevel"], "json": str(j.resolve()), "markdown": str(m.resolve()),
                       "clientMarkdown": str(cm.resolve()), "clientEvidence": str(em.resolve()), "missing": report["missingRequirements"]}
            if args.html:
                summary["clientHtml"] = str(ch.resolve())
        print(json.dumps(summary, ensure_ascii=True, allow_nan=False))
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
