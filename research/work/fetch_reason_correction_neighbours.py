from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from pypdf import PdfReader
import json, hashlib

root = Path(__file__).resolve().parents[1]
items = [
    ('R6_Xie2023_PRAG', 'https://ojs.aaai.org/index.php/AAAI/article/download/26618/26390'),
    ('R7_Zhang2025_Refinement', 'https://aclanthology.org/2025.findings-emnlp.434.pdf'),
    ('R8_Kabongo2026_FactualConsistency_v2', 'https://arxiv.org/pdf/2512.24366v2'),
    ('R9_Gao2023_ALCE', 'https://aclanthology.org/2023.emnlp-main.398.pdf'),
]

def fetch(item):
    code, url = item
    dest = root / 'sources' / (code + '.pdf')
    result = dict(code=code, url=url, date='2026-10-28', timezone='Asia/Shanghai')
    try:
        if not dest.exists():
            with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=25) as response:
                data = response.read()
            if not data.startswith(b'%PDF'):
                raise ValueError('Response is not a PDF')
            dest.write_bytes(data)
        data = dest.read_bytes()
        pages = [page.extract_text() or '' for page in PdfReader(dest).pages]
        (root / 'work' / (code + '_pages.json')).write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
        (root / 'work' / (code + '_fulltext.txt')).write_text('\n\n'.join(f'===== PDF PAGE {i+1} =====\n{page}' for i,page in enumerate(pages)), encoding='utf-8')
        result.update(status='PDF obtained and extracted; reading status recorded separately', file=str(dest), sha256=hashlib.sha256(data).hexdigest(), pages=len(pages), chars=sum(map(len,pages)))
    except Exception as error:
        result.update(status='failed', error=str(error))
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(fetch, items))
(root / 'evidence' / '理由纠错近邻_获取记录.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
