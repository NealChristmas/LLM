"""Reference-style branching SVG; presentation only, reads report.json."""
from pathlib import Path
import json,html,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'report.json').read_text(encoding='utf-8'));c=r['central'];p=c['phase']['prefill'];d=c['phase']['decode'];a=r['assumptions'];cache=r['cache'];cards=r['budgetCards'];q=r['request']
W,H=2200,1720
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#8f999f"/></marker></defs><rect width="100%" height="100%" fill="white"/><style>text{{font-family:Microsoft YaHei,Noto Sans CJK SC,sans-serif;fill:#135b96;font-size:22px;text-anchor:middle}}.head{{font-weight:700;font-size:25px}}.note{{font-size:21px;fill:#637586}}.edge{{fill:none;stroke:#9ca3a7;stroke-width:1.8;marker-end:url(#arrow);stroke-linejoin:round}}</style>']
boxes=[]
def box(x,y,w,h,lines,kind='blue'):
 color,stroke={'blue':('#e5f2ff','#d0dce5'),'yellow':('#fff3cf','#dba439'),'green':('#e1f2e3','#69a66f')}[kind]
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{color}" stroke="{stroke}" stroke-width="1.5"/>')
 step=32;top=y+(h-len(lines)*step)/2+24
 for i,t in enumerate(lines):svg.append(f'<text x="{x+w/2}" y="{top+i*step}" class="{ "head" if i==0 else "" }">{html.escape(t)}</text>')
 boxes.append((x,y,w,h,lines))
