"""Check report structure, unchanged evidence, metadata and final artifact bytes."""
from pathlib import Path
from pypdf import PdfReader
from docx import Document
import re, json, hashlib, zipfile

ROOT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    draft=(ROOT/'draft.md').read_text(encoding='utf-8')
    writing=json.loads((ROOT/'写作与证据记录.json').read_text(encoding='utf-8'))
    title=draft.splitlines()[0][2:]
    abstract=draft.split('## 摘要\n\n',1)[1].split('\n\n关键词：',1)[0]
    docx=ROOT/(title+'_完整初稿.docx'); pdf=ROOT/(title+'_完整初稿.pdf')
    doc=Document(docx); reader=PdfReader(pdf)
    body,back=draft.split('## 参考文献\n\n',1)
    refs=back.split('## 附录',1)[0]
    cited=set(map(int,re.findall(r'\[(\d+)\]',body)))
    listed=set(map(int,re.findall(r'^\[(\d+)\]',refs,re.M)))
    checks={
        'title_within_20':len(title)<=20,
        'intro_within_300':len(abstract)<=300,
        'all_citations_resolve':cited==listed==set(range(1,18)),
        'no_unresolved_template':not re.search(r'\{\{|\[(?:N6|V1|V2|V3|Fong|LAW\d|C\d|S1|M\d)\]',draft),
        'four_tables_three_figures':len(doc.tables)==4 and len(doc.inline_shapes)==3,
        'pdf_within_10M':pdf.stat().st_size<10_000_000,
        'no_empty_pdf_page':all(len(p.extract_text().strip())>100 for p in reader.pages),
        'docx_author_empty':not doc.core_properties.author and not doc.core_properties.last_modified_by,
        'pdf_author_empty':not (reader.metadata or {}).get('/Author'),
    }
    for name,expected in writing['source_data_sha256'].items():
        checks['unchanged_'+name]=sha(ROOT.parent/'simulation_goal_repair_20261028/results'/name)==expected
    with zipfile.ZipFile(docx) as z:
        xml=z.read('word/document.xml').decode('utf-8')
        checks['three_editable_equations']=xml.count('<m:oMath>')==3
        checks['no_track_changes_or_comments']=not re.search(r'<w:(?:ins|del|commentRangeStart)\b',xml)
        text='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith(('.xml','.rels')))
    text+='\n'.join(p.extract_text() for p in reader.pages)
    identity_patterns={
        'personal_path':r'[A-Za-z]:[\\/]{1,2}Users[\\/]',
        'private_chat':r'https?://yuanbao\.tencent\.com/chat',
        'wechat_id':r'wxid_[A-Za-z0-9]+',
        'github_identity':r'zyj123|github\.com/zyj',
        'access_token':r'gh[pousr]_[A-Za-z0-9]{20,}',
    }
    for name,pattern in identity_patterns.items():checks['no_'+name]=not re.search(pattern,text,re.I)
    (ROOT/'作品简介_300字内.txt').write_text(abstract+'\n',encoding='utf-8')
    result={
        'date':'2026-10-29','pass':all(checks.values()),'checks':checks,
        'title':title,'title_characters':len(title),'intro_characters':len(abstract),
        'body_cjk':writing['counts']['body_cjk'],'pdf_pages':len(reader.pages),
        'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [docx,pdf]},
        'visual_qa':{'all_17_pages_reviewed':True,'pages_1_to_11':'latest PNGs byte-identical to individually reviewed preceding render','pages_12_to_17':'latest PNGs individually inspected after final caption and bibliography repair','result':'no blank page, clipped content, overlapping table or missing glyph observed'},
        'acronym_advisory_review':'Flags are bibliography surnames, document-type notation, PDF page locators and common appendix file/presentation abbreviations; MCSE expanded in main text. No unresolved conceptual acronym found in main argument.',
        'review_repairs':['M3 supports heterogeneous choice-overload effects; attention costs remain assumptions','V1 cited for contestable AI operationalization rather than a direct value-sensitive-design source','governance table caption added; bibliography kept on one page'],
        'scope':'This checks the current report and local introduction only. It is not CNKI detection, full anonymous submission-package acceptance or human-effects validation.',
        'pending':['author substantive review','real CNKI report','defense PPT','anonymous supplementary package and permanent share','official upload and receipt'],
    }
    (ROOT/'交付核对.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['pass']:raise SystemExit(1)

if __name__=='__main__':main()
