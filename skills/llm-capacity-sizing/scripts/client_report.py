"""Customer-facing, progressive disclosure reports from the same calculation result."""
from datetime import datetime, timedelta, timezone
from html import escape
import ntpath
import re

LEVELS = {"measured_match": "匹配基线候选", "near_reference": "保守近似候选",
          "theory_only": "仅有理论假设，待测试验证", "insufficient": "依据不足，暂不确定卡数"}
STATES = LEVELS | {"reference": "仅供参考", "pending": "口径待确认", "failed": "延迟不达标",
                  "config_conflict": "配置冲突", "associated": "已关联，修订仍需核对",
                  "context_conflict": "上下文声明冲突", "compatible_assumptions": "与原假设一致",
                  "unusable": "无法采用", "inconsistent": "原结果与重算不一致"}
LABELS = {"cardCountScope": "部署卡数计数范围", "prefillCards": "输入侧卡数", "decodeCards": "生成侧卡数", "modelConfigHash": "模型配置摘要", "plannedConcurrency": "规划模型并发", "plannedRate": "规划请求速率",
          "ttftStat": "首Token延迟统计方式", "tpotStat": "每Token耗时统计方式", "lengthStat": "长度统计方式",
          "reasoning": "推理Token统计范围", "framework": "推理框架", "concurrency": "模型请求并发",
          "theoryServer": "理论配置服务器", "modality": "模态", "parallel": "并行策略", "model": "模型版本",
          "chip": "芯片完整型号", "quant": "量化格式", "form": "部署形态", "cpu": "CPU架构",
          "input": "输入长度", "output": "输出长度", "load": "负载方式", "prefix": "缓存命中率",
          "ttft": "首Token延迟", "tpot": "每Token耗时", "rate": "请求速率", "growth": "增长预留",
          "spare": "备用组数", "kBase": "K换算口径"}
VALUES = {"total": "输入与生成两侧总计", "per_stage": "单侧卡数", "unknown": "未知", "p95": "P95", "p99": "P99", "mean": "平均值", "max": "上限/最大值",
          "fixed": "固定长度", "closed": "固定并发闭环压测", "burst": "同批请求突发",
          "arrival": "开放请求到达", "included": "计入全部生成Token", "excluded": "不含推理Token"}
FLOW = """flowchart LR
  A[统一用户需求与单位] --> B[第一步 理论测算]
  B --> C[第二步 基线测算]
  C --> D[第三步 综合判断]
  B -.资源预算与缺项.-> D
  D --> E[候选卡数及待验证项]
  D --> F[冲突先核对 不取平均或机械取大]
"""
RULE = '''flowchart LR
  A[用户模型并发] --> B[加入增长预留]
  B --> C[除以基线达标并发并向上取整]
  R[可选请求速率与实测请求吞吐] --> M[取两种需求所需组数的较大值]
  C --> M
  M --> W[乘以每组卡数得到工作卡]
  S[备用组数乘以每组卡数] --> T[工作卡加备用卡]
  W --> T'''


def fmt(value, decimals=4):
    if value is None or value == "":
        return "未提供"
    if isinstance(value, (int, float)):
        return f"{value:,.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{value:,.0f}"
    return str(value)


def localize(value):
    s = str(value)
    for key in sorted(LABELS, key=len, reverse=True):
        s = s.replace(key, LABELS[key])
    return s


def state(value):
    return STATES.get(value, value)


def val(value):
    return VALUES.get(str(value), fmt(value))


def basename(value):
    return ntpath.basename(str(value)) if value else "未提供"


def display_date(value):
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M（北京时间）")
    except (ValueError, TypeError):
        return str(value or "未提供")


def simulated(r):
    if r.get("demonstration"):
        return True
    return any(str(e.get("key", "")).lower().startswith("id:demo") or
               str(e.get("baseline", {}).get("model", "")).upper().startswith("DEMO") or
               "合成" in str(e.get("baseline", {}).get("status", "")) for e in r.get("evaluations", []))


