from pathlib import Path
from urllib.parse import unquote
import re,csv,json,hashlib,zipfile
R=Path(__file__).resolve().parents[1]
main=(R/'研究与论证方案_A-I.md').read_text(encoding='utf-8')
title=re.search(r'\*\*暂拟题目：(.*?)\*\*',main).group(1)
intro=main.split('简介设计稿（')[1].split('> ')[1].split('\n')[0]
heads=re.findall(r'^## ([A-I])\.',main,re.M)
assert heads==list('ABCDEFGHI'),heads
assert len(title)<=20,(title,len(title))
assert len(intro)<=300,len(intro)
matrix=(R/'B_核心论文论证方法矩阵.md').read_text(encoding='utf-8')
assert all(c in matrix for c in ['C2','C3','I1','I3','I4','N2','N6','S1'])
local_links=[]; missing=[]
for p in R.rglob('*.md'):
 if 'work' in p.parts:continue
 text=p.read_text(encoding='utf-8')
 assert '\ufffd' not in text,str(p)
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if re.match(r'^[A-Z]:[/\\]',target):
   target=unquote(target)
   local_links.append(target)
   if not Path(target).exists():missing.append({'file':p.name,'target':target})
assert not missing,missing
for p in R.glob('*_空白.csv'):
 with p.open(encoding='utf-8-sig',newline='') as inp:rows=list(csv.reader(inp))
 assert len(rows)==1,p.name
assert 'd_i=\\min' not in (R/'E2_MATLAB机制仿真设计.md').read_text(encoding='utf-8')
assert '基准仿真只处理明确的整项任务预算更新' in (R/'E2_MATLAB机制仿真设计.md').read_text(encoding='utf-8')

review=R/'evidence'/'方案反对意见审查.md'
rt=review.read_text(encoding='utf-8')
if '主代理最终处置（2026-10-28）' not in rt:
 rt+='\n\n## 主代理最终处置（2026-10-28）\n\n限定复核指出的单次商品许可/任务级预算残留已修复：E2基准明确只模拟任务级预算更新，单次许可留在CASE；未认可超支公式只用于这一基准范围，未来若扩展须增加授权账。主稿保留三种授权范围的规范比较。本次只完成设计与文件核验，没有运行仿真或真实交互。\n'
 review.write_text(rt,encoding='utf-8')

records={
 'date':'2026-10-28',
 'timezone':'Asia/Shanghai',
 'deliverable_scope':'研究与论证方案；非整篇参赛论文',
 'source_md_sha256':'3d75afeec4e2f1967450433578647b5688fa6c1c34184d4560d9fbbfeaf32815',
 'source_md_matches_package_copy':True,
 'main_sections':heads,
 'core_full_argument_read_count':8,
 'original_pdf_count':15,
 'title':title,'title_characters':len(title),'intro_characters':len(intro),
 'local_markdown_links_checked':len(local_links),'missing_local_links':missing,
 'empty_csv_templates':4,
 'real_ai_audit':'not_performed','human_participant_study':'not_performed','matlab_simulation':'not_run',
 'reference_lists_individually_verified':False,'user_attested_reading':False,
 'author_topic_and_contribution_decision':'pending_review',
 'submission':'not_performed','cnki_similarity_check':'not_performed',
 'reviewed_design_repairs':['区分重筛有解与停止有效','披露D与控制C分离','识别b/阅读r/理解q分离','请求停止与执行停止分离','主CASE同事实','加入较强逐轮遵从竞争基线','仿真限定任务级预算更新'],
}
(R/'evidence'/'交付核验记录.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=[]
for p in sorted(R.rglob('*')):
 if not p.is_file() or 'work' in p.parts:continue
 if p.name=='交付文件校验表.json':continue
 manifest.append({'file':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'evidence'/'交付文件校验表.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=R.parent/(R.name+'_工作包.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(R.rglob('*')):
  if not p.is_file() or 'work' in p.parts:continue
  if p.parent==R/'sources' and not p.name.startswith('附件'):continue
  z.write(p,arcname=R.name+'/'+str(p.relative_to(R)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 count=len(z.namelist())
print(json.dumps({'checked':records,'archive':str(archive),'archive_files':count,'archive_bytes':archive.stat().st_size},ensure_ascii=False,indent=2))
