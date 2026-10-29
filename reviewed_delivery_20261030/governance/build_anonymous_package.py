"""Build the anonymous materials ZIP from a declared allowlist.

Run from any directory: python governance/build_anonymous_package.py
Uses the standard library. Original research inputs are read only. Four clearly
labelled navigation pages are generated inside the ZIP, not over source files.
"""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission'
TITLE='AI导购理由撤回后的预算重审'

def main():
    selected={}
    for name in [TITLE+'_参赛修复稿.docx',TITLE+'_参赛修复稿.pdf',TITLE+'_答辩稿.pptx','作品简介.txt','答辩讲稿与来源.md','复现与构建说明.md','三四项技能复审记录.md','ppt_reproduction.json']:
        selected['submission/'+name]=(OUT/name).read_bytes()
    for name in ['budget_guard.py','check_protocol.py','protocol_results.json','check_boundaries.py','boundary_results.json','rules.json','build_submission_report.py','build_defense.mjs','scrub_pptx_core.py','build_anonymous_package.py','伦理审计清单.md','README.md']:
        selected['governance/'+name]=(ROOT/'governance'/name).read_bytes()
    domestic=ROOT/'research/domestic_data_reanalysis_20261029'
    for p in domestic.rglob('*'):
        if p.is_file() and p.suffix!='.pdf' and '__pycache__' not in p.parts:
            selected[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    base=ROOT/'research/user_reinforced_domestic_revision_20261029'/(TITLE+'_补强稿国内数据版.docx')
    selected[base.relative_to(ROOT).as_posix()]=base.read_bytes()
    for name in ['元宝桌面版预试_执行前协议.md','元宝桌面版预试_匿名会话.json','元宝桌面版预试_匿名文字摘录.md']:
        p=ROOT/'research/evidence'/name
        selected[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    # Navigation stubs are labelled derivatives; never impersonate original files.
    stubs={
      'research/evidence/元宝桌面版预试_完整对话.md':
        '# 匿名包导航：完整预试记录\n\n本页是匿名包的导航说明，不是原同名文件的副本。完整匿名提示与回复见[匿名会话JSON](元宝桌面版预试_匿名会话.json)，可读文字见[匿名摘录](元宝桌面版预试_匿名文字摘录.md)。提示前史为构造输入，回复为限定系统的实际输出。\n',
      'research/元宝桌面版预试_结果与论证修订.md':
        '# 匿名包导航：限定预试及使用范围\n\n本页是匿名包导航说明，原阶段修订备忘未收入本包。实际响应见[匿名摘录](evidence/元宝桌面版预试_匿名文字摘录.md)及[完整匿名JSON](evidence/元宝桌面版预试_匿名会话.json)。当前分析见[完整报告](../submission/'+TITLE+'_参赛修复稿.pdf)。给定前史、每条件一次的限定响应不估计总体发生率。\n',
      'research/domestic_simulation_report_20261029/README.md':
        '# 匿名包导航：原独立统计报告\n\n本页是导航说明，不是原独立报告README的副本。独立六页报告保留于公开研究仓库，本匿名包以[完整现稿](../../submission/'+TITLE+'_参赛修复稿.pdf)承载相同统计结果；[原数据与代码](../domestic_data_reanalysis_20261029/README.md)在本包内提供。\n',
      'research/phase6_domestic_report_20261029/README.md':
        '# 匿名包导航：历史全文前稿\n\n本页是导航说明。该历史全文前稿未收入本匿名包，当前使用[参赛修复稿](../../submission/'+TITLE+'_参赛修复稿.pdf)。原研究代码和数据保留原字节；历史版本不作为新增独立证据。\n',
    }
    for name,text in stubs.items():selected[name]=text.encode('utf-8')
    selected['README.md']=('''# 匿名研究材料与复现入口

完整报告、答辩与来源见submission；详细命令见[复现说明](submission/复现与构建说明.md)。原规范案例、限定系统预试、国内二手数据与本轮工程检查分别登记。

python governance/check_protocol.py重现原16项工程断言；python governance/check_boundaries.py运行独立的边界回归检查。输入为构造协议记录，不代表消费者心理或方案效果。原数据、MATLAB代码及作者许可在research/domestic_data_reanalysis_20261029；复跑另存输出。

本包保留正常学术作者及作者数据仓库出处，剔除参赛者账号入口与私人会话定位。第三方论文全文按来源链接取得。原始研究文件不改；为避免匿名子集中的导航断链，四个缺省历史链接位置放入明确标注的导航页，清单见package_scope.json。

SHA256SUMS.json列出除自身外所有文件。已交付PDF21页、PPT16页。查重和百度分享依用户要求不在本轮办理；正式赛事上传未执行。材料检查为AI自审，完整保护检查在公开仓库执行。
''').encode('utf-8')
    selected['package_scope.json']=json.dumps({'date':'2026-10-30','scope':'anonymous subset of current materials','navigation_stubs':list(stubs),'original_research_source_files_modified':False,'third_party_paper_fulltexts_included':False,'new_consumer_observations':False},ensure_ascii=False,indent=2).encode('utf-8')
    selected['SHA256SUMS.json']=json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in sorted(selected.items())},ensure_ascii=False,indent=2).encode('utf-8')
    destination=OUT/'AI导购预算重审_匿名复现材料.zip'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(selected.items()):
            info=zipfile.ZipInfo(name,(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,data)
    print(json.dumps({'entries':len(selected),'navigation_stubs':len(stubs),'bytes':destination.stat().st_size},ensure_ascii=False))

if __name__=='__main__':main()