def document(r):
    """One structured document feeds both HTML and Markdown; never recalculate card counts."""
    d, selected = r["demand"], r.get("selected")
    project = str(d.get("project") or "LLM推理服务")
    sections = []
    def section(title, blocks, deep=False):
        sections.append({"title": title, "blocks": blocks, "deep": deep})
    def p(s): return ("p", s)
    def table(headers, rows): return ("table", headers, rows)
    def listing(items): return ("list", items)
    def diagram(kind): return ("diagram", kind)
    summary = [p("本说明按“理论测算 → 基线测算 → 综合判断”展开。两条计算路径独立给出依据，最后核对配置与差异；理论输入不能由基线卡数反推填充。")]
    if selected:
        q, b = selected["result"], selected["baseline"]
        summary += [table(["结果项", "本次候选"], [["工作卡数", f"{q['workCards']} 张"],
                    ["备用卡数", f"{q['spareCards']} 张"], ["合计", f"{q['totalCards']} 张"],
                    ["部署方式", f"{q['workGroups']}个工作组＋{q['spareGroups']}个备用组，每组{b['cards']}卡"],
                    ["依据等级", state(selected["state"])], ["引用基线", selected["key"]],
                    ["原基线状态", b["status"]]]),
                    p("上述数量按基线的设备计数口径给出。每组保持原并行策略和P/D配比；多组流量分配及实际延迟仍需验证。未提供整机配置时不折算服务器台数。")]
        if selected["state"] == "near_reference":
            summary.append(p("本次存在长度差异，仅沿用原测试并发能力作为保守参考；没有因请求变短而提高每组容量。"))
    else:
        summary.append(p("当前不能给出有充分实测依据的候选卡数。下文列出已具备的依据、阻塞条件和下一步，不将缺少数据解释为零卡。"))
        compatible = [t for t in r.get("theoryEvidence", []) if t.get("candidate")]
        if compatible:
            summary += [p("以下仅为同一原理论假设下的待验证方案，不是实测达标结论；多个理论方案不自动合并。"),
                        table(["理论来源", "待验证总卡数"], [[basename(t["source"].get("path")), str(t["candidate"]["totalCards"])] for t in compatible])]
        reasons = list(r.get("missingRequirements", [])) + list(r.get("modelConfigIssues", []))
        reasons += [reason for e in r.get("evaluations", []) for reason in e.get("reasons", [])]
        summary.append(listing([localize(x) for x in dict.fromkeys(reasons)] or ["缺少可匹配并核对的实测测试点。 "]))
    section("第一层 · 先看测算结论", summary)
    section("第二层 · 理解计算模型", [diagram("flow"),
            p("这里的“完整部署组”是一整套已测试的模型服务配置，不是任意一张卡。例如一个测试组用了16卡，核算时就按16卡整组复制，不能默认8卡有一半能力。"),
            p("P/D分离是把输入处理（Prefill）和逐Token生成（Decode）安排到不同资源上。复制一个组时，需保留原测试的资源配比，不能只增加其中一侧就套用原结果。"),
            listing(["先确认模型、硬件、量化、框架和业务负载是否能复用测试结果。",
                     "再检查首Token延迟（TTFT）和后续每Token耗时（TPOT）是否满足用户目标，统计方式必须一致。",
                     "最后核算完整组数。达标并发描述一个组在该测试条件下的容量，不是单卡理论算力。",
                     "没有匹配依据时先补测；不能简单增加独立部署组，就认定单请求延迟可以改善。"]), diagram("rule")])
    req_rows = []
    units = {"input": " Token", "output": " Token", "concurrency": " 路", "ttft": " 毫秒", "tpot": " 毫秒/Token", "growth": "%", "prefix": "%", "spare": " 组", "rate": " 次/秒"}
    for key in ["model", "chip", "quant", "framework", "form", "cpu", "parallel", "input", "output", "lengthStat", "reasoning", "concurrency", "growth", "ttft", "ttftStat", "tpot", "tpotStat", "load", "prefix", "rate", "spare"]:
        v = d.get(key)
        empty = v is None or v == "" or v == "unknown"
        text = "未限制，沿用所选基线配置" if empty and key in {"chip", "quant", "framework", "form", "cpu", "parallel"} else "未提供" if empty else val(v) + units.get(key, "")
        if key == "rate" and empty:
            text = "未提供；本次不覆盖持续请求流量"
        req_rows.append([LABELS[key], text])
    paired = [req_rows[i] + (req_rows[i+1] if i+1 < len(req_rows) else ["", ""]) for i in range(0, len(req_rows), 2)]
    section("第三层 · 本次需求与计算前提", [table(["条件", "用户要求", "条件", "用户要求"], paired),
            p("并发必须按同时执行的模型请求统计。一个业务串行调用模型多次，不表示并发按调用次数直接相乘。P95表示95%的请求指标值不超过该值，不能用平均值直接代替。")])
    basis = []
    if selected:
        e, b, m = selected, selected["baseline"], selected["metadata"]
        basis += [table(["指标", "基线测试点", "用户目标", "判断"], [
            ["首Token延迟", f"{fmt(b['ttft'])}毫秒 / {val(m['ttftStat'])}", f"≤{fmt(d['ttft'])}毫秒 / {val(d['ttftStat'])}", "所选口径与目标满足筛选规则"],
            ["每Token耗时", f"{fmt(b['tpot'])}毫秒 / {val(m['tpotStat'])}", f"≤{fmt(d['tpot'])}毫秒 / {val(d['tpotStat'])}", "所选口径与目标满足筛选规则"],
            ["输入/输出长度", b["io"], f"{fmt(d['input'])}/{fmt(d['output'])} Token", "一致" if e["state"] == "measured_match" else "存在差异，按保守近似处理"],
            ["每组达标并发", f"{b['concurrency']}路 / {b['cards']}卡", "按规划负载计算组数", "不提高原测试容量"]]),
            p(f"采用配置：{b['model']}；{b['chip']}；{b['quant']}；{b['framework']}；{b['form']}；CPU架构{b['cpu']}。"),
            p("口径核对依据：" + (m.get("source") or "未提供")),
            p("保留并行策略：" + (b.get("parallel") or "未提供")),
            p("基线更新时间：" + (b.get("updated") or "未提供") + "；状态：" + b["status"]),
            p("优先采用精确匹配，其次采用明确启用的保守近似；同等级默认展示卡数最少的候选，未比较价格或总拥有成本。")]
    if r.get("evaluations"):
        basis.append(table(["记录", "筛选结果", "采用或排除原因"], [[e["key"], state(e["state"]),
                     "；".join(localize(x) for x in e.get("reasons", []) + e.get("notes", [])) or
                     ("本次采用" if selected and e["key"] == selected["key"] else "条件满足，保留备选")]
                     for e in r["evaluations"]]))
    else:
        basis.append(p("尚无可评估的实测记录；不构造虚假的测试点作为依据。"))
    section("第四层 · 为什么采用这条基线", basis, True)
    formulas = []
    if selected:
        b, q, m = selected["baseline"], selected["result"], selected["metadata"]
        rows = [["规划并发", "向上取整［用户模型并发×（1＋增长比例）］",
                 f"向上取整［{fmt(d['concurrency'])}×（1＋{fmt(d['growth'])}%）］＝{d['plannedConcurrency']}路"],
                ["并发所需组数", "向上取整［规划并发÷基线达标并发］",
                 f"向上取整［{fmt(d['plannedConcurrency'])}÷{fmt(b['concurrency'])}］＝{q['concurrencyGroups']}组"]]
        if d.get("plannedRate") is not None:
            rows += [["规划请求速率", "用户请求速率×（1＋增长比例）", f"{fmt(d['rate'])}×（1＋{fmt(d['growth'])}%）＝{fmt(d['plannedRate'])}次/秒"],
                     ["速率所需组数", "向上取整［规划速率÷同测试点实测请求吞吐］", f"向上取整［{fmt(d['plannedRate'])}÷{m['qps']}］＝{q['rateGroups']}组"]]
        rows += [["工作组数", "取并发和速率所需组数的较大值", f"最大值［{q['concurrencyGroups']}；{q['rateGroups']}］＝{q['workGroups']}组"],
                 ["工作卡数", "工作组数×每组卡数", f"{q['workGroups']}×{b['cards']}＝{q['workCards']}张"],
                 ["备用卡数", "备用组数×每组卡数", f"{q['spareGroups']}×{b['cards']}＝{q['spareCards']}张"],
                 ["候选总卡数", "工作卡数＋备用卡数", f"{q['workCards']}＋{q['spareCards']}＝{q['totalCards']}张"]]
        formulas += [table(["步骤", "计算规则", "本次数值代入"], rows),
                     p("组数必须向上取整，避免缺少承接剩余请求的完整配置。备用组不计入正常工作能力。"),
                     diagram("allocation")]
        if d.get("plannedRate") is None:
            formulas.append(p("未提供请求速率，速率所需组数在取最大值时记0，表示该约束未参与计算，不表示已测得速率为0或持续吞吐达标。"))
    else:
        formulas.append(p("当前没有可采用的实测候选，因此不填造代入值。计算规则仍为：工作组数取并发与可选速率约束的较大值，总卡数等于工作与备用完整组数之和乘以基线每组卡数。理论方案与本规则分开，不视为实测容量。"))
    section("第五层 · 卡数如何逐步算出", formulas, True)
    auxiliary = []
    configs = r.get("modelConfigEvidence", [])
    if not configs:
        auxiliary.append(p("未提供模型配置，本次不补造层数、上下文限制或缓存结构。"))
    for c in configs:
        auxiliary.append(p(f"模型配置：{c['modelName'] or '未绑定模型'}；{state(c['state'])}；修订：{c.get('revision') or '未提供'}。"))
        check = c.get("checks", {}).get("context")
        if check:
            auxiliary.append(p(f"输入加输出为{fmt(check['requested'])} Token，配置声明上限为{fmt(check['declaredLimit'])} Token；{'未超过声明，但仍需核对部署支持' if check['withinDeclaredLimit'] else '超过声明，当前应暂停采用候选并核对扩展依据'}。"))
        kv = c.get("derived", {}).get("standardKv")
        if kv:
            auxiliary.append(table(["辅助项", "公式及代入", "结果"], [["标准K/V张量", kv['formula'] + '；' + kv['substitution'], f"{fmt(kv['bytesPerToken'])} Byte/Token，{fmt(kv['bytesPerRequest']/2**30,6)} GiB/请求"]]))
        auxiliary.append(listing([localize(x) for x in c.get("notes", [])]))
    theories = r.get("theoryEvidence", [])
    if not theories:
        auxiliary.append(p("未提供既有理论测算；可计算基线候选，但综合结论必须注明理论校核未完成。"))
    for t in theories:
        auxiliary.append(p(f"理论文件：{basename(t['source'].get('path'))}；用途判断：{state(t['state'])}。"))
        if "recomputed" in t:
            auxiliary.append(p(f"原理论假设重算为{t['recomputed']['cards']}卡。这是原配置下的结果，不自动作为当前需求结论。"))
        v = t.get("original", {}).get("inputs", {}) if isinstance(t.get("original"), dict) else {}
        if isinstance(v, dict) and v:
            auxiliary.append(table(["关键理论假设", "原取值"], [["模型 / 部署量化", f"{v.get('model','未提供')} / {v.get('quant','未提供')}"],
                       ["每Token等效缓存预算", f"{fmt(v.get('cache'))} KiB/Token"],
                       ["标称运算率及有效比例", f"{fmt(v.get('peak'))} T运算/秒；输入{fmt(v.get('prefillEfficiency'))}%，生成{fmt(v.get('decodeEfficiency'))}%"],
                       ["TTFT输入时间比例", f"{fmt(v.get('timeBudget'))}%"]]))
        auxiliary.append(listing([localize(x) for x in t.get("notes", [])]))
    auxiliary.append(p("模型配置推导的张量占用不等于完整运行显存，理论卡数不与实测卡数取平均或机械取最大值。"))
    section("第六层 · 模型配置与理论结果起什么作用", auxiliary, True)
    section("后续验证 · 综合建议如何落地", [listing([
        "基线反映特定模型、软件、硬件和压测条件；实际业务仍需验证相同统计方式的延迟。",
        "复制完整组不等于无限线性扩展；需测试流量分配、持续到达和多组协同。",
        "备用组数量不自动证明容灾；须确认故障域、部署位置与切换后剩余能力。",
        "当前没有整机BOM、成本数据时，不给服务器台数或最优采购结论。"]),
        listing([localize(x) for x in r.get("nextSteps", [])])])
    sources = []
    for e in r.get("evaluations", []):
        src = e.get("source") or {}
        sources.append(["实测记录 " + e["key"], basename(src.get("path")), src.get("sha256", "未提供"), e.get("rawHash", "未提供")])
    for c in configs:
        sources.append(["模型配置 " + (c["modelName"] or "未绑定"), basename(c["source"].get("path")), c["source"].get("sha256", "未提供"), c["configHash"]])
    for t in theories:
        sources.append(["理论结果", basename(t["source"].get("path")), t["source"].get("sha256", "未提供"), "见原始文件"])
    section("附录 · 依据追溯与术语", [table(["依据", "文件名", "文件SHA-256", "内容摘要"], sources),
        p("文件摘要用于确认所引用的文件版本，不证明数据真实性。详细本地路径和原始JSON保留在内部技术报告，不在客户版正文展开。"),
        table(["术语", "说明"], [["TTFT", "从约定计时起点到首Token的延迟。"], ["TPOT", "首Token之后的每Token生成耗时，须与基线统计定义一致。"],
              ["完整部署组", "测试时共同工作的全部卡、并行方式与P/D配比。"], ["向上取整", "有余数时增加一整个组，不能使用小数组。"],
              ["证据等级", "匹配基线、保守近似、理论待验证或依据不足，表示不同的结论边界。"]])], True)
    theory_intro = [("h3", "1.1 先检查资源预算规则"), p("第一步先回答：模型装得下吗，按假设需要多少计算资源？理论预算用于检查资源约束，不能证明P95延迟达标。"),
        table(["约束", "计算规则", "需要的独立输入"], [
            ["模型权重", "总参数量×每参数存储量×（1＋权重额外比例）", "完整权重参数量、实际存储格式、量化元数据开销；结果GiB"],
            ["每请求缓存", "每词元缓存量×（输入长度＋输出长度）×缓存精度比例", "预算单位KiB/Token，适用该模型缓存结构，明确参考精度；结果GiB"],
            ["每组显存", "每组卡数×（单卡显存×可用比例－单卡运行预留）", "卡显存、运行预留、权重布局、缓存分配；需验证每卡不溢出"],
            ["输入计算需求", "规划并发×输入长度×每词元计算量÷（TTFT×输入计算时间比例）", "每词元计算量≈２×每词元激活参数量；单位统一后计算"],
            ["生成计算需求", "规划并发×每词元计算量÷TPOT", "每卡有效生成能力；该式仅为简化计算预算"],
            ["理论卡数", "同时满足显存与计算约束，再按理论部署组取整并加入备用", "明确共享/分离部署、通信和内存带宽瓶颈；不能直接除标称峰值"]]),
        p("本工具仅自动重算支持的理论JSON。表中规则是预算模型；有效算力、特殊缓存结构和部署布局缺失时，不输出假精确卡数。闭环并发基线与突发理论模型不能自动视为同一负载。")]
    if not theories:
        theory_intro += [("h3", "1.2 本次能算什么、还缺什么"), p("本次理论卡数：暂不能确定。尚未导入适用于当前模型及需求的完整理论测算输入。"),
            table(["待补输入", "为什么不能从现有配置直接得到"], [
                ["总参数量、每Token激活参数量及权重字节", "配置尺寸不等于已校验的参数统计；MoE和混合精度需要专门计数与权重依据"],
                ["模型专属每Token缓存预算及运行显存", "压缩、滑窗等结构不能套普通全注意力KV公式；需架构说明或显存测量"],
                ["每卡有效输入/生成能力、时间预算与部署布局", "标称峰值不等于实际有效能力；P/D分离不能直接套共享副本模型"]])]
    for t in theories:
        if t.get("recomputed"):
            v, q = t.get("original", {}).get("inputs", {}), t["recomputed"]
            theory_intro.append(table(["理论项目", "原输入数值代入 / 重算结果"], [
                ["权重GiB", f"{fmt(v.get('total'))}×10⁹×{fmt(v.get('bytes'))}×（1＋{fmt(v.get('weightExtra'))}%）÷2³⁰＝{fmt(q['weight'])}"],
                ["每请求缓存GiB", f"{fmt(v.get('cache'))}×（{fmt(v.get('input'))}＋{fmt(v.get('output'))}）÷1024²×参考精度字节比＝{fmt(q['cache'])}"],
                ["输入 / 生成计算需求TFLOPS", f"{fmt(q['fp'])} / {fmt(q['fd'])}"],
                ["原假设总卡数", f"{q['cards']}张；是否可用于当前需求：{state(t['state'])}"]]))
    integrated = r.get("workflow", {}).get("integration", {})
    tc = [t["candidate"]["totalCards"] for t in theories if t.get("candidate")]
    compare = [p(integrated.get("conclusion", "请分别核对理论和基线依据。")),
        table(["维度", "本次结果", "在综合结论中的作用"], [
            ["理论测算", "、".join(str(n)+"张" for n in tc) if tc else "未形成适用于本需求的理论卡数", "资源预算校核；不替代延迟测试"],
            ["基线测算", str(selected['result']['totalCards'])+"张（候选）" if selected else "无可用达标候选", "相同条件下完整组复制的容量预算"],
            ["综合判断", "暂采用基线候选，理论校核待完成" if selected and not tc else "有差异待核对，暂不自动确定最终卡数", "核对同模型、硬件、负载、量化、工作/备用口径后再定案"]]),
        p("综合规则：①先统一比较口径；②比较工作卡与备用卡，而非只看总数；③理论偏大，检查效率假设与实测优化；理论偏小，检查带宽、通信、缓存和调度开销；④显存硬约束冲突先核查权重分布、卸载和实际精度；⑤原因未查清前保留候选与补测项，不取平均，也不机械取最大值。")]
    for diff in integrated.get("comparison", []):
        compare.append(p(f"数值对比：理论{diff['theoryCards']}张－基线{diff['baselineCards']}张＝{diff['theoryMinusBaseline']}张。卡数相同也不能证明假设一致；先核对工作/备用、每组布局和负载口径。"))
    if selected:
        ties = [e for e in r.get("candidates", []) if e["result"]["totalCards"] == selected["result"]["totalCards"]]
        if len(ties) > 1:
            compare += [table(["同总卡数备选", "工作卡", "备用卡", "组大小"], [[e["key"], str(e["result"]["workCards"]), str(e["result"]["spareCards"]), str(e["baseline"]["cards"])] for e in ties]),
                        p("这些方案总卡数相同，工作能力与备用故障域不同。当前按输入顺序展示首个，不能视为唯一最优方案。")]
    # Main reading order is visible; only provenance is collapsed.
    sections = [
        {"title": "测算路线 · 先理论，再基线，最后综合", "blocks": [diagram("flow"), summary[0]], "deep": False},
        {"title": "共同输入 · 本次需求与口径", "blocks": sections[2]["blocks"], "deep": False},
        {"title": "第一步 · 理论测算：显存与计算预算", "blocks": theory_intro + [("h3", "1.3 模型配置与已导入理论证据")] + auxiliary, "deep": False},
        {"title": "第二步 · 基线测算：选择测试点并计算完整组", "blocks": [p("第二步独立使用测试数据，不使用第一步的理论卡数反推性能。先检查配置及延迟，达标后才复制完整组。"), diagram("rule"), ("h3", "2.1 先筛选满足条件的测试点")] + basis + [("h3", "2.2 再计算完整组与卡数")] + formulas, "deep": False},
        {"title": "第三步 · 综合判断：对比依据与候选方案", "blocks": [("h3", "3.1 并排比较两类依据")] + compare + [("h3", "3.2 当前候选及适用条件")] + summary[1:], "deep": False},
        sections[-2], sections[-1]]
    # Customer revision: one statement per fact, with raw technical evidence in the appendix.
    capacity = {
        "title": "第三层 · 显存与计算分别能承接多少并发",
        "formulas": [
            "显存可承接并发＝向下取整｛［每组卡数×（单卡显存×可用比例－运行预留）－权重显存］÷每请求缓存｝",
            "计算可承接并发＝向下取整［１÷（单请求输入需求÷单组输入有效算力＋单请求生成需求÷单组生成有效算力）］"
        ],
        "note": "权重、缓存和有效算力的取值依据见下方理论测算。任一承载并发小于１，当前组配置不可用。理论式适用于输入与生成共享资源；分离部署需分别核对两侧。"
    }
    work = {
        "title": "第二层 · 理论与基线各需要多少工作组",
        "formulas": [
            "理论工作组数＝向上取整｛向上取整［用户并发×（1＋增长比例）］÷最小值（显存可承接并发，计算可承接并发）｝",
            "基线工作组数＝向上取整｛向上取整［用户并发×（1＋增长比例）］÷基线达标并发｝" if d.get("plannedRate") is None else "基线工作组数＝最大值｛向上取整［向上取整（用户并发×（1＋增长比例））÷基线达标并发］，向上取整［用户请求速率×（1＋增长比例）÷基线请求吞吐］｝"
        ],
        "note": "基线须先匹配配置与负载，并满足TTFT、TPOT目标。统一两条路径的部署口径、解释差异后确定工作组数，不直接取平均或取最大值。",
        "child": capacity
    }
    overview = [diagram("model"), ("onion", {
        "title": "第一层 · 总共需要多少卡",
        "formulas": ["候选总卡数＝（工作组数＋备用组数）×每组卡数"],
        "child": work
    })]
    sections[0] = {"title": "整体计算模型与总公式", "blocks": overview, "deep": False}
    theory_blocks = [p("本次理论卡数：暂不能确定。缺少下列独立输入，暂只完成模型上下文检查。") if not tc else p("以下展示导入理论结果与本次需求的对应关系。"),
        table(["理论输入", "本次状态", "影响"], [
            ["模型配置与上下文", "已导入，见下方检查" if configs else "未提供", "仅检查配置声明，不能证明部署已支持"],
            ["总参数量、激活参数量、权重存储格式", "见导入理论依据" if theories else "待补充", "权重显存和每Token计算量暂无法确定"],
            ["模型专属缓存预算、运行显存", "见导入理论依据" if theories else "待补充", "每组可承接请求数暂无法确定"],
            ["有效计算能力及部署布局", "见导入理论依据" if theories else "待补充", "不能仅用标称峰值换算卡数"]])]
    for c in configs:
        check = c.get("checks", {}).get("context")
        if check:
            theory_blocks.append(p(f"上下文检查：{fmt(d['input'])}＋{fmt(d['output'])}＝{fmt(check['requested'])} Token，配置声明上限{fmt(check['declaredLimit'])} Token；" + ("未超过声明上限。" if check['withinDeclaredLimit'] else "超过声明上限，暂停采用候选。")))
    theory_blocks += [("h3", "计算规则与已有结果")]
    theory_blocks += [b for b in theory_intro if b[0] == "table" and b[1][0] != "待补输入"]
    if not theories:
        theory_blocks.append(p("缓存预算需匹配该模型的压缩、滑窗等结构；完整理论参数补齐后再进行数值代入。"))
    else:
        theory_blocks += [b for b in auxiliary if b[0] != "list"]
    sections[2]["blocks"] = theory_blocks
    # Keep detailed statements for audit without forcing customers through implementation notes.
    technical = [b for b in auxiliary if b[0] in {"p", "list"}]
    basis_compact = []
    if selected:
        b, q, m = selected["baseline"], selected["result"], selected["metadata"]
        basis_compact += [p(f"本次采用{selected['key']}：每组{b['cards']}卡，测试并发{b['concurrency']}路。复制时保留原并行策略及P/D配比。"), basis[0]]
    rows = []
    for ev in r.get("evaluations", []):
        bb, qq = ev["baseline"], ev.get("result")
        reason = "本次采用" if selected and ev["key"] == selected["key"] else "保留备选" if qq else "；".join(localize(x) for x in ev.get("reasons", [])) or state(ev["state"])
        rows.append([ev["key"], f"{bb.get('cards')}卡 / {bb.get('concurrency')}路", bb.get("io", "未提供"),
                     f"{fmt(bb.get('ttft'))} / {fmt(bb.get('tpot'))}", str(qq["totalCards"])+"卡" if qq else "不采用", reason])
    basis_compact.append(table(["基线", "每组规模 / 并发", "输入/输出", "TTFT / TPOT（ms / ms每Token）", "总卡数", "选择依据"], rows))
    # Avoid an artificial zero-rate branch when the user did not supply request rate.
    if d.get("plannedRate") is None:
        for block in formulas:
            if block[0] == "table":
                for row in block[2]:
                    if row[0] == "工作组数":
                        row[1:] = ["未提供请求速率，采用并发所需组数", f"工作组数＝{selected['result']['workGroups']}组"]
        formulas = [b for b in formulas if not (b[0] == "p" and b[1].startswith("未提供请求速率，速率"))]
    sections[3]["blocks"] = [("h3", "2.1 选择达标基线")] + basis_compact + [("h3", "2.2 代入计算")]+formulas
    integration_blocks = [p(integrated.get("conclusion", "尚无综合结论")), compare[1], diagram("decision")]
    if selected:
        ties = [ev for ev in r.get("candidates", []) if ev["result"]["totalCards"] == selected["result"]["totalCards"]]
        if len(ties) > 1:
            integration_blocks += [("h3", "同卡数方案如何选择"), table(["方案", "工作卡 / 备用卡", "工作组承载并发预算", "每组规模"], [
                [ev["key"], f"{ev['result']['workCards']} / {ev['result']['spareCards']}",
                 f"{ev['result']['workGroups']}×{ev['baseline']['concurrency']}＝{ev['result']['workGroups']*ev['baseline']['concurrency']}路", f"{ev['baseline']['cards']}卡"] for ev in ties]),
                p("两种方案均为模拟基线预算。备用组规模不同，故障域需另行确认；当前按输入顺序展示首个方案，未认定其成本或性能最优。")]

        # Retain a concise result table for numeric traceability.
        integration_blocks += [summary[1]]
    else:
        integration_blocks += summary[1:]
    if selected and selected["state"] == "near_reference":
        integration_blocks.append(p("存在差异，按保守近似处理；沿用原测试并发，不因请求更短提高容量。"))
    sections[4]["blocks"] = integration_blocks
    sections[5]["title"] = "待补事项与验证"
    sections[5]["blocks"] = [table(["事项", "完成条件"], [
        ["理论输入", "补齐模型专属参数、缓存预算和部署有效能力，重新执行理论测算"],
        ["部署一致性", "确认模型修订、量化转换、推理框架及原P/D并行策略"],
        ["业务负载", "验证多组流量分配及相同分位数的TTFT/TPOT；持续流量需另提供请求速率"],
        ["备用及整机", "确认故障域与切换能力；提供整机BOM后再折算服务器数"]])]
    # Preserve metadata and technical caveats in a single appendix.
    sections[-1]["blocks"] = [("h3", "技术依据与口径定义")] + technical + sections[-1]["blocks"]
    for block in sections[-1]["blocks"]:
        if block[0] == "table":
            for row in block[2]:
                if row and str(row[0]).startswith("实测记录 ") and any(str(row[0]).endswith(ev["key"]) and (str(ev["key"]).lower().startswith("id:demo") or "合成" in str(ev.get("baseline", {}).get("status", ""))) for ev in r.get("evaluations", [])):
                    row[0] = str(row[0]).replace("实测记录 ", "模拟基线记录 ", 1)
    return {"title": project + "｜算力容量测算说明", "version": r.get("toolVersion", "未知"),
            "date": r.get("createdAt", ""), "level": ("基线候选已算出，理论校核待完成" if integrated.get("status") == "baseline_only" else "两类结果待综合核对" if integrated.get("status") == "review_required" else state(r.get("evidenceLevel", "insufficient"))),
            "simulation": simulated(r), "selected": selected, "sections": sections}


