"""Validate the revised artifact and its links to actual secondary-data outputs."""
from pathlib import Path
from docx import Document
from pypdf import PdfReader
import json,re,csv,hashlib,zipfile,math

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent/'secondary_data_reanalysis_20261029'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    draft=(ROOT/'draft.md').read_text(encoding='utf-8')
    title=draft.splitlines()[0][2:];intro=(ROOT/'作品简介_300字内.txt').read_text(encoding='utf-8').strip()
    body,back=draft.split('## 参考文献\n\n',1);refs=back.split('## 附录',1)[0]
    docx=ROOT/(title+'_二手数据修订稿.docx');pdf=ROOT/(title+'_二手数据修订稿.pdf')
    doc=Document(docx);reader=PdfReader(pdf)
    writing=json.loads((ROOT/'写作与证据记录.json').read_text(encoding='utf-8'))
    meta=json.loads((DATA/'results/run_metadata.json').read_text(encoding='utf-8'))
    audit=json.loads((DATA/'validation/独立复算.json').read_text(encoding='utf-8'))
    checks={
        'title_within_20':len(title)<=20,'intro_within_300':len(intro)<=300,
        'all_19_citations_resolve':set(map(int,re.findall(r'\[(\d+)\]',body)))==set(map(int,re.findall(r'^\[(\d+)\]',refs,re.M)))==set(range(1,20)),
        'no_template_or_named_citation_key':not re.search(r'\{\{|\[(?:Fong|DATA|PRE|N6|V\d|LAW\d|C\d|M\d)\]',draft),
        'old_synthetic_effects_removed':not any(t in body for t in ['51.70','46.48','32.15','12.80','120,000']),
        'four_tables_three_images':len(doc.tables)==4 and len(doc.inline_shapes)==3,
        'pdf_within_10M':pdf.stat().st_size<10_000_000,
        'no_empty_pdf_page':all(len(p.extract_text().strip())>100 for p in reader.pages),
        'docx_author_empty':not doc.core_properties.author and not doc.core_properties.last_modified_by,
        'pdf_author_empty':not (reader.metadata or {}).get('/Author'),
        'actual_observed_sample_and_bootstrap':meta['participants']==5050 and meta['bootstrap_repetitions']==5000 and meta['new_behavior_generated'] is False,
        'independent_point_check_pass':audit['within_scope_pass'] is True,
        'primary_numbers_in_report':all(t in body for t in ['63.22%','57.24%','5.98个百分点','[3.72, 8.28]']),
    }
    for name,expected in writing['source_results_sha256'].items():checks['unchanged_'+name]=sha(DATA/'results'/name)==expected
    intervals=True
    for name in ['arm_estimates.csv','contrasts.csv']:
        with (DATA/'results'/name).open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):
                v=[float(r[k]) for k in ['estimate','ci_low','ci_high']]
                intervals=intervals and all(math.isfinite(x) for x in v) and v[1]<=v[2]
    checks['finite_ordered_intervals']=intervals
    with zipfile.ZipFile(docx) as z:
        text='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith(('.xml','.rels')))
        checks['no_tracked_edits_or_comments']=not re.search(r'<w:(?:ins|del|commentRangeStart)\b',z.read('word/document.xml').decode('utf-8'))
    text+='\n'.join(p.extract_text() for p in reader.pages)
    for key,pattern in {
        'personal_machine_path':r'[A-Za-z]:[\\/]{1,2}Users[\\/]',
        'private_chat':r'https?://yuanbao\.tencent\.com/chat',
        'wechat_account':r'wxid_[A-Za-z0-9]+',
        'participant_platform_id':r'PROLIFICPID',
        'github_account':r'zyj123|github\.com/zyj',
        'access_token':r'gh[pousr]_[A-Za-z0-9]{20,}',
    }.items():checks['no_'+key]=not re.search(pattern,text,re.I)
    report={
        'date':'2026-10-29','pass':all(checks.values()),'checks':checks,
        'title_characters':len(title),'intro_characters':len(intro),'body_cjk':writing['counts']['body_cjk'],
        'pdf_pages':len(reader.pages),'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in [docx,pdf]},
        'visual_qa':{'all_17_pages_reviewed':True,'pages_1_to_15':'latest PNGs byte-identical to individually reviewed preceding render','pages_16_and_17':'latest appendix render individually inspected','result':'no empty page, clipping, overlap or missing glyph observed; long source paths left aligned'},
        'evidence_scope':'Real author-observed secondary data; actual MATLAB computation and participant-cluster bootstrap; independent Python point-estimate/count validation. No new consumers, original R/C intervention responses, budget measures or natural AI-error chain generated.',
        'review_fix':'Conclusion states normative premises ground responsibility and secondary data constrain measurement/acceptance, rather than implying an ought follows from observed differences.',
        'not_completed':['author substantive review','real CNKI detection and appendix report','defense PPT','full anonymous supplementary package/permanent sharing','official submission'],
    }
    (ROOT/'交付核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['pass']:raise SystemExit(1)

if __name__=='__main__':main()
