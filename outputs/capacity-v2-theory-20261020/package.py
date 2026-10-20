"""Build and verify a self-contained customer evidence package."""
from pathlib import Path
import json,hashlib,shutil,zipfile,re
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'delivery'
DEST.mkdir(exist_ok=True)
files=['report.client.md','report.evidence.md','sizing-flow.png','sizing-flow.svg','request.json','assumptions.json','model-input.json','config.json','report.json','verification.json','calculate.py','render.py','draw_flow.py','render_flow_png.ps1','test_calculate.py']
for name in files:shutil.copyfile(ROOT/name,DEST/name)
for name in ['sources','tools']:
 shutil.copytree(ROOT/name,DEST/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(DEST/'README.md').write_text("""# 客户测算交付包

入口：[测算报告](report.client.md)；[测算依据](report.evidence.md)。图片和必要依据在本目录内，可整体复制或解压后阅读，无需原仓库及Skill。

报告针对2026-10-20确认的DeepSeek-V4.1-Flash、8K/1K平均长度、60路突发条件，固定Prefill8张＋Decode8张布局。16张是明确假设下的预算候选，并非全局最少卡数或实测达标结论。

`sources/`包含必要的固定模型/推理实现快照及清单、结构分组摘要和硬件说明；`.source.txt`是原始Markdown文档的内容快照，原文的延伸链接未全部打包。完整权重和实测性能数据未包含。

可选复算：Python 3运行`calculate.py`，再运行`render.py`。数值计算只用标准库和本地`tools/`，不联网。重新生成PNG还需Windows、PowerShell 7和System.Drawing；不重绘时可直接使用随包图片。文件摘要见`package-manifest.json`，原始来源修订及SHA见sources清单。
""",encoding='utf-8')
def verify(folder):
 for f in folder.glob('*.md'):
  for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
   if ':' in link or link.startswith('#'):continue
   target=(f.parent/link.split('#')[0]).resolve()
   assert target.is_relative_to(folder.resolve()),(f,link,'outside package')
   assert target.exists(),(f,link,'missing')
verify(DEST)
manifest={str(f.relative_to(DEST)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(DEST.rglob('*')) if f.is_file() and f.name!='package-manifest.json'}
(DEST/'package-manifest.json').write_text(json.dumps({'files':manifest,'localLinksContained':True,'source':'selected fixed theoretical evidence, no measured performance data'},ensure_ascii=False,indent=2),encoding='utf-8')
archive=ROOT/'customer-delivery.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in DEST.rglob('*'):
  if f.is_file():z.write(f,Path('customer-delivery')/f.relative_to(DEST))
# Extract into a separate persistent audit folder to validate portability; do not delete user data.
audit=ROOT/'delivery-audit'
with zipfile.ZipFile(archive) as z:z.extractall(audit)
verify(audit/'customer-delivery')
for rel,digest in manifest.items():assert hashlib.sha256((audit/'customer-delivery'/rel).read_bytes()).hexdigest()==digest
print(json.dumps({'archive':str(archive),'fileCount':len(manifest)+1,'portableLinksChecked':True,'archiveBytes':archive.stat().st_size}))