def md_safe(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "；").replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`")


def readable_equation(eq):
    """Native MathML renders fractions offline; original text remains the accessible label."""
    esc = lambda value: escape(str(value), quote=True)
    text = lambda value: '<mtext>' + esc(value) + '</mtext>'
    frac = lambda numerator, denominator: '<mfrac>' + text(numerator) + text(denominator) + '</mfrac>'
    left, sep, right = eq.partition('＝')
    if not sep:
        left, sep, right = eq.partition('≈')
    if not sep:
        return '<div class="readable-equation">' + esc(eq) + '</div>'
    rounding = ''
    explanation = ''
    fractions = {
        '理论工作组数': ('向上取整［用户并发×（1＋增长比例）］', '最小值（显存可承接并发，计算可承接并发）', '向上取整'),
        '显存可承接并发': ('每组卡数×（单卡显存×可用比例－运行预留）－权重显存', '每请求缓存', '向下取整'),
        '单请求输入需求': ('输入长度×每词元计算量', 'TTFT×输入计算时间比例', ''),
        '单请求生成需求': ('每词元计算量', 'TPOT', '')
    }
    if left == '基线工作组数' and '最大值' not in right:
        fractions[left] = ('向上取整［用户并发×（1＋增长比例）］', '基线达标并发', '向上取整')
    if left in fractions:
        numerator, denominator, rounding = fractions[left]
        body = frac(numerator, denominator)
    elif left == '计算可承接并发':
        denominator = frac('单请求输入需求', '单组输入有效算力') + '<mo>＋</mo>' + frac('单请求生成需求', '单组生成有效算力')
        body = '<mfrac>' + text('１') + '<mrow>' + denominator + '</mrow></mfrac>'
        rounding = '向下取整'
    elif left == '单请求计算占比':
        body = frac('单请求输入需求', '单组输入有效算力') + '<mo>＋</mo>' + frac('单请求生成需求', '单组生成有效算力')
        explanation = '先把输入、生成各自需要的资源换成占比，再相加。'
    elif left == '理论单组并发':
        body = text('显存可承接并发') + '<mo>，</mo>' + text('计算可承接并发')
        rounding = '取两者较小值'
    elif left == '规划并发':
        body, rounding = text('用户并发×（1＋增长比例）'), '向上取整'
    else:
        body = text(right)
    if left in ('理论工作组数', '基线工作组数'):
        explanation = ''
    elif left == '显存可承接并发':
        explanation = '先扣除权重，再看剩余显存能放下多少份请求缓存。'
    elif left == '计算可承接并发':
        explanation = '一个请求占用多少计算能力，决定一组能同时承接多少请求。'
    return ('<div class="readable-equation" aria-label="' + esc(eq) + '"><div class="equation-output">' + esc(left) + '</div>'
            + '<div class="equation-expression"><span class="equation-equals">' + sep + '</span>'
            + '<div class="math-scroll"><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><mrow>' + body + '</mrow></math></div>'
            + ('<span class="rounding">' + esc(rounding) + '</span>' if rounding else '') + '</div>'
            + ('<div class="equation-explanation">' + esc(explanation) + '</div>' if explanation else '') + '</div>')


def onion_html(node, nested=False):
    esc = lambda value: escape(str(value), quote=True)
    out = ['<details class="formula-layer"><summary>展开：' + esc(node["title"]) + '</summary>'] if nested else ['<div class="formula-root"><h3>' + esc(node["title"]) + '</h3>']
    out += [readable_equation(eq) for eq in node.get("formulas", [])]
    if node.get("panels"):
        out.append('<div class="equation-grid">' + ''.join('<div class="equation-panel"><h4>' + esc(title) + '</h4>' + ''.join(readable_equation(eq) for eq in equations) + '</div>' for title, equations in node["panels"]) + '</div>')
    if node.get("note"):
        out.append('<p class="layer-note">' + esc(node["note"]) + '</p>')
    if node.get("child"):
        out.append(onion_html(node["child"], True))
    out.append('</details>' if nested else '</div>')
    return ''.join(out)


def onion_markdown(node):
    out = ["### " + md_safe(node["title"]), ""]
    for eq in node.get("formulas", []):
        eq = eq.replace("向上取整［用户并发×（1＋增长比例）］÷", "规划并发÷")
        out += ["**" + md_safe(eq) + "**", ""]
    if node["title"].startswith("第二层"):
        out += ["其中，规划并发＝向上取整［用户并发×（1＋增长比例）］。", ""]
    for title, equations in node.get("panels", []):
        out += ["#### " + md_safe(title), ""] + ["- " + md_safe(eq) for eq in equations] + [""]
    if node.get("note"):
        out += [md_safe(node["note"]), ""]
    if node.get("child"):
        out += onion_markdown(node["child"])
    return out


def calculation_rules_markdown(r):
    return [
        "## 二、计算规则", "",
        "先做理论预算，再核算达标基线容量，最后统一口径形成建议。公式只说明关系，具体数值放在测算过程。", "",
        "```mermaid", "flowchart LR", "  A[理论：资源约束] --> C[综合校核]", "  B[基线：达标容量] --> C", "  C --> D[工作组加备用组，换算卡数]", "```", "",
        "### 理论预算", "",
        "> 显存需求＝权重显存＋规划并发×每请求缓存", "",
        "根据模型参数、缓存结构、输入输出长度和TTFT、TPOT目标，确定同时满足显存、输入计算及生成计算约束的完整组数。采用有效能力，输入与生成分离部署时分别核对两侧资源。", "",
        "### 基线容量与卡数", "",
        "> 基线工作组数＝向上取整［用户并发×（1＋增长比例）÷基线达标并发］", "",
        "> 候选总卡数＝（工作组数＋备用组数）×每组卡数", "",
        "组数按完整配置取整；规划并发先向上取整。若另有持续请求速率要求，还须满足同一达标测试点的请求吞吐约束。理论与基线的卡数分别保留，综合时解释差异，不直接取平均或取最大值。", ""
    ]


def md_table(headers, rows):
    alignments = ["---:" if h in {"候选总量", "合计"} else "---" for h in headers]
    return ["| " + " | ".join(md_safe(x) for x in headers) + " |", "| " + " | ".join(alignments) + " |"] + ["| " + " | ".join(md_safe(x) for x in row) + " |" for row in rows] + [""]


def polish_markdown_spacing(text):
    """Apply typography to visible prose, leaving code and link targets intact."""
    output, fenced = [], False
    for line in text.splitlines():
        if line.startswith('```'):
            fenced = not fenced
            output.append(line)
            continue
        if fenced:
            output.append(line)
            continue
        pieces = re.split(r'(`[^`]*`|\]\([^)]*\)|https?://\S+)', line)
        for i in range(0, len(pieces), 2):
            value = pieces[i]
            for old, new in [('＝', ' = '), ('＋', ' + '), ('×', ' × '), ('÷', ' ÷ '), ('≤', ' ≤ ')]:
                value = value.replace(old, new)
            value = re.sub(r'(?<![<>=!])=(?!=)', ' = ', value)
            value = re.sub(r'(?<=[A-Za-z0-9%])(?=[\u4e00-\u9fff])|(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])', ' ', value)
            value = re.sub(r'(?<=[\u4e00-\u9fff])(?=\*\*[A-Za-z0-9])|(?<=[A-Za-z0-9])(?=\*\*[\u4e00-\u9fff])', ' ', value)
            value = re.sub(r'(?<=[\u4e00-\u9fff0-9])\*\*(?=[\u4e00-\u9fff])', '** ', value)
            value = re.sub(r'(?<=\S)/(?=[A-Za-z0-9\u4e00-\u9fff])', ' / ', value)
            value = re.sub(r' {2,}', ' ', value)
            pieces[i] = value
        rendered = ''.join(pieces).rstrip()
        if re.match(r'^(规划并发|并发所需组数|速率所需组数|工作卡数|候选总卡数)\s*[＝=]', rendered):
            rendered = '> ' + rendered
        output.append(rendered)
    for i in range(1, len(output) - 1):
        if not output[i] and output[i-1].startswith('> ') and output[i+1].startswith('> '):
            output[i] = '>'
    return '\n'.join(output) + '\n'


