# 字幕与画面联合分析

先取得字幕证据，再让视觉分析读取同一时间范围的字幕。脚本只用Python标准库，不要求安装requests；与.NET视频下载脚本独立。

## 采集与导入

从本skill目录执行（完整URL里的`p`选择分P）：

```powershell
python scripts/collect_subtitles.py "https://www.bilibili.com/video/BV15z4C6SEHT/?p=4" -o ./output/subtitle-evidence --language ai-zh
```

依次尝试player/v2与player/wbi/v2，每个请求超时15秒，不保证接口一直可用。`--language`为精确轨道代码，例如`zh-CN`或`ai-zh`，不静默换语言。`--cid`可检查预期CID。需要登录时可用用户已授权的本地`--cookie-file`，不把Cookie内容写进命令、日志或报告。

已有字幕可离线导入：

```powershell
python scripts/collect_subtitles.py "https://www.bilibili.com/video/BV15z4C6SEHT/?p=4" -o ./output/subtitle-evidence --input ./cached-p4.json --source cache --cid 41394373935
```

接受B站`body`、普通字幕列表（from/to/content）、segments（start/end/text）或SRT。导入ASR产物时指定`--source asr`，人工整理字幕用`--source manual`。旧缓存没有来源元数据时，其视频身份是调用者声明，报告`identity_verified=false`；先检查它与分P、时长和画面内容一致。不能把这类缓存说成刚获取的平台字幕。

输出：`subtitle-raw.json`保留导入或下载内容；`subtitles.json`包含来源与逐句时间；`subtitles.srt`；按分钟组织的`sectioned.md`；`subtitle-report.json`记录状态、来源、身份、缺口；`evidence-index.json`用于关联帧与字幕。

拿不到字幕时脚本返回2，报告为missing，不伪造字幕或把OCR当音轨转录。平台登录不可用时优先已有字幕；没有缓存则根据当前可用ASR工具转录选定分P的音轨，保留时间轴后用`--source asr`导入。未配置ASR时明确保留字幕缺口，不自动安装模型或购买API。

## 时间对齐

可用`--frame-map frame-map.json`传入`[{"file":"images/frame_0097.jpg","time":96,"precision":"approximate"}]`，输出对应字幕ID。准确采集应使用原始PTS；旧素材估计时间必须标approximate。字幕不覆盖该时刻时返回空列表，不强行匹配。

现有prepare.cs去重后重新编号，**不能据新帧号推算时间**。联合分析默认用`--no-dedup`保留连续采样，或先保存原帧时间清单再去重；目录的旧帧不能与新一次抽帧混用。若缺时间记录，重新按时间截取代表画面，或只保留内容证据并注明不能精确对齐。

## 交给分析助手的证据

每个主题记录：结论、字幕ID及原文时间、支持的帧与时间精度、冲突／待复核、外部补充。例如：`S0031 [01:04–01:07] + frame_0075（约01:14）`。字幕窗口可以提供前后几句，避免割裂上下文；相近时间本身不证明字幕与画面讲的是同一个事实。

- 保留视觉分析发现的公式、代码、GELU标签与图示变化。字幕补充口头解释，不能覆盖画面事实。
- 字幕错字保留在原始文件；纠正另记原文、修订、依据。字幕与画面冲突时核对原画面／音轨，未确认就标待复核。
- 按章节组织分析输入，引用可回溯的字幕与图片；分析阶段不要求卡片、自测题或固定篇幅。
- 用户指定独立写作skill时，交付分析证据包，由该skill写作，不额外套用本skill的文章模板或工作目录课程规范。
