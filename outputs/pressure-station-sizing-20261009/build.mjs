import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=new URL('.',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1');
const w=Workbook.create(), rough=w.worksheets.add('粗略估算'), s=w.worksheets.add('填写与核算'), h=w.worksheets.add('硬件与依据');
for(const sh of [rough,s,h]){sh.showGridLines=false;sh.getRange('A1:D85').format.font={name:'Arial',size:11,color:'#243247'};sh.getRange('A1:D85').format.rowHeight=32;sh.getRange('A1:D85').format.verticalAlignment='center';sh.getRange('A1:A85').format.columnWidth=40;sh.getRange('B1:B85').format.columnWidth=29;sh.getRange('C1:C85').format.columnWidth=13;sh.getRange('D1:D85').format.columnWidth=86;sh.getRange('D1:D85').format.wrapText=true;}
const val=(r,a,b,c,d)=>s.getRange(`A${r}:D${r}`).values=[[a,b,c,d]];
const fx=(r,f)=>s.getRange(`B${r}`).formulas=[[f]];
const band=(r,text)=>{val(r,text,null,null,null);s.getRange(`A${r}:D${r}`).format.fill='#263F60';s.getRange(`A${r}:D${r}`).format.font={bold:true,color:'#FFFFFF'};};
const input=(r,a,b,c,d)=>{val(r,a,b,c,d);s.getRange(`B${r}`).format.fill='#FFF0BF';s.getRange(`B${r}`).format.font.color='#174B91';};
val(2,'调压站智能体计算卡核算',null,null,'核对日期：2026-10-09。适用于本地大模型推理，不含训练资源。');s.getRange('A2').format.font={size:16,bold:true};
val(3,'详细核算（可选）',null,null,'初步预算请使用第一张“粗略估算”。本页保留具体模型参数和同配置压测核算，不影响粗估结果。');
band(5,'自动核算结果');
val(6,'容量下限（主模型物理卡）',null,'张','按显存能容纳的并发计算。尚未验证速度，不含备用与辅助模型。');fx(6,'=IF(ISNUMBER(B63),B63*B36,"待填写容量参数")');
val(7,'采购规划数量（物理卡）',null,'张','性能证据完整时计算：工作副本 + 在线备用副本 + 额外模型用卡。');fx(7,'=IF(ISNUMBER(B69),B69,"待补齐参数与压测")');
val(8,'服务器规划数（分开部署）',null,'台','主模型按完整副本装箱，辅助卡另配服务器；同一副本在一台内，未计故障域隔离。');fx(8,'=IF(ISNUMBER(B69),ROUNDUP((B66+B42)/ROUNDDOWN(B40/B36,0),0)+ROUNDUP(B43/B40,0),"待核算")');
val(9,'核算状态',null,null,'兼容性与单芯片峰值内存须供应商确认。备用副本数不自动代表可承受整机故障。');fx(9,'=IF(B54<>"参数有效",B54,IF(B62<1,"所选分组放不下一路请求",IF(B65<>"证据齐全",B65,"已给出规划数量，待采购验收")))');
band(11,'客户填写：业务峰值与服务要求');
input(12,'项目 / 客户名称',null,'文本','填写客户名称与部署范围。');
input(13,'峰值业务请求速率',null,'次/秒','填写告警、问答、巡检报告等同时到达的总业务请求峰值。不要填日平均值。');
input(14,'每次业务平均模型调用次数',null,'次','包含规划、工具返回后的再推理、校验等。多个模型分开核算，不能重复计入。');
input(15,'重试与额外调用系数',1,'倍','1 表示没有额外调用；1.1 表示在上述调用次数外再增加 10%。');
input(16,'峰值同时在推理的模型请求',null,'路','填写活动生成序列数，含 Agent 内部并行调用；不是注册用户数或站点总数。');
input(17,'单次模型输入 Token 上限',null,'Token','含系统提示、历史、RAG 检索材料和工具结果。多个调用采用规划上限。');
input(18,'单次模型输出 Token 上限',null,'Token','含思考 Token（如启用）与最终回答。与输入上限相加作为 KV 规划长度。');
input(19,'业务增长余量',0.2,'比例','同时作用于请求速率与活动并发。20% 为可修改规划假设，不是实测结论。');
input(20,'首 Token 延迟目标 P95',null,'秒','TTFT，供应商压测必须满足。工具处理与检索耗时另列预算。');
input(21,'单次模型完成延迟目标 P95',null,'秒','包含排队、Prefill 与 Decode；不是整个多轮 Agent 的完成时间。');
band(23,'研发填写：模型与显存');
input(24,'模型名称 / 版本 / 精度方案',null,'文本','填实际检查点版本与量化方法。多模型独立部署可分别复制表核算后汇总。');
input(25,'模型总参数量',null,'十亿参数','例如 7 表示 7B。MoE 必须填写总参数，不能用激活参数估算权重内存。');
input(26,'权重有效字节数 / 参数',2,'Byte','FP16/BF16 为 2；INT8 理想值 1；INT4 理想值 0.5，量化元数据另加。精度须有后端支持。');
input(27,'权重额外内存比例',0.1,'比例','覆盖量化尺度、未量化参数等。10% 为可修改假设，最好按实际加载内存校准。');
input(28,'KV 计算方式','标准MHA/GQA','选项','普通 MHA/GQA 用下方结构公式；MLA、混合注意力等选择自定义并填实测/结构推导值。');
input(29,'注意力层数',null,'层','从实际模型 config.json 读取；自定义 KV 模式不使用此项。');
input(30,'每层 KV 头数',null,'个','num_key_value_heads，不能直接用 Query 头数代替。');
input(31,'每个 KV 头维度',null,'维','head_dim，确认 K/V 维度相同；不同则改用自定义。');
input(32,'KV 每个元素的字节数',2,'Byte','BF16/FP16 为 2；不要根据权重量化精度推定 KV 精度。');
input(33,'自定义 KV 每 Token 内存',null,'Byte','整个模型、单序列、未计分组复制。包含量化元数据等；自定义模式必填。');
input(34,'分组内 KV 复制 / 开销系数',1,'倍','理想均匀切分为 1；KV 头不能均分、缓存复制或块取整时须增加，并确认单芯片峰值。');
band(35,'研发与供应商填写：物理卡与部署');
input(36,'每个模型副本使用物理卡数',null,'张','一个副本是独立服务实例，可由同一服务器内多卡协同推理。须采用后端支持的并行分组。');
input(37,'每张物理卡的计算芯片数',null,'个','Duo 为双芯片，其他型号按所采购 SKU 填；计算芯片数与卡数分别统计。');
input(38,'单芯片名义设备内存',null,'GiB','明确按 GiB=2^30 Byte 填入；若厂家给十进制 GB，乘 10^9/2^30 转换。参考页供核对。');
input(39,'设备内存可用比例',0.85,'比例','扣除驱动、不可用内存与安全余量。85% 为规划假设，应以 npu-smi / 引擎实测校准。');
input(40,'每台服务器允许安装物理卡数',null,'张','主模型与辅助服务按相同插槽容量、分开部署估算。须核对机箱、功耗与互联；模组按 BOM 口径。');
input(41,'每芯片运行时额外内存',null,'GiB','含激活、算子工作区、通信缓冲、图缓存；必须为规划上下文 / batch 测量或留足预算。');
input(42,'在线备用模型副本数',1,'组','备用与工作副本配置相同。默认 1 为规划假设；0 允许无备用。');
input(43,'辅助服务额外物理卡数',0,'张','Embedding、Reranker、视觉、语音等独立占用的卡。0 需确认可用 CPU 或已计入其他部署。');
input(44,'型号 / SKU / 服务器配置',null,'文本','填写精确 SKU、内存版本、互联方式与 CANN / MindIE / vLLM-Ascend 版本。');
band(46,'供应商填写：同配置并发压测证据');
input(47,'单副本达标模型请求吞吐',null,'次/秒','同模型、精度、分组、输入输出长度与混合业务下，同时满足两项 P95 目标的完成吞吐。');
input(48,'单副本达标活动并发上限',null,'路','与上项同次压测、同负载。吞吐与并发均须稳定达标，禁止使用理论 TFLOPS 替代。');
input(49,'实测首 Token 延迟 P95',null,'秒','同次压测报告中的 TTFT。');
input(50,'实测单次模型完成延迟 P95',null,'秒','同次压测报告中的完成延迟。');
input(51,'压测报告 / 日期 / 配置',null,'文本','填写报告编号、日期及配置摘要。还应记录失败率、运行时长与长上下文峰值内存。');
input(52,'部署兼容性与内存切分已确认','待确认','选项','供应商确认模型/量化/后端/互联可用，以及最忙芯片内存可容纳。确认后才输出采购规划数。');
band(53,'计算过程（灰色区域自动更新）');
val(54,'容量参数检查',null,null,'缺项或数值非法时停止计算。自定义 KV 模式不要求标准结构参数。');
const req=[13,14,15,16,17,18,25,26,34,36,37,38,39,40];
const bad=req.map(r=>`NOT(ISNUMBER(B${r})),B${r}<=0`).join(',');
const ints=[16,17,18,36,37,40,42,43].map(r=>`B${r}<>INT(B${r})`).join(',');
fx(54,`=IF(OR(${bad},NOT(ISNUMBER(B19)),B19<0,NOT(ISNUMBER(B27)),B27<0,B39>1,NOT(ISNUMBER(B41)),B41<0,NOT(ISNUMBER(B42)),B42<0,NOT(ISNUMBER(B43)),B43<0,B15<1,B34<1,${ints}),"请补齐或修正黄色容量参数",IF(B28="标准MHA/GQA",IF(OR(COUNT(B29:B32)<>4,MIN(B29:B32)<=0,B29<>INT(B29),B30<>INT(B30),B31<>INT(B31)),"请补齐或修正KV结构参数","参数有效"),IF(B28="自定义",IF(OR(NOT(ISNUMBER(B33)),B33<=0),"请填写自定义KV内存","参数有效"),"请选择有效KV方式")))`);
val(55,'规划模型请求速率',null,'次/秒','业务请求速率 × 模型调用次数 × 重试系数 × (1 + 增长余量)。');fx(55,'=IF(B54="参数有效",B13*B14*B15*(1+B19),"待填写")');
val(56,'规划活动并发',null,'路','峰值活动模型请求 × (1 + 增长余量)，向上取整。');fx(56,'=IF(B54="参数有效",ROUNDUP(B16*(1+B19),0),"待填写")');
val(57,'单副本权重内存',null,'GiB','总参数量 × 10^9 × 每参数字节 × (1 + 权重额外比例) / 2^30。');fx(57,'=IF(B54="参数有效",B25*10^9*B26*(1+B27)/2^30,"待填写")');
val(58,'单序列每 Token KV 内存',null,'Byte','标准公式：2 × 层数 × KV头数 × 头维度 × KV字节数，2 代表 K 和 V。');fx(58,'=IF(B54="参数有效",IF(B28="自定义",B33,2*B29*B30*B31*B32),"待填写")');
val(59,'单序列 KV 规划内存',null,'GiB','每 Token KV × (输入上限 + 输出上限) × 分组复制系数 / 2^30。');fx(59,'=IF(B54="参数有效",B58*(B17+B18)*B34/2^30,"待填写")');
val(60,'单副本可用设备内存',null,'GiB','物理卡数 × 每卡芯片数 × 单芯片内存 × 可用比例。分组切分有效时成立。');fx(60,'=IF(B54="参数有效",B36*B37*B38*B39,"待填写")');
val(61,'单副本留给 KV 的内存',null,'GiB','可用设备内存 − 权重内存 − 每芯片运行时内存 × 分组芯片数。');fx(61,'=IF(B54="参数有效",B60-B57-B41*B36*B37,"待填写")');
val(62,'显存允许单副本活动并发',null,'路','向下取整。依赖权重与 KV 可切分，单芯片不均衡由供应商检查。');fx(62,'=IF(B54="参数有效",MAX(0,ROUNDDOWN(B61/B59,0)),"待填写")');
val(63,'容量要求工作副本数',null,'组','规划活动并发 / 显存允许并发，向上取整。');fx(63,'=IF(B54<>"参数有效","待填写",IF(B62<1,"分组内存不足",ROUNDUP(B56/B62,0)))');
val(64,'性能要求工作副本数',null,'组','取请求速率要求与压测并发要求的较大者，按相同副本线性扩容估算。');fx(64,'=IF(B65<>"证据齐全","待有效压测",MAX(ROUNDUP(B55/B47,0),ROUNDUP(B56/B48,0)))');
val(65,'性能证据检查',null,null,'同次压测必须达到填写的服务目标，同时完成兼容性确认。');fx(65,'=IF(B54<>"参数有效","待容量参数",IF(OR(COUNT(B20:B21)<>2,MIN(B20:B21)<=0),"待填写延迟目标",IF(OR(COUNT(B47:B50)<>4,MIN(B47:B50)<=0,B48<>INT(B48),B51=""),"待填写有效压测报告",IF(OR(B49>B20,B50>B21),"压测延迟未达标",IF(B52<>"已确认","待供应商确认部署兼容性","证据齐全")))))');
val(66,'最终工作副本数',null,'组','取显存与性能需求的最大值。每个副本配置相同。');fx(66,'=IF(AND(ISNUMBER(B63),ISNUMBER(B64)),MAX(B63,B64),"待核算")');
val(67,'工作副本物理卡数',null,'张','最终工作副本数 × 每副本物理卡数。');fx(67,'=IF(ISNUMBER(B66),B66*B36,"待核算")');
val(68,'在线备用物理卡数',null,'张','备用副本数 × 每副本物理卡数。需配合故障域与路由设计。');fx(68,'=IF(ISNUMBER(B66),B42*B36,"待核算")');
val(69,'采购物理卡总数',null,'张','工作卡 + 备用卡 + 辅助服务卡。不含机箱未使用插槽。');fx(69,'=IF(ISNUMBER(B67),SUM(B67:B68)+B43,"待核算")');
val(70,'主模型计算芯片总数',null,'个','(工作卡 + 备用卡) × 每卡芯片数。辅助卡型号可能不同，不计入芯片总数。');fx(70,'=IF(ISNUMBER(B67),SUM(B67:B68)*B37,"待核算")');
val(72,'适用边界',null,null,'单一主模型，标准 MHA/GQA 或自定义 KV，单副本无权重卸载。模型多副本独立常驻；不估算训练、CPU、内存、磁盘和网络容量。');
val(73,'调压站业务补充',null,null,'站点数量不直接等于卡数。高频遥测由时序/规则服务处理，只将触发诊断或报告的负载计入模型请求；视觉/语音另核算。');
val(74,'采购验收',null,null,'用真实 RAG 文档、工具结果、多轮历史和告警突发压测；验证 P95、失败率、最忙芯片内存、备用切换和整机故障。线性副本扩容需复核共享瓶颈。');
s.getRange('B6:B8').format.fill='#E2ECF7';s.getRange('B6:B8').format.font={bold:true,size:14};s.getRange('B54:B70').format.fill='#EDF0F4';s.getRange('B54:B70').format.wrapText=true;s.getRange('B9').format.wrapText=true;
s.getRange('B28').dataValidation={rule:{type:'list',values:['标准MHA/GQA','自定义']}};s.getRange('B52').dataValidation={rule:{type:'list',values:['待确认','已确认']}};
for(const r of [19,27,39])s.getRange(`B${r}`).setNumberFormat('0.0%');
for(const r of [13,15,25,26,32,38,41,47,49,50,55,57,59,60,61])s.getRange(`B${r}`).setNumberFormat('0.00');
for(const r of [54,65,9])s.getRange(`B${r}`).conditionalFormats.add('containsText',{text:'待',format:{fill:'#FCE2D9',font:{color:'#9C331F'}}});
s.freezePanes.freezeRows(3);
h.getRange('A2').values=[['硬件规格与核算依据']];h.getRange('A2').format.font={bold:true,size:16};
const sources=[
['参考项','官方标称 / 方法','核对日期','来源与使用说明'],
['Atlas 300I Duo','整卡 48GB / 96GB；双芯片','2026-10-09','https://e.huawei.com/cn/products/computing/ascend/atlas-300i-duo?trk=article-ssr-frontend-pulse_little-text-block'],
['Duo 的单芯片口径','96GB 型号不是单芯片 96GB','2026-10-09','https://www.hiascend.com/developer/techArticles/20251212-1 ；官方文章明确单卡双芯片，43GB 为单芯片可用示例。实际可用值按目标硬件测量。'],
['Atlas 300I A2','官方文章列 64G 型号','2026-10-09','https://www.hiascend.com/developer/techArticles/20251212-1 ；仅作 SKU 核对入口，不推定不同版本相同。'],
['Atlas 350','官网列 112GB HBM','2026-10-09','https://www.hiascend.com/hardware/accelerator-card ；需单独核对所采购 SKU、内存单位、计算设备枚举和模型支持。'],
['内存单位','1 GiB = 2^30 Byte','定义','厂商若用十进制 GB：GiB = GB × 10^9 / 2^30；厂商若按二进制标称，则按其说明录入。不能自动把 GB 视作 GiB。'],
['资源核算参考','区分计算量、权重及其他内存','2026-10-09','https://datawhalechina.github.io/diy-llm/chapter3/chapter3_pytorch%E4%B8%8E%E8%B5%84%E6%BA%90%E6%A0%B8%E7%AE%97.html ；此章主要讲训练核算，不直接套用训练 6P 或优化器内存到推理。'],
['标准 KV 存储布局','K/V 按块、头数、头维度存储','CANN 9.1.0 / 2026-10-09','https://www.hiascend.com/doc_center/source/zh/CANNCommunityEdition/910/acce/ascendtb/ascendtb_01_0241.html ；本表据标准 K/V 张量元素数量推导内存。'],
['性能核算方法','使用达标副本 QPS 与活动并发','本表工程规划方法','不把理论 TFLOPS 换算成稳定 Token/s。单副本吞吐测量须固定模型、精度、卡型、分组、上下文、调度和 P95 服务目标。'],
['规划假设','20% 增长、10% 权重、85% 可用','可修改，未实测','备用副本默认 1、辅助卡默认 0、KV 复制默认 1、FP16 权重与 KV 默认 2 Byte。默认值须由研发确认；没有任何客户性能实测。'],
['多个业务与辅助模型','主模型调用分别汇总','填写指引','客户可分别统计告警诊断、知识问答、报告生成等峰值；仅将共享主模型的调用累加。Embedding/Reranker/视觉/语音的独立用卡填入辅助卡。'],
['硬件销售核对','卡与模组不可混用采购口径','填写指引','Atlas 800I 等整机常使用集成模组。若采购整机，按报价 BOM 明确设备数、模组数与整机台数；不要把模组数称作可单独购买的 PCIe 卡数。']
];
h.getRange('A4:D15').values=sources;h.getRange('A4:D4').format.fill='#263F60';h.getRange('A4:D4').format.font={bold:true,color:'#FFFFFF'};h.getRange('A5:D15').format.wrapText=true;h.getRange('A5:D15').format.rowHeight=66;h.getRange('B5:B15').format.fill='#F1F4F8';h.freezePanes.freezeRows(4);
h.getRange('A18').values=[['粗估默认值（本表预算假设，未实测）']];
h.getRange('A19:D23').values=[['模型参数档位','总参数量（B）','KV预算（KiB/Token）','说明'],['7B',7,128,'通用结构预算，不绑定某个实际模型'],['14B',14,160,'默认档位，不代表模型选型结论'],['32B',32,320,'参数与KV档位同时随选择变化'],['70B',70,512,'不适用于总参数大于此档位的MoE或特殊缓存结构']];
h.getRange('A25:D31').values=[['共同内存假设','值','单位','说明'],['权重字节数',2,'Byte/参数','按FP16/BF16，不要求客户了解量化'],['权重额外占用',0.1,'比例','覆盖未单列的权重开销'],['设备内存可用比例',0.85,'比例','设备余量，与运行时工作区分别计入'],['每芯片运行时预算',6,'GiB','简化占位预算，未实测'],['KV额外系数',1.2,'倍','缓存块、复制等额外占用的简化余量'],['默认能力假设','4路 / 10次模型调用每分钟','每副本','人为预算假设，不是华为保证的性能；使用者可在粗估页修改']];
for(const row of [19,25]){h.getRange(`A${row}:D${row}`).format.fill='#263F60';h.getRange(`A${row}:D${row}`).format.font={bold:true,color:'#FFFFFF'};}
h.getRange('A19:D31').format.wrapText=true;h.getRange('A19:D31').format.rowHeight=42;h.getRange('A31:D31').format.rowHeight=60;h.getRange('B27:B28').setNumberFormat('0%');
const rv=(row,a,b,c,d)=>rough.getRange(`A${row}:D${row}`).values=[[a,b,c,d]];
const rf=(row,f)=>rough.getRange(`B${row}`).formulas=[[f]];
const rb=(row,a)=>{rv(row,a,null,null,null);rough.getRange(`A${row}:D${row}`).format.fill='#263F60';rough.getRange(`A${row}:D${row}`).format.font={bold:true,color:'#FFFFFF'};};
const ri=(row,a,b,c,d,customer=false)=>{rv(row,a,b,c,d);rough.getRange(`B${row}`).format.fill=customer?'#FFF0BF':'#EAF1F8';rough.getRange(`B${row}`).format.font.color='#174B91';};
rv(2,'调压站智能体计算卡粗估',null,null,'版本2.0。所有输入已预填，改两项业务规模即可。适用于初步预算。');rough.getRange('A2').format.font={size:16,bold:true};
rv(3,'黄色填业务，蓝色可用默认',null,null,'默认规模只是示例。无须模型结构参数或压测报告，结果使用下方可修改的能力假设。');
rb(5,'自动估算结果');
rv(6,'初步预算计算卡数',null,'张','含主模型工作卡、默认1组在线备用及单列辅助卡。按假设估算，不代表实测能力。');rf(6,'=IF(B31="参数有效",B41,"请填写有效数值")');
rv(7,'主模型工作卡数',null,'张','工作副本数 × 每副本卡数，不含备用。');rf(7,'=IF(B31="参数有效",B40*B37,"待填写")');
rv(8,'每个模型副本使用卡数',null,'张','按内存预算自动估算为1、2、4、8等卡分组，实际并行支持仍须选型时确认。');rf(8,'=IF(B31="参数有效",B37,"待填写")');
rv(9,'服务器装箱规划',null,'台','主模型按完整副本装箱，辅助卡另配服务器。若要求整机容灾，另做故障域规划。');rf(9,'=IF(B31="参数有效",B42,"待填写")');
rv(10,'估算口径',null,null,'4路并发、每分钟10次模型调用是可修改的预算占位假设，未经过华为硬件实测。');rf(10,'=IF(B31="参数有效","初步预算估算，默认能力未实测",B31)');rough.getRange('B10').format.wrapText=true;
rb(12,'客户优先调整这两项，其余可先用默认值');
ri(13,'项目名称','调压站智能体','文本','可修改，不参与计算。');
ri(14,'高峰同时处理的任务数',10,'个','业务任务并发。默认同一任务内模型调用依次执行；若有并行分支，请按同时调用数折算。',true);
ri(15,'高峰每分钟业务请求数',2,'次/分钟','告警诊断、问答、报告等总请求。未知时可先保留2，结果只代表该示例规模。',true);
rb(17,'默认配置（不熟悉时可以保留，知道实际情况再改）');
ri(18,'模型参数档位','14B','选项','7B、14B、32B、70B，默认14B是预算场景。具体模型与质量另行选型。');
ri(19,'单次调用总上下文长度',5120,'Token','默认输入4096 + 输出1024，含历史、规程材料与工具返回。');
ri(20,'每个业务的模型调用次数',3,'次','默认依次进行分析、工具后再分析、回答等3次调用；重试如需计入也加到这里。');
ri(21,'每副本规划活动并发',4,'路','预算假设，未实测；不会因卡数增加而自动提高。');
ri(22,'每副本规划模型调用吞吐',10,'次/分钟','预算假设，未实测；与上项一起约束副本数，知道供应商能力时直接替换。');
ri(23,'每张物理卡总内存',64,'GB','默认64GB级单芯片卡预算场景。按十进制GB换算，双芯片卡需同时修改下一项。');
ri(24,'每张物理卡芯片数',1,'个','默认1；Duo为2，填的是整卡总内存，不把双芯片当成连续内存。');
ri(25,'业务增长余量',0.2,'比例','默认20%，同时增加并发与请求量。');
ri(26,'在线备用模型副本',1,'组','默认1。不要求备用可改0，备用不自动保证整机容灾。');
ri(27,'辅助服务额外计算卡',0,'张','默认Embedding/Reranker走CPU或不另占卡。独立视觉、语音等用卡在此追加。');
ri(28,'每台服务器允许装卡数',8,'张','仅用于服务器数量估算，最终按机箱、互联和整机BOM确认。');
rb(30,'自动计算过程（无须填写）');
rv(31,'输入检查',null,null,'核心数值无效时不输出预算数量。业务规模允许0，模型服务仍至少常驻1组。');
const roughNums=[14,15,19,20,21,22,23,24,25,26,27,28];
const roughInts=[14,19,21,24,26,27,28];
rf(31,`=IF(OR(${roughNums.map(i=>`NOT(ISNUMBER(B${i}))`).join(',')}),"请填写有效数值",IF(OR(B14<0,B15<0,MIN(B19:B24)<=0,B25<0,B26<0,B27<0,B28<1,${roughInts.map(i=>`B${i}<>INT(B${i})`).join(',')},B23*10^9/2^30*'硬件与依据'!B28-'硬件与依据'!B29*B24<=0),"请修正数值范围",IF(OR(B18="7B",B18="14B",B18="32B",B18="70B"),"参数有效","请选择有效模型档位")))`);
rv(32,'模型总参数量',null,'B','跟随模型档位，不要求填写层数、头数。');rf(32,'=IF(B31="参数有效",INDEX(\'硬件与依据\'!B20:B23,MATCH(B18,\'硬件与依据\'!A20:A23,0)),"待填写")');
rv(33,'每Token KV粗估预算',null,'KiB','通用档位假设，可在“硬件与依据”修改。不是具体模型的配置参数。');rf(33,'=IF(B31="参数有效",INDEX(\'硬件与依据\'!C20:C23,MATCH(B18,\'硬件与依据\'!A20:A23,0)),"待填写")');
rv(34,'单副本权重内存',null,'GiB','参数 × 2字节 × 1.1，按FP16/BF16预留10%开销。');rf(34,'=IF(B31="参数有效",B32*10^9*\'硬件与依据\'!B26*(1+\'硬件与依据\'!B27)/2^30,"待填写")');
rv(35,'单序列KV缓存',null,'GiB','每Token预算 × 上下文长度，再预留20%缓存开销。');rf(35,'=IF(B31="参数有效",B33*1024*B19*\'硬件与依据\'!B30/2^30,"待填写")');
rv(36,'每卡扣除运行时后的内存',null,'GiB','整卡GB转换GiB × 85% − 每芯片6GiB运行时预算。');rf(36,'=IF(B31="参数有效",B23*10^9/2^30*\'硬件与依据\'!B28-\'硬件与依据\'!B29*B24,"待填写")');
rv(37,'每副本分组卡数',null,'张','权重 + 规划并发KV，除以每卡内存，向上取1、2、4、8等；预算上假设可切分。');rf(37,'=IF(B31="参数有效",2^ROUNDUP(LOG(MAX(1,(B34+B35*B21)/B36),2),0),"待填写")');
rv(38,'规划活动并发',null,'路','高峰任务数 × 1.2，向上取整，默认无任务内并行。');rf(38,'=IF(B31="参数有效",ROUNDUP(B14*(1+B25),0),"待填写")');
rv(39,'规划模型调用量',null,'次/分钟','高峰业务请求数 × 每业务调用次数 × (1 + 增长余量)。');rf(39,'=IF(B31="参数有效",B15*B20*(1+B25),"待填写")');
rv(40,'工作副本数',null,'组','取并发约束与调用量约束中较大值，至少保留1组常驻服务。');rf(40,'=IF(B31="参数有效",MAX(1,ROUNDUP(B38/B21,0),ROUNDUP(B39/B22,0)),"待填写")');
rv(41,'预算物理卡总数',null,'张','(工作副本 + 在线备用) × 每副本卡数 + 辅助卡。');rf(41,'=IF(B31="参数有效",(B40+B26)*B37+B27,"待填写")');
rv(42,'服务器数量估算',null,'台','副本须在单台内，主模型与辅助卡分开装箱；容灾隔离可增加台数。');rf(42,'=IF(B31<>"参数有效","待填写",IF(B37>B28,"需更大机箱或跨机方案",ROUNDUP((B40+B26)/ROUNDDOWN(B28/B37,0),0)+ROUNDUP(B27/B28,0)))');
rv(44,'估算边界',null,null,'用于前期预算，不要求压测。70B以上总参数、特殊KV、多模态主模型、跨机并行应单独核算；详细核算页可选用。');
rough.getRange('B6:B9').format.fill='#E2ECF7';rough.getRange('B6:B9').format.font={bold:true,size:14};rough.getRange('B31:B42').format.fill='#EDF0F4';rough.getRange('B31:B42').format.wrapText=true;rough.getRange('A44:D44').format.rowHeight=54;
rough.getRange('B25').setNumberFormat('0%');for(const i of [34,35,36,39])rough.getRange(`B${i}`).setNumberFormat('0.0');
rough.getRange('B18').dataValidation={rule:{type:'list',values:['7B','14B','32B','70B']}};
for(const i of roughNums)rough.getRange(`B${i}`).dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1000000}};
rough.freezePanes.freezeRows(3);
for(const r of [72,73,74])s.getRange(`A${r}:D${r}`).format.rowHeight=52;
// Type guards run before integer arithmetic, including pasted text that bypasses Excel validation.
const numeric=[...req,19,27,41,42,43];
const original54=s.getRange('B54').formulas[0][0].slice(1).replace('B34<1,','B34<1,B36>B40,');
fx(54,`=IF(OR(${numeric.map(r=>`NOT(ISNUMBER(B${r}))`).join(',')}),"请补齐或修正黄色容量参数",IF(AND(B28="标准MHA/GQA",COUNT(B29:B32)<>4),"请补齐或修正KV结构参数",${original54}))`);
const original65=s.getRange('B65').formulas[0][0].slice(1);
fx(65,`=IF(B54<>"参数有效","待容量参数",IF(OR(B24="",B44=""),"待填写模型版本与硬件配置",IF(COUNT(B47:B50)<>4,"待填写有效压测报告",${original65})))`);
for(const r of numeric)s.getRange(`B${r}`).dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1000000000000}};
// Disposable in-memory input checks. All temporary example values are restored before delivery.
const sample={13:1,14:3,16:8,17:2048,18:1024,24:'7B 合成算例，非实际型号',25:7,29:32,30:8,31:128,36:1,37:1,38:64,40:8,41:4,44:'合成硬件与部署配置，非采购 SKU',20:2,21:30,47:2,48:8,49:1,50:20,51:'合成测试数据，不是客户压测',52:'已确认'};
const old=new Map();for(const [r,v]of Object.entries(sample)){old.set(r,s.getRange(`B${r}`).values[0][0]);s.getRange(`B${r}`).values=[[v]];}
const tests=[];function check(name,row,expected){const actual=s.getRange(`B${row}`).values[0][0];if(actual!==expected)throw Error(`${name}: ${actual} != ${expected}`);tests.push({name,actual});}
w.recalculate();check('capacity valid',54,'参数有效');check('planned concurrency',56,10);check('performance replicas',64,2);check('procurement cards',7,3);
s.getRange('B24').values=[[null]];w.recalculate();check('missing model identity blocks procurement',7,'待补齐参数与压测');s.getRange('B24').values=[[sample[24]]];
s.getRange('B36').values=[[3]];s.getRange('B40').values=[[4]];s.getRange('B42').values=[[2]];w.recalculate();check('whole replica packing',8,4);s.getRange('B43').values=[[1]];w.recalculate();check('auxiliary server separation',8,5);s.getRange('B43').values=[[0]];s.getRange('B36').values=[[5]];w.recalculate();check('cross server replica blocked',54,'请补齐或修正黄色容量参数');s.getRange('B36').values=[[1]];s.getRange('B40').values=[[8]];s.getRange('B42').values=[[1]];
s.getRange('B36').values=[['误填文本']];w.recalculate();check('text input blocks without formula error',54,'请补齐或修正黄色容量参数');s.getRange('B36').values=[[1]];
s.getRange('B48').values=[['误填文本']];w.recalculate();check('text benchmark blocks without formula error',65,'待填写有效压测报告');s.getRange('B48').values=[[8]];
s.getRange('B49').values=[[3]];w.recalculate();check('failed latency blocks procurement',7,'待补齐参数与压测');s.getRange('B49').values=[[1]];
s.getRange('B52').values=[['待确认']];w.recalculate();check('compatibility blocks procurement',7,'待补齐参数与压测');s.getRange('B52').values=[['已确认']];
s.getRange('B38').values=[[1]];w.recalculate();check('insufficient group memory',62,0);check('insufficient group blocks procurement',7,'待补齐参数与压测');s.getRange('B38').values=[[64]];
s.getRange('B28').values=[['自定义']];s.getRange('B33').values=[[131072]];s.getRange('B29').values=[[null]];w.recalculate();check('custom KV supports missing standard fields',54,'参数有效');s.getRange('B28').values=[['标准MHA/GQA']];s.getRange('B33').values=[[null]];
for(const[r,v]of old)s.getRange(`B${r}`).values=[[v??null]];
w.recalculate();check('blank customer fields block procurement',7,'待补齐参数与压测');
const roughDefaults=new Map(roughNums.concat(18).map(i=>[i,rough.getRange(`B${i}`).values[0][0]]));
function roughCheck(name,row,expected){const actual=rough.getRange(`B${row}`).values[0][0];if(actual!==expected)throw Error(`${name}: ${actual} != ${expected}`);tests.push({name,actual});}
roughCheck('rough default budget without benchmark',6,4);roughCheck('rough default per replica cards',8,1);
rough.getRange('B18').values=[['70B']];w.recalculate();roughCheck('rough 70B automatic four card group',8,4);roughCheck('rough 70B budget cards',6,16);rough.getRange('B18').values=[['14B']];
rough.getRange('B15').values=[[100]];w.recalculate();roughCheck('rough peak rate drives budget',6,37);rough.getRange('B15').values=[[2]];
rough.getRange('B14').values=[[100]];w.recalculate();roughCheck('rough concurrency drives budget',6,31);rough.getRange('B14').values=[[10]];
rough.getRange('B26').values=[[0]];w.recalculate();roughCheck('rough zero spare preserved',6,3);rough.getRange('B26').values=[[1]];
rough.getRange('B14').values=[[null]];w.recalculate();roughCheck('rough missing demand invalidates budget',6,'请填写有效数值');rough.getRange('B14').values=[[10]];
rough.getRange('B22').values=[['文字']];w.recalculate();roughCheck('rough text capability invalidates budget',6,'请填写有效数值');
for(const[i,v]of roughDefaults)rough.getRange(`B${i}`).values=[[v]];
w.recalculate();roughCheck('rough defaults restored',6,4);
await fs.writeFile(dir+'verification.json',JSON.stringify(tests,null,2));
console.log((await w.inspect({kind:'table',range:'粗略估算!A6:C10',include:'values,formulas',tableMaxRows:5,tableMaxCols:3})).ndjson);
console.log((await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20}})).ndjson);
for(const [sheetName,range,name]of [['粗略估算','A1:D28','preview-main'],['粗略估算','A30:D44','preview-rough-calculation'],['填写与核算','A1:D21','preview-detailed'],['填写与核算','A23:D52','preview-inputs'],['填写与核算','A53:D74','preview-calculation'],['硬件与依据','A1:D15','preview-sources'],['硬件与依据','A18:D31','preview-defaults']]){const p=await w.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(dir+name+'.png',new Uint8Array(await p.arrayBuffer()));}
const out=await SpreadsheetFile.exportXlsx(w);await out.save(dir+'调压站智能体-华为计算卡自动核算.xlsx');
console.log('Exported workbook and completed '+tests.length+' checks');