def edge(points):svg.append('<path class="edge" d="M'+' L'.join(f'{x} {y}' for x,y in points)+'"/>')
# Draw links first, all routed in gutters so text is never crossed.
edge([(1100,220),(1100,250),(510,250),(510,280)])
edge([(1100,220),(1100,250),(1635,250),(1635,280)])
for x in [180,510,840]:edge([(510,355),(510,380),(x,380),(x,410)])
for x in [1225,1515,1805,2095]:edge([(1635,355),(1635,380),(x,380),(x,410)])
for x in [180,510,840]:edge([(x,580),(x,620),(510,620),(510,665)])
edge([(510,800),(510,860)]);edge([(510,985),(510,1055)])
for x in [1225,1515]:edge([(x,580),(x,620),(1370,620),(1370,665)])
for x in [1805,2095]:edge([(x,580),(x,620),(1950,620),(1950,665)])
edge([(1370,860),(1370,935)]);edge([(1950,860),(1950,935)])
for x,y in [(510,1175),(1370,1075),(1950,1075)]:edge([(x,y),(x,1225),(1100,1225),(1100,1270)])
edge([(1100,1400),(1100,1450)])
# Main input box.
box(640,25,920,195,['需求与计算参数 · 固定参考布局',f"平均输入 {q['inputTokens']:,} / 输出 {q['outputTokens']:,} Token；并发 {r['plannedConcurrency']} 路",'平均 TTFT ≤ 3秒；平均 TPOT ≤ 50毫秒/Token','A3-560T：每物理卡128 GB、INT8峰值1,120 TOPS','W8A8；KV INT8为假设；Prefix Cache命中率0'])
box(300,280,420,75,['显存计算 · 每物理卡'])
box(1425,280,420,75,['性能计算 · 按推理实例'])
# Memory branches.
box(30,410,300,170,['权重驻留预算','专家分片＋非专家复制','及草稿、保留模块',f"Prefill ≈ {p['cardWeightGiB']:.2f} GiB",f"Decode ≈ {d['cardWeightGiB']:.2f} GiB"])
box(360,410,300,170,['KV Cache预算',f"每请求 {cache['logicalBytesPerRequest']/2**20:.2f} MiB × 1.25",'按请求分配及复制计入',f"Prefill ≈ {p['cardCacheGiB']:.2f} GiB",f"Decode ≈ {d['cardCacheGiB']:.2f} GiB"])
box(690,410,300,170,['运行预留',f"每物理卡 {a['runtimeGiBPerCard']:g} GiB",'覆盖工作区等预算','并非现场分配峰值','不再另扣显存可用比例'])
box(220,665,580,135,['每物理卡显存需求','权重驻留预算＋缓存预算＋运行预留',f"Prefill ≈ {p['cardWeightGiB']:.2f}＋{p['cardCacheGiB']:.2f}＋16 ≈ {p['cardTotalGiB']:.2f} GiB",f"Decode ≈ {d['cardWeightGiB']:.2f}＋{d['cardCacheGiB']:.2f}＋16 ≈ {d['cardTotalGiB']:.2f} GiB"])
box(220,860,580,125,['与单卡容量比较','128 GB十进制标称容量 ≈ 119.21 GiB',f"Prefill {p['cardTotalGiB']:.2f}、Decode {d['cardTotalGiB']:.2f} 均低于标称容量",'卡内仅按均匀分片假设核算，真实峰值待验证'])
box(220,1055,580,120,['显存约束判断','当前 Prefill 8张＋Decode 8张布局','假设分片下容量可容纳','不等于已确定显存所需最少卡数'])
# Independent work and effective capability branches.
box(1090,410,270,170,['Prefill工作量','输入Token数 × 2', '× Prefill激活参数','8,000 × 2 × 80亿',f"＝ {r['inputWorkTopPerRequest']:g} TOP / 请求"])
box(1380,410,270,170,['Prefill有效算力','每实例2张物理卡','卡数 × 单卡峰值 × 效率','2 × 1,120 × 40%',f"＝ {p['effectiveTopsPerInstance']:g} TOPS"])
box(1670,410,270,170,['Decode工作量','2 × Decode激活参数','2 × 160亿',f"＝ {r['decodeWorkTopPerToken']:g} TOP / Token",'草稿额外工作预算 ×1.25'])
box(1960,410,270,170,['Decode有效算力','每实例1张物理卡','卡数 × 单卡峰值 × 效率','1 × 1,120 × 2%',f"＝ {d['effectiveTopsPerInstance']:g} TOPS"])
box(1090,665,560,195,['平均 TTFT 预算','60路 ÷ 4个Prefill实例 ＝ 每实例15路','平均完成顺序＝(1＋15)÷2＝8','固定开销＋工作量÷有效算力×平均完成顺序','≈ 0.300＋(128÷896)×8',f"≈ {c['meanTtftBudgetMs']/1000:.2f} 秒"])
box(1670,665,560,195,['TPOT 预算近似','60路 ÷ 8个Decode实例，最繁忙8路','并发×每Token工作量×草稿系数÷有效算力','再换算毫秒并加入固定开销','≈ 8×0.032×1.25÷22.4×1,000＋2',f"≈ {c['busyDecodeStepBudgetMs']:.1f} 毫秒/Token"])
box(1090,935,560,140,['TTFT 约束判断',f"预算 {c['meanTtftBudgetMs']/1000:.2f} 秒 ≤ 平均目标 3秒",'均衡、逐请求先到先服务的简化模型','40%效率、300毫秒固定开销均为假设'])
box(1670,935,560,140,['TPOT 约束判断',f"近似 {c['busyDecodeStepBudgetMs']:.1f} ≤ 目标 50毫秒/Token",'以最繁忙实例步长近似，非真实平均值','2%效率与额外开销均为未校准假设'])
box(700,1270,800,130,['同时核对显存、TTFT和TPOT预算','当前固定布局在所列假设下满足三项约束','未搜索更小布局；未验证通信、主机卸载及KV INT8支持','不把满足三项预算理解为真实部署达标'])
box(700,1450,800,130,['当前参考布局的理论预算候选','工作卡＝Prefill 8张＋Decode 8张＝16张物理卡','备用卡＝0；总计16张物理卡','更小布局尚未评估，不能称为全局最少卡数'],'green')
box(300,1620,1600,75,['适用限制：KV INT8格式、有效效率、KV传输、Engram卸载和实际运行峰值均待验证。'],'yellow')
svg.append('</svg>')
# Extend canvas slightly past the rightmost nodes, without scaling text.
svg[0]=svg[0].replace('width="2200"','width="2260"').replace('viewBox="0 0 2200 1720"','viewBox="0 0 2260 1720"')
path=ROOT/'sizing-flow.svg';path.write_text('\n'.join(svg),encoding='utf-8');ET.parse(path)
assert all(t not in path.read_text(encoding='utf-8') for t in ['Device','输入侧','生成侧','进程'])
assert all(x>=0 and y>=0 and x+w<=2260 and y+h<=1720 for x,y,w,h,lines in boxes)
print('Reference-style branching flow drawn; 20 boxes checked within canvas; numerical result unchanged.')
