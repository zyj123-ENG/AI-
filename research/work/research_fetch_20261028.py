from pathlib import Path
import urllib.request, concurrent.futures, json, hashlib
from pypdf import PdfReader
R=Path(__file__).resolve().parents[1]
sources={
'N1_smu.pdf':'https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3688&context=sol_research',
'N5_yeung.pdf':'https://law.unimelb.edu.au/__data/assets/pdf_file/0003/3290385/Yeung-2017-Hypernudge-Big-Data-as-a-mode-of-regulation-by-.pdf',
'N4_hacker.html':'https://onlinelibrary.wiley.com/doi/full/10.1111/eulj.12389',
'N4_hacker.pdf':'https://onlinelibrary.wiley.com/doi/pdf/10.1111/eulj.12389',
'R1_lara2026.pdf':'https://link.springer.com/content/pdf/10.1007/s11948-026-00619-7.pdf',
'R2_delvalle2023.pdf':'https://link.springer.com/content/pdf/10.1007/s00146-023-01720-2.pdf',
'比赛通知.html':'https://www.aicomp.cn/notice/notice-3/3921.html',
'赛程调整.html':'https://www.aicomp.cn/notice/notice-3/5435.html',
'消法.html':'https://www.samr.gov.cn/zfjcj/tzgg/art/2023/art_615af9ed6bcd4974bf853dd2e02bc663.html',
'消法实施条例.html':'https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2024/art_0aea188276a44f0baf940ab95ee00e0a.html',
'个保法.html':'https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm',
'算法推荐规定.html':'https://www.cac.gov.cn/2022-01/04/c_1642894606364259.htm',
'互联网广告办法.html':'https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_d93a579afd45413e8576e4623fab348f.html',
'Apple快充条件.html':'https://support.apple.com/zh-cn/102574',
}
def get(item):
 name,url=item
 rec={'id':name,'url':url,'access_date':'2026-10-28','status':'failed'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=25) as resp:
   b=resp.read();rec['content_type']=resp.headers.get('Content-Type');rec['final_url']=resp.geturl()
  p=R/'sources'/name
  if name.endswith('.pdf') and not b.startswith(b'%PDF'):raise ValueError('Response is not a PDF')
  p.write_bytes(b)
  rec.update(status='saved',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),file=str(p))
  if name.endswith('.pdf'):
   doc=PdfReader(p);pages=[t.extract_text() or '' for t in doc.pages]
   rec['pages']=len(pages)
   (R/'work'/(name+'.txt')).write_text('\n\n'.join(f'===== PDF PAGE {i+1} =====\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
 except Exception as e:rec['error']=str(e)
 return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 records=list(pool.map(get,sources.items()))
(R/'evidence'/'补找与官方来源获取日志.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
for r in records: print(r['id'],r['status'],r.get('pages',''),r.get('error',''))
