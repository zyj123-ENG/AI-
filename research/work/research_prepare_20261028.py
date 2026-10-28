from pathlib import Path
import json, hashlib, urllib.request, datetime
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
PACK=Path(__file__).resolve().parents[2] / 'literature'
for d in ['work','sources','evidence']:(ROOT/d).mkdir(parents=True,exist_ok=True)
items=[]
for p in sorted((PACK/'01_论文全文PDF').glob('*.pdf')):
    code=p.name.split('_')[0]
    doc=PdfReader(p)
    pages=[page.extract_text() or '' for page in doc.pages]
    (ROOT/'work'/f'{code}_pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'work'/f'{code}_fulltext.txt').write_text('\n\n'.join(f'\n===== PDF PAGE {i+1} =====\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
    items.append(dict(code=code,file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(pages),chars=sum(map(len,pages))))
(ROOT/'evidence'/'本地PDF清单与哈希.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
cards='\n\n'.join('===== '+p.name+' =====\n'+p.read_text(encoding='utf-8-sig') for p in sorted((PACK/'03_逐篇文献卡').glob('*.md')))
(ROOT/'work'/'all_cards.txt').write_text(cards,encoding='utf-8')
urlbase='https://www.aicomp.cn/wp-content/uploads/2026/05/'
official=['附件1AIC·AI伦理竞赛规则及作品提交要求.pdf','附件2AIC·AI伦理研究报告参考大纲.pdf']
for name in official:
    dest=ROOT/'sources'/name
    url=urlbase+urllib.parse.quote(name)
    if not dest.exists():
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            dest.write_bytes(urllib.request.urlopen(req,timeout=45).read())
        except Exception as e:
            print(name,str(e));continue
    doc=PdfReader(dest)
    (ROOT/'evidence'/(name+'.txt')).write_text('\n\n'.join(f'===== PDF PAGE {i+1} =====\n'+(p.extract_text() or '') for i,p in enumerate(doc.pages)),encoding='utf-8')
print(json.dumps(items,ensure_ascii=False,indent=2))
