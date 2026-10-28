from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from pypdf import PdfReader
import json,hashlib
root=Path(__file__).resolve().parents[1]
items=[
 ('V1_Alfrink2023_ContestableAI','https://link.springer.com/content/pdf/10.1007/s11023-022-09611-z.pdf'),
 ('V2_AshtonFranklin2022_MetaPreferences','https://arxiv.org/pdf/2209.11801'),
 ('V3_Fischli2026_ManyFacesAutonomy','https://link.springer.com/content/pdf/10.1007/s11023-026-09786-9.pdf'),
 ('V4_Li2026_PredictionMemory','https://arxiv.org/pdf/2607.24798'),
]
def fetch(item):
 code,url=item; p=root/'sources'/(code+'.pdf'); result=dict(code=code,url=url,date='2026-10-28',timezone='Asia/Shanghai')
 try:
  if not p.exists():
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response: data=response.read()
   if not data.startswith(b'%PDF'): raise ValueError('not a PDF')
   p.write_bytes(data)
  data=p.read_bytes(); pages=[q.extract_text() or '' for q in PdfReader(p).pages]
  (root/'work'/(code+'_pages.json')).write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
  (root/'work'/(code+'_fulltext.txt')).write_text('\n\n'.join(f'===== PDF PAGE {i+1} =====\n'+q for i,q in enumerate(pages)),encoding='utf-8')
  result.update(status='obtained and extracted; reading separately recorded',file=str(p),pages=len(pages),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e: result.update(status='failed',error=str(e))
 print(json.dumps(result,ensure_ascii=False),flush=True);return result
with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(fetch,items))
(root/'evidence'/'创新续查V1-V4_获取记录.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
