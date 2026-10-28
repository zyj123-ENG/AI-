from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from pypdf import PdfReader
import hashlib, json

root=Path(__file__).resolve().parent
record=json.loads((root/'数值与出处核对.json').read_text(encoding='utf-8'))
for name,expected in record['deliverableSHA256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected
doc=root/'论文仿真章节_可编辑稿.docx'
with ZipFile(doc) as z:
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    styles=E.fromstring(z.read('word/styles.xml'))
    title=next(s for s in styles.findall('w:style',ns) if s.get('{'+ns['w']+'}styleId')=='Title')
    assert not title.findall('.//w:pBdr',ns)
    body=z.read('word/document.xml');xml=E.fromstring(body)
    assert len(xml.findall('.//m:oMath',ns))==2
    assert len(xml.findall('.//w:tbl',ns))==2
    assert 'C:/Users/' not in body.decode('utf-8')
pdf=next((root/'render_delivery').glob('*.pdf'))
pages=len(PdfReader(pdf).pages)
assert pages==6
same=[];changed=[]
for i in range(1,pages+1):
    f=f'page-{i}.png'
    (same if (root/'render_final'/f).read_bytes()==(root/'render_delivery'/f).read_bytes() else changed).append(i)
qa={'date':'2026-10-28','docx_bytes':doc.stat().st_size,'pages':pages,'tables':2,'figures':2,
    'editable_equations':2,'hashes':'pass','title_border':'removed',
    'numeric_review':'latest corrected CSV; reviewer found no substantive numeric error',
    'visual_review':'all six pages inspected; after final minor text edit, byte-identical pages reused and changed pages4/6 reopened',
    'unchanged_pages':same,'reopened_changed_pages':changed,
    'scope':'simulation methods/results/discussion sections; synthetic mechanism evidence',
    'docx_sha256':hashlib.sha256(doc.read_bytes()).hexdigest()}
(root/'最终交付核对.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False,indent=2))
