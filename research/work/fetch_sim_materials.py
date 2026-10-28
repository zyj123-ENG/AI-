from pathlib import Path
from urllib.request import Request, urlopen
import json, hashlib
from pypdf import PdfReader

r = Path(__file__).resolve().parents[1]
dest = r / 'simulation_goal_repair_20261028'
for sub in ['sources','work','code','results','figures']:
    (dest/sub).mkdir(parents=True, exist_ok=True)
items=[
 ('M1_Selvaggi2024_ProductValuation','https://www.iris.unict.it/bitstream/20.500.11769/606530/1/40.%20Effects%20of%20misinformation.pdf'),
 ('M2_RichZaragoza_ImpliedExplicit','https://www.apa.org/pubs/journals/features/xlm-0000155.pdf'),
 ('M3_Scheibehenne2010_ChoiceOverload','https://scheibehenne.de/ScheibehenneGreifenederTodd2010.pdf'),
]
log=[]
for key,url in items:
    rec={'id':key,'url':url,'attemptDate':'2026-10-28','readStatus':'not yet read in this retrieval'}
    try:
        data=urlopen(Request(url,headers={'User-Agent':'Academic research source retrieval'}),timeout=35).read()
        if not data.startswith(b'%PDF'):
            raise ValueError('Response is not PDF')
        p=dest/'sources'/f'{key}.pdf'; p.write_bytes(data)
        reader=PdfReader(p); pages=[page.extract_text() or '' for page in reader.pages]
        (dest/'work'/f'{key}_pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        (dest/'work'/f'{key}_text.txt').write_text('\n\n'.join(f'===== PDF {i+1} =====\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
        rec.update({'status':'downloaded','pages':len(pages),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    except Exception as e:
        rec.update({'status':'unavailable','error':str(e)})
    log.append(rec)
(dest/'sources'/'acquisition_log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(log,ensure_ascii=False,indent=2))