def client_markdown(r, evidence_filename="result.evidence.md"):
    d, e = r['demand'], r.get('selected')
    project = str(d.get('project') or 'LLM推理服务').split('｜')[0]
    lines = ['# ' + md_safe(project) + '算力测算说明', '', '测算时间：' + md_safe(display_date(r.get('createdAt'))) + '。', '']
    if simulated(r):
        lines += ['> **仅流程演示：以下性能基线为模拟数据。**', '']
    if e:
        q = e['result']
        lines += [f"**本次候选：{q['workCards']}张工作卡＋{q['spareCards']}张备用卡＝{q['totalCards']}张。**", '',
                  ('理论测算尚未完成，本次结果为基线容量候选。' if r.get('workflow', {}).get('integration', {}).get('status') == 'baseline_only' else md_safe(r.get('workflow', {}).get('integration', {}).get('conclusion', '候选待核对')) + '。'), '']
    else:
        lines += ['**当前不能给出有充分基线依据的卡数。**', '']
    lines += ['## 一、需求与部署条件', '', '本次按以下业务负载和延迟目标核算。', '']
    lines += md_table(['项目', '要求'], [
        ['模型', d.get('model')], ['输入 / 输出', f"{fmt(d.get('input'))} / {fmt(d.get('output'))}词元；{val(d.get('lengthStat'))}"],
        ['模型请求并发', f"{fmt(d.get('concurrency'))}路，增长预留{fmt(d.get('growth'))}%"],
        ['延迟目标', f"TTFT≤{fmt(d.get('ttft'))}毫秒（{val(d.get('ttftStat'))}）；TPOT≤{fmt(d.get('tpot'))}毫秒/词元（{val(d.get('tpotStat'))}）"],
        ['负载口径', f"{val(d.get('load'))}；缓存命中率{fmt(d.get('prefix'))}%；{val(d.get('reasoning'))}"],
        ['备用与请求速率', f"{fmt(d.get('spare'))}个完整备用组；" + (f"请求速率{fmt(d.get('rate'))}次/秒" if d.get('rate') is not None else '未提供持续请求速率')]
    ])
    config = []
    for k in ['chip', 'quant', 'framework', 'form', 'cpu']:
        if d.get(k):
            config.append(str(d[k]))
    lines += ['部署要求：' + md_safe('；'.join(config) or '沿用所选基线配置') + '。', '']
    lines += calculation_rules_markdown(r)
    lines += ['## 三、测算过程', '', '### 理论测算', '']
    compatible = [t for t in r.get('theoryEvidence', []) if t.get('candidate')]
    if compatible:
        lines += md_table(['理论依据', '工作卡 / 备用卡', '合计'], [[basename(t['source'].get('path')), f"{t['candidate']['workCards']} / {t['candidate']['spareCards']}", f"{t['candidate']['totalCards']}张"] for t in compatible])
        lines += ['上述为原理论假设下的待验证预算，采用条件与重算记录见附录。', '']
    else:
        lines += ['**完整理论卡数尚不能确定。** 工具已解析模型配置；缺少的模型实现依据、硬件能力或部署开销需继续核对，无需提供理论结果 JSON。', '']
        lines += md_table(['待补内容', '用于核算'], [['参数量与权重存储格式', '权重显存及计算量'], ['模型专属缓存预算与运行显存', '每组请求容量'], ['两侧部署资源与有效能力', '输入、生成及完整组数量']])
    for c in r.get('modelConfigEvidence', []):
        if c.get('state') not in {'associated', 'context_conflict'}:
            continue
        ctx = c.get('checks', {}).get('context')
        if ctx:
            lines += [f"配置检查：输入加输出＝{fmt(ctx['requested'])}词元，声明上限{fmt(ctx['declaredLimit'])}词元；" + ('未超过声明，部署支持仍需确认。' if ctx['withinDeclaredLimit'] else '**超过声明，应暂停采用候选并核对配置。**'), '']
        derived = c.get('derived', {})
        rows = []
        if 'weightTensorBytes' in derived:
            rows.append(['权重张量理论占用', f"{derived['weightTensorBytes'] / 2**30:.4f} GiB；未含量化元数据与运行开销"])
        if 'linearFlopsPerToken' in derived:
            rows.append(['每词元线性层近似计算量', f"{derived['linearFlopsPerToken'] / 10**12:.6f} TFLOP；未含注意力等额外运算"])
        kv = derived.get('standardKv')
        if kv:
            rows.append(['每请求标准缓存张量', f"{kv['bytesPerRequest'] / 2**30:.6f} GiB；未含分页与复制开销"])
        if rows:
            lines += md_table(['配置驱动的理论预算', '计算结果'], rows)
    lines += ['### 基线测算', '']
    if e:
        b, q, meta = e['baseline'], e['result'], e['metadata']
        lines += [f"采用**{md_safe(e['key'])}**：每组{b['cards']}卡，达标并发{fmt(b['concurrency'])}路，保持原并行策略及输入/生成配比。", '']
        lines += md_table(['校验项', '基线', '用户要求'], [
            ['输入 / 输出', b.get('io'), f"{fmt(d['input'])} / {fmt(d['output'])}词元"],
            ['TTFT', f"{fmt(b['ttft'])}毫秒（{val(meta['ttftStat'])}）", f"≤{fmt(d['ttft'])}毫秒（{val(d['ttftStat'])}）"],
            ['TPOT', f"{fmt(b['tpot'])}毫秒/词元（{val(meta['tpotStat'])}）", f"≤{fmt(d['tpot'])}毫秒/词元（{val(d['tpotStat'])}）"]
        ])
        if e['state'] == 'near_reference':
            lines += ['**存在差异，按保守近似处理**；沿用原测试并发，不因请求更短提高容量。', '']
        lines += ['**工作配置**', '', f"规划并发＝向上取整［{fmt(d['concurrency'])}×（1＋{fmt(d['growth'])}%）］＝{fmt(d['plannedConcurrency'])}路", '',
                  f"并发所需组数＝向上取整［{fmt(d['plannedConcurrency'])}÷{fmt(b['concurrency'])}］＝{q['concurrencyGroups']}组", '']
        if d.get('plannedRate') is not None:
            lines += [f"速率所需组数＝向上取整［{fmt(d['plannedRate'])}÷{fmt(meta['qps'])}］＝{q['rateGroups']}组；工作组数＝较大值（{q['concurrencyGroups']}，{q['rateGroups']}）＝{q['workGroups']}组", '']
        lines += [f"工作卡数＝{q['workGroups']}×{b['cards']}＝{q['workCards']}张", '', '**含备用的总量**', '',
                  f"候选总卡数＝（{q['workGroups']}＋{q['spareGroups']}）×{b['cards']}＝**{q['totalCards']}张**；其中备用{q['spareCards']}张。", '']
    else:
        reasons = r.get('missingRequirements', []) + r.get('modelConfigIssues', [])
        reasons += [reason for ev in r.get('evaluations', []) for reason in ev.get('reasons', [])]
        lines += ['当前没有可用达标基线；' + md_safe('；'.join(dict.fromkeys(localize(x) for x in reasons)) or '需补充同配置测试数据') + '。', '']
    if r.get('evaluations'):
        lines += ['其他记录的筛选结果如下，完整条件见附录。', '']
        rows = []
        for ev in r['evaluations']:
            result = ev.get('result')
            reason = '本次采用' if e and ev['key'] == e['key'] else '达标备选' if result else '；'.join(localize(x) for x in ev.get('reasons', [])) or state(ev['state'])
            rows.append([ev['key'], f"{result['totalCards']}张" if result else '未采用', reason])
        lines += md_table(['基线记录', '候选总量', '采用或排除依据'], rows)
    lines += ['## 四、综合建议', '']
    if e:
        lines += [f"保留**{q['totalCards']}张卡**作为基线候选，理论与部署校核完成后再定案。" if not compatible else '已有理论和基线两类候选，须完成假设与差异核对后定案。', '']
        ties = [ev for ev in r.get('candidates', []) if ev['result']['totalCards'] == q['totalCards']]
        if len(ties) > 1:
            lines += ['同总卡数方案的工作能力和备用规模不同。', '']
            lines += md_table(['方案', '工作卡 / 备用卡', '工作组并发预算'], [[ev['key'], f"{ev['result']['workCards']} / {ev['result']['spareCards']}", f"{ev['result']['workGroups']}×{ev['baseline']['concurrency']}＝{ev['result']['workGroups'] * ev['baseline']['concurrency']}路"] for ev in ties])
            lines += ['当前按输入顺序展示首个同等级、同卡数方案，未比较成本与故障域。', '']
    else:
        lines += [md_safe(r.get('workflow', {}).get('integration', {}).get('conclusion', '依据不足，暂不确定卡数')) + '。', '']
    lines += ['后续重点确认：', '', '- 补齐理论参数与模型专属缓存预算，核验权重修订、量化及框架支持。',
              '- 验证多组流量分配、持续负载及相同统计口径下的TTFT、TPOT。', '- 确认备用组故障域与切换能力；整机数量需有部署配置依据。', '',
              '## 测算依据', '', f"引用的测试条件、核对口径、模型配置及文件摘要见[测算依据附录]({evidence_filename})。", '']
    return polish_markdown_spacing('\n'.join(lines))


