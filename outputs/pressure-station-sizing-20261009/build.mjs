import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=new URL('.',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1');
const w=Workbook.create(), s=w.worksheets.add('填写与核算'), h=w.worksheets.add('硬件与依据');
for(const sh of [s,h]){sh.showGridLines=false;sh.getRange('A1:D85').format.font={name:'Arial',size:11,color:'#243247'};sh.getRange('A1:D85').format.rowHeight=32;sh.getRange('A1:D85').format.verticalAlignment='center';sh.getRange('A1:A85').format.columnWidth=40;sh.getRange('B1:B85').format.columnWidth=29;sh.getRange('C1:C85').format.columnWidth=13;sh.getRange('D1:D85').format.columnWidth=86;sh.getRange('D1:D85').format.wrapText=true;}
const val=(r,a,b,c,d)=>s.getRange(`A${r}:D${r}`).values=[[a,b,c,d]];
const fx=(r,f)=>s.getRange(`B${r}`).formulas=[[f]];
const band=(r,text)=>{val(r,text,null,null,null);s.getRange(`A${r}:D${r}`).format.fill='#263F60';s.getRange(`A${r}:D${r}`).format.font={bold:true,color:'#FFFFFF'};};
const input=(r,a,b,c,d)=>{val(r,a,b,c,d);s.getRange(`B${r}`).format.fill='#FFF0BF';s.getRange(`B${r}`).format.font.color='#174B91';};
val(2,'调压站智能体计算卡核算',null,null,'核对日期：2026-10-09。适用于本地大模型推理，不含训练资源。');s.getRange('A2').format.font={size:16,bold:true};
val(3,'填写黄色单元格',null,null,'客户填业务需求，研发填模型与部署参数，供应商填同配置压测数据。空白业务参数没有预设客户数据。');
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
await fs.writeFile(dir+'verification.json',JSON.stringify(tests,null,2));
console.log((await w.inspect({kind:'table',range:'填写与核算!A6:C9',include:'values,formulas',tableMaxRows:4,tableMaxCols:3})).ndjson);
console.log((await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20}})).ndjson);
for(const [sheetName,range,name]of [['填写与核算','A1:D21','preview-main'],['填写与核算','A23:D52','preview-inputs'],['填写与核算','A53:D74','preview-calculation'],['硬件与依据','A1:D15','preview-sources']]){const p=await w.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(dir+name+'.png',new Uint8Array(await p.arrayBuffer()));}
const out=await SpreadsheetFile.exportXlsx(w);await out.save(dir+'调压站智能体-华为计算卡自动核算.xlsx');
console.log('Exported workbook and completed '+tests.length+' checks');
