"""Build a publishable snapshot from local research inputs; never modify originals.

Run: python tools/build_public_snapshot.py --research PATH --literature PATH
      --stage1 PATH --summary PATH
The destination is the repository containing this script.
"""
from pathlib import Path
import argparse, csv, hashlib, io, json, re, shutil, zipfile

REPO = Path(__file__).resolve().parents[1]
TEXT_EXT = {'.md','.txt','.json','.csv','.py','.m','.html','.bib','.ris','.log'}
LICENSES = {
    'R1_lara2026.pdf': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/', 'PDF p20'),
    'R2_delvalle2023.pdf': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/', 'PDF p12'),
    'V1_Alfrink2023_ContestableAI.pdf': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/', 'PDF p23'),
    'V3_Fischli2026_ManyFacesAutonomy.pdf': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/', 'PDF p19'),
    'I1_The Role of Consumer Autonomy in Developing Sustainable AI_ A Conceptual Framework.pdf': ('CC BY 4.0','https://creativecommons.org/licenses/by/4.0/','PDF p1'),
    'I4_Technology, Autonomy, and Manipulation.pdf': ('CC BY 3.0 DE','https://creativecommons.org/licenses/by/3.0/de/','PDF p1'),
}
ALLOWED_PREFIXES = ('R1_','R2_','V1_','V3_','I1_','I4_')

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for k in ['research','literature','stage1','summary']: ap.add_argument('--'+k,required=True,type=Path)
    args=ap.parse_args()
    roots=[(args.research,'research'),(args.literature,'literature')]
    changes=[]; rows=[]; licences=[]; removed=[]
    absmap={}
    for root,dst in roots:
        for form in [str(root),root.as_posix(),str(root).replace('\\','\\\\')]: absmap[form]=dst
    absmap[str(args.stage1)]= 'stage1/拒绝后的再建议边界_研究报告初稿.pdf'
    absmap[args.stage1.as_posix()]= 'stage1/拒绝后的再建议边界_研究报告初稿.pdf'
    absmap[str(args.summary)]= 'literature/两轮文献汇总_消费者自主选择权_20261027.md'
    absmap[args.summary.as_posix()]= 'literature/两轮文献汇总_消费者自主选择权_20261027.md'

    def sanitize(s):
        for old,new in sorted(absmap.items(),key=lambda kv:-len(kv[0])): s=s.replace(old,new)
        # Replace remaining personal machine paths and private conversation locators.
        s=re.sub(r"[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2}[^\\/\s\"'<>]+", '<LOCAL_USER>',s,flags=re.I)
        s=re.sub(r"[A-Za-z]:[\\/]{1,2}xwechat_files[\\/]{1,2}[^\s\"'<>\]\)]+",'<LOCAL_ATTACHMENT>',s,flags=re.I)
        s=re.sub(r'wxid_[A-Za-z0-9_]+','<REDACTED_WECHAT_ID>',s)
        s=re.sub(r'https?://(?:tencent\.)?yuanbao(?:\.tencent)?\.com/chat[^\s<>"\)\]]*','<PRIVATE_CONVERSATION_REMOVED>',s)
        s=re.sub(r'https?://yuanbao\.tencent\.com/chat[^\s<>"\)\]]*','<PRIVATE_CONVERSATION_REMOVED>',s)
        s=re.sub(r'https?://tencent\.yuanbao/chat[^\s<>"\)\]]*','<PRIVATE_CONVERSATION_REMOVED>',s)
        s=re.sub(r'("(?:appConversationURL|conversationURL|conversationId|traceId|requestId)"\s*:\s*)"[^"\r\n]*"',r'\1"<PRIVATE_ID_REMOVED>"',s,flags=re.I)
        # Any accidental credential is removed, without printing the matched secret.
        s=re.sub(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}','<REDACTED_TOKEN>',s)
        return s

    def copy(src,dst,origin):
        data=src.read_bytes(); dst.parent.mkdir(parents=True,exist_ok=True)
        if src.suffix.lower() in TEXT_EXT:
            text=data.decode('utf-8-sig'); new=sanitize(text)
            if new!=text: changes.append(dst.relative_to(REPO).as_posix())
            data=new.encode('utf-8')
        elif src.suffix.lower()=='.docx':
            inp=zipfile.ZipFile(io.BytesIO(data)); buf=io.BytesIO(); xml_changed=False
            with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as out:
                for n in inp.namelist():
                    b=inp.read(n)
                    if n.endswith(('.xml','.rels')):
                        redacted=sanitize(b.decode('utf-8')).encode('utf-8')
                        xml_changed=xml_changed or redacted!=b;b=redacted
                    out.writestr(n,b)
            if xml_changed:data=buf.getvalue()
        dst.write_bytes(data)
        rows.append({'original':origin,'destination':dst.relative_to(REPO).as_posix(),'status':'included','source_sha256':sha(src.read_bytes()),'published_sha256':sha(data),'bytes':len(data)})

    def omit(src,origin,reason,stub=False):
        rows.append({'original':origin,'destination':'','status':'indexed_only','reason':reason,'source_sha256':sha(src.read_bytes()),'bytes':src.stat().st_size})
        removed.append((origin,reason))
        if stub:
            dest=REPO/(origin+'.source.md');dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text('# 来源文件索引\n\n原文件：`'+src.name+'`\n\nSHA256：`'+sha(src.read_bytes())+'`\n\n'+reason+'。题录、合法获取入口及读取范围见同目录来源日志、literature/文献目录与下载状态.md及逐篇文献卡。公开可获取不等于已核实再分发许可。\n',encoding='utf-8')

    for root,base in roots:
        for src in sorted(root.rglob('*')):
            if not src.is_file():continue
            rel=src.relative_to(root); origin=base+'/'+rel.as_posix(); ext=src.suffix.lower()
            if src.name=='AGENTS.md': omit(src,origin,'本机代理工作指令，不属于比赛研究材料');continue
            if ext=='.zip': omit(src,origin,'按公开副本重建复现包，避免包内旧路径及重复版本');continue
            if base=='literature' and rel.parts[0]=='02_原始网页': omit(src,origin,'第三方网页下载缓存；保留逐篇书目、来源和获取状态');continue
            is_source_pdf=ext=='.pdf' and ('sources' in rel.parts or base=='literature') and not src.name.startswith('附件')
            if is_source_pdf and src.name not in LICENSES:
                omit(src,origin,'本轮未核实该版本全文的公开再分发许可，原件留在本地',True);continue
            is_extracted=('work' in rel.parts and ext in {'.txt','.json'} and (re.search(r'_(fulltext|pages|text)\.',src.name) or src.name.endswith('.pdf.txt')))
            if is_extracted and not src.name.startswith(ALLOWED_PREFIXES) and 'refusal_draft_comparison' not in origin:
                omit(src,origin,'全文提取缓存随对应来源管理；公开保留阅读记录与方法矩阵');continue
            if base=='research' and src.name in {'C5_governance.png','I3_首页核验.png','S1_table2.png','创新续查_网页返回.json','理由纠错_网页检索返回.json'}:
                omit(src,origin,'第三方原文或网页长缓存；公开研究记录保留来源定位');continue
            copy(src,REPO/base/rel,origin)
            if src.name in LICENSES:
                name,url,locator=LICENSES[src.name]
                licences.append({'file':origin,'license':name,'license_url':url,'verified_locator':locator,'modification':'PDF unchanged; authors and source attribution retained'})

    copy(args.stage1,REPO/'stage1/拒绝后的再建议边界_研究报告初稿.pdf','stage1/拒绝后的再建议边界_研究报告初稿.pdf')
    copy(args.summary,REPO/'literature/两轮文献汇总_消费者自主选择权_20261027.md','literature/两轮文献汇总_消费者自主选择权_20261027.md')

    # Make archived collection scripts resolve within the clone instead of the author's PC.
    for p in (REPO/'research/work').glob('*.py'):
        s=p.read_text(encoding='utf-8'); before=s
        s=re.sub(r"Path\(r?['\"]research['\"]\)","Path(__file__).resolve().parents[1]",s)
        s=re.sub(r"Path\(r?['\"]literature['\"]\)","Path(__file__).resolve().parents[2] / 'literature'",s)
        if s!=before: p.write_text(s,encoding='utf-8');changes.append(p.relative_to(REPO).as_posix())
    # Avoid leaving old reproducibility checksums as if they applied to the redacted copies.
    for p in list(REPO.rglob('文件校验SHA256.json'))+list(REPO.rglob('*文件校验SHA256.txt')):
        p.replace(p.with_name(p.name+'.local-record'))

    for row in rows:
        if row['status']!='included': continue
        dest=REPO/row['destination']
        if not dest.is_file() and dest.with_name(dest.name+'.local-record').is_file():
            dest=dest.with_name(dest.name+'.local-record')
            row['destination']=dest.relative_to(REPO).as_posix()
        if dest.is_file():
            data=dest.read_bytes();row['published_sha256']=sha(data);row['bytes']=len(data)

    pr=REPO/'provenance';pr.mkdir(exist_ok=True)
    (pr/'source_inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (pr/'third_party_licenses.json').write_text(json.dumps(licences,ensure_ascii=False,indent=2),encoding='utf-8')
    (pr/'publication_changes.json').write_text(json.dumps({'date':'2026-10-29','modified_text_files':sorted(set(changes)),'originals_preserved':True,'note':'Source hashes refer to local originals; verify current published bytes with repository SHA256 manifest.'},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 公开副本范围与来源','', '原始研究文件保持在本地。此仓库包含代码、当前及历史数值结果、方案、论证矩阵、来源/阅读记录、报告片段、第一阶段稿与后续任务。','', '已核验许可的第三方PDF保留原文和署名；许可、定位见 third_party_licenses.json。其余全文及提取缓存保留索引、SHA256与获取入口。','', '下列条目以索引方式保留：','', '|原条目|处理理由|','|---|---|']
    lines += ['|'+x.replace('|','/')+'|'+y+'|' for x,y in removed]
    (pr/'PUBLICATION_SCOPE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Rebuild a portable computational archive from already-public files only.
    sim=REPO/'research/simulation_goal_repair_20261028'
    target=REPO/'research/仿真复现包_纠错与目标修订_20261028.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(sim.rglob('*')):
            if p.is_file() and p.relative_to(sim).parts[0] not in {'work','sources','results_smoke'}:
                z.write(p,arcname='simulation_goal_repair_20261028/'+p.relative_to(sim).as_posix())
    print(json.dumps({'included':sum(x['status']=='included' for x in rows),'indexed_only':len(removed),'licenses':len(licences),'modified_text_files':len(set(changes)),'repro_zip_bytes':target.stat().st_size},ensure_ascii=False))

if __name__=='__main__':main()