def client_evidence_markdown(r):
    lines = ['# 算力测算依据附录', '', '本附录保留来源与测试口径，供核对正文；文件摘要用于确认版本，不证明数据真实性。', '']
    if simulated(r):
        lines += ['> **本案例基线为模拟数据，核对信息仅确认演练设定。**', '']
    for ev in r.get('evaluations', []):
        b, meta = ev['baseline'], ev['metadata']
        lines += ['## ' + md_safe(ev['key']), '', '筛选结论：' + state(ev['state']) + '。', '']
        rows = [[LABELS.get(k, k), b.get(k, '未提供')] for k in ['model', 'chip', 'quant', 'framework', 'form', 'cpu', 'parallel']]
        rows += [['输入 / 输出', b.get('io')], ['并发 / 每组卡数', f"{b.get('concurrency')} / {b.get('cards')}"],
                 ['TTFT / TPOT', f"{b.get('ttft')} / {b.get('tpot')}"], ['基线状态', b.get('status')], ['更新时间', b.get('updated')]]
        rows += [[LABELS.get(k, k), val(meta.get(k))] for k in ['ttftStat', 'tpotStat', 'load', 'lengthStat', 'reasoning', 'kBase']]
        rows += [[LABELS[k], val(meta[k])] for k in ['cardCountScope', 'prefillCards', 'decodeCards'] if k in meta]
        rows += [['同点请求吞吐', meta.get('qps')], ['口径核对来源', meta.get('source')], ['原始记录摘要', ev.get('rawHash')]]
        lines += md_table(['项目', '依据'], rows)
        reasons = ev.get('reasons', []) + ev.get('notes', [])
        if reasons:
            lines += ['- ' + md_safe(localize(x)) for x in reasons] + ['']
    appendix = document(r)['sections'][-1]
    lines += ['## 模型配置与来源追溯', '']
    for c in r.get('modelConfigEvidence', []):
        lines += ['### ' + md_safe(c.get('modelName') or '未绑定模型'), '',
                  '配置文件：' + md_safe(c['source']['path']) + '；摘要：' + md_safe(c['configHash']) + '。', '']
        derived = c.get('derived', {})
        counts = derived.get('declaredParameters', {})
        if counts:
            lines += ['参数量采用配置显式声明，未通过权重张量清单独立核验。', '']
        if 'weightTensorBytes' in derived:
            lines += [f"> 权重张量占用＝配置总参数量 × 目标每参数字节数＝{derived['weightTensorBytes']} Byte。", '']
        if 'linearFlopsPerToken' in derived:
            lines += [f"> 每词元线性层近似计算量＝2 × 配置激活参数量＝{derived['linearFlopsPerToken']} FLOP。", '']
        kv = derived.get('standardKv')
        if kv:
            lines += ['> 标准缓存公式：' + md_safe(kv['formula']), '',
                      '> 数值代入：' + md_safe(kv['substitution']) + f"＝{kv['bytesPerToken']} Byte/Token。", '']
        lines += ['- ' + md_safe(x) for x in c.get('notes', [])] + ['']
    for t in r.get('theoryEvidence', []):
        basis = t.get('original', {}).get('basis', [])
        if basis:
            lines += ['### 工具生成的理论预算依据', '']
            lines += ['- ' + md_safe(x) for x in basis] + ['']
    for block in appendix['blocks']:
        if block[0] == 'p':
            lines += [md_safe(block[1]), '']
        elif block[0] == 'list':
            lines += ['- ' + md_safe(x) for x in block[1]] + ['']
        elif block[0] == 'table':
            lines += md_table(block[1], block[2])
    return polish_markdown_spacing('\n'.join(lines))


def svg_diagram(kind, selected):
    """Native SVG needs no network or Mermaid runtime. All labels are escaped."""
    if kind == "model":
        boxes = [(15, 90, 170, ["共同需求", "并发、长度、延迟与配置"]),
                 (230, 20, 240, ["① 理论测算", "权重 / 缓存显存＋输入 / 生成计算"]),
                 (230, 160, 240, ["② 基线测算", "匹配测试点 → 所需完整工作组"]),
                 (515, 90, 190, ["③ 综合校核", "统一口径、解释差异"]),
                 (750, 90, 150, ["候选总卡数", "完整组数 × 每组卡数"])]
        edges = [(185, 120, 226, 60), (185, 140, 226, 200), (470, 60, 511, 120), (470, 200, 511, 140), (705, 130, 746, 130)]
        height = 270
    elif kind == "decision":
        boxes = [(15, 25, 270, ["① 统一比较口径", "模型、配置、负载与工作/备用"]), (320, 25, 270, ["② 检查资源冲突", "核对显存、布局与有效能力"]), (625, 25, 270, ["③ 解释差异后给建议", "缺项或冲突未解决 → 补充 / 补测"])]
        edges, height = [(285, 65, 316, 65), (590, 65, 621, 65)], 135
    elif kind == "allocation":
        b, q = selected["baseline"], selected["result"]
        boxes = [(20, 30, 260, ["工作资源", f"{q['workGroups']}组 × {b['cards']}卡 = {q['workCards']}卡"]),
                 (320, 30, 260, ["备用资源", f"{q['spareGroups']}组 × {b['cards']}卡 = {q['spareCards']}卡"]),
                 (620, 30, 260, ["合计候选", f"{q['totalCards']}卡"])]
        edges, height = [(580, 70, 616, 70)], 135
    elif kind == "flow":
        boxes = [(20, 30, 260, ["① 理论测算", "显存、计算预算与参数缺项"]),
                 (320, 30, 260, ["② 基线测算", "配置匹配、延迟与完整部署组"]),
                 (620, 30, 260, ["③ 综合判断", "比较口径、解释差异与建议"])]
        boxes += [(240, 150, 420, ["两条路径独立计算，最后交叉检查", "缺项明确列出，冲突先核对，不机械取大"])]
        edges = [(280, 70, 316, 70), (580, 70, 616, 70), (750, 110, 660, 150)]
        height = 255
    else:
        boxes = [(15, 18, 270, ["并发路径", "规划并发 ÷ 实测并发，向上取整"]),
                 (15, 128, 270, ["可选速率路径", "规划速率 ÷ 实测请求吞吐，向上取整"]),
                 (330, 70, 230, ["工作组数取较大值", "两种约束同时满足"]),
                 (620, 70, 260, ["总候选卡数", "（工作组＋备用组）× 每组卡数"])]
        edges = [(285, 58, 326, 100), (285, 168, 326, 122), (560, 110, 616, 110)]
        height = 235
    title = {"flow": "理论、基线与综合测算流程图", "rule": "完整部署组计算规则", "allocation": "工作与备用资源构成", "decision": "综合判断规则", "model": "理论与基线共同校核的整体计算模型"}[kind]
    parts = [f'<svg viewBox="0 0 910 {height}" role="img" aria-label="{title}" xmlns="http://www.w3.org/2000/svg"><title>{title}</title>',
             '<defs><marker id="arrow-'+kind+'" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#54828b"/></marker></defs>']
    for x1, y1, x2, y2 in edges:
        parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#54828b" stroke-width="2" fill="none" marker-end="url(#arrow-{kind})"/>')
    for x, y, w, text in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="80" rx="9" fill="#edf6f7" stroke="#8cbbc0"/>')
        for i, line in enumerate(text):
            parts.append(f'<text x="{x+w/2}" y="{y+29+i*25}" text-anchor="middle" font-size="{15 if i==0 else 12}" fill="#193d49">{escape(line)}</text>')
    if kind == "allocation":
        parts.append('<text x="300" y="78" text-anchor="middle" font-size="24" fill="#193d49">＋</text>')
    return "".join(parts) + "</svg>"


def client_html(r):
    doc = document(r)
    e = lambda value: escape(str(value), quote=True)
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>' + e(doc["title"]) + '</title><style>',
             '.readable-equation{margin:12px 0;padding:17px 20px;background:#f6f9fa;border:1px solid #dce5e8;border-radius:7px}.equation-output{font-size:17px;font-weight:650;color:#087e83;margin-bottom:10px}.equation-expression{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.equation-equals{font-size:22px;color:#647580}.math-scroll{overflow-x:auto;max-width:100%;padding:5px 0}math{font-size:19px;margin:0}mtext{font-family:system-ui,"Microsoft YaHei",sans-serif}.rounding{font-size:12px;color:#526b74;border:1px solid #cbdde1;border-radius:4px;padding:3px 8px}.equation-explanation{font-size:13px;color:#647580;margin-top:10px}.formula-root .equation-grid{grid-template-columns:1fr}.formula-root .equation-panel{padding:10px 16px}.formula-root .equation-panel h4{padding:8px 4px}.formula-layer{margin-top:16px;border:1px solid #dce5e8;border-radius:8px;padding:14px 18px}.formula-layer>summary{font-size:16px;color:#087e83}.layer-note{font-size:13px;color:#647580}.equation-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0}.equation-panel{border:1px solid #dce5e8;border-radius:8px;padding:16px 20px}.equation-panel h4{margin:0 0 10px;color:#087e83;font-size:17px}.equation-row{padding:11px 0;border-top:1px solid #e6edef;line-height:1.9;font-size:14px;overflow-wrap:anywhere}.formula{padding:14px 18px;margin:16px 0;border-left:3px solid #087e83;background:#f1f7f8;font-size:18px;font-weight:600;overflow-wrap:anywhere}.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.status-card{padding:16px;border:1px solid #dce5e8;border-radius:8px}.status-card span,.status-card small{display:block;color:#647580}.status-card strong{display:block;font-size:24px;margin:7px 0}.status-card small{font-size:12px}body{margin:0;background:#f3f7f8;color:#193441;font:15px/1.8 system-ui,"Microsoft YaHei",sans-serif}*{box-sizing:border-box}header,main{max-width:1100px;margin:auto;padding:28px}h1{font-size:29px;margin:8px 0}h2,summary{font-size:20px;font-weight:650}h3{font-size:17px;margin:26px 0 10px;border-left:3px solid #087e83;padding-left:10px}p{margin:10px 0}.meta{color:#647580;font-size:13px}.tag{color:#087e83;letter-spacing:2px;font-size:12px}section{background:white;border:1px solid #dce5e8;border-radius:12px;padding:26px;margin:0 0 20px}details summary{cursor:pointer}details[open] summary{margin-bottom:20px}table{width:100%;border-collapse:collapse;font-size:14px;margin:14px 0}td,th{padding:10px 12px;text-align:left;border-bottom:1px solid #dce5e8;vertical-align:top;overflow-wrap:anywhere}th{background:#f1f7f8}td:first-child{min-width:100px}.table{overflow-x:auto}svg{width:100%;display:block;min-width:640px}.diagram{overflow-x:auto;margin:18px 0}ul{padding-left:23px}.notice{background:#fff5df;border-left:4px solid #b7812e;padding:13px 18px;margin:15px 0}.nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.nav a{padding:5px 10px;border:1px solid #cbdde1;border-radius:6px;font-size:13px;color:#087e83;text-decoration:none}button{font:inherit;padding:8px 15px;border:1px solid #b9d5d9;border-radius:6px;background:white;color:#087e83;cursor:pointer}.tools{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.foot{color:#687e87;font-size:12px;margin:20px 0}a{color:#087e83}@media(max-width:600px){.equation-grid{grid-template-columns:1fr}.formula{font-size:16px}.status-grid{grid-template-columns:1fr}.status-card{padding:12px}.status-card strong{font-size:21px}header,main{padding:16px}section{padding:18px}h1{font-size:23px}h2,summary{font-size:18px}table{font-size:13px}}@media print{body{background:white;font-size:11px}header,main{padding:10px}.tools,.nav{display:none}section{padding:14px;border-radius:0}h1{font-size:23px}h2,summary{font-size:16px}table{font-size:10px}.table{overflow:visible}svg{min-width:0}.diagram{overflow:visible}tr{break-inside:avoid}}',
             '</style></head><body><header><div class="tag">LLM INFERENCE CAPACITY / 测算说明</div><h1>' + e(doc["title"]) + '</h1>',
             '<div class="meta">结论类型：' + e(doc["level"]) + ' · 规则版本：' + e(doc["version"]) + ' · ' + e(display_date(doc["date"])) + '</div>']
    if doc["simulation"]:
        parts.append('<div class="notice"><strong>仅流程演示：</strong>采用合成数据，不是实测验收或采购依据。</div>')
    parts += ['<div class="tools"><button onclick="window.print()">打印 / 保存PDF</button><button id="expand">展开全部依据</button></div><nav class="nav">']
    for i, sec in enumerate(doc["sections"]):
        parts.append(f'<a href="#s{i}">{e(sec["title"])}</a>')
    parts.append('</nav></header><main>')
    for i, sec in enumerate(doc["sections"]):
        parts.append(f'<section id="s{i}">')
        if sec["deep"]:
            parts.append('<details><summary>' + e(sec["title"]) + '</summary>')
        else:
            parts.append('<h2>' + e(sec["title"]) + '</h2>')
        for block in sec["blocks"]:
            if block[0] == "onion":
                parts.append(onion_html(block[1]))
            elif block[0] == "equations":
                parts.append('<div class="equation-grid">' + ''.join('<div class="equation-panel"><h4>' + e(title) + '</h4>' + ''.join('<div class="equation-row">' + e(eq) + '</div>' for eq in equations) + '</div>' for title, equations in block[1]) + '</div>')
            elif block[0] == "formula":
                parts.append('<div class="formula">' + e(block[1]).replace("\n", "<br>") + '</div>')
            elif block[0] == "cards":
                parts.append('<div class="status-grid">' + "".join('<div class="status-card"><span>' + e(row[0]) + '</span><strong>' + e(row[1]) + '</strong><small>' + e(row[2]) + '</small></div>' for row in block[1]) + '</div>')
            elif block[0] == "h3":
                parts.append("<h3>" + e(block[1]) + "</h3>")
            elif block[0] == "p":
                parts.append('<p>' + e(block[1]) + '</p>')
            elif block[0] == "list":
                parts.append('<ul>' + ''.join('<li>' + e(x) + '</li>' for x in block[1]) + '</ul>')
            elif block[0] == "table":
                parts.append('<div class="table"><table><thead><tr>' + ''.join('<th>' + e(x) + '</th>' for x in block[1]) + '</tr></thead><tbody>')
                parts.extend('<tr>' + ''.join('<td>' + e(x) + '</td>' for x in row) + '</tr>' for row in block[2])
                parts.append('</tbody></table></div>')
            elif block[0] == "diagram":
                parts.append('<div class="diagram">' + svg_diagram(block[1], doc["selected"]) + '</div>')
        if sec["deep"]:
            parts.append('</details>')
        parts.append('</section>')
    parts.append('<p class="foot">本文件可离线阅读。图、公式和数值来自同一次测算结果；任何输入变化后均应重新核算。</p></main>')
    parts.append('''<script>
document.getElementById('expand').onclick=()=>document.querySelectorAll('details').forEach(d=>d.open=true);
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{const section=document.querySelector(a.getAttribute('href'));const d=section&&section.querySelector('details');if(d)d.open=true}));
let before=null;window.addEventListener('beforeprint',()=>{if(before===null)before=Array.from(document.querySelectorAll('details')).map(d=>d.open);document.querySelectorAll('details').forEach(d=>d.open=true)});window.addEventListener('afterprint',()=>{if(before!==null){document.querySelectorAll('details').forEach((d,i)=>d.open=before[i]);before=null}});
</script></body></html>''')
    return ''.join(parts)
