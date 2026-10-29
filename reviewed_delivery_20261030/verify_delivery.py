"""Verify this published subset; uses Python standard library only."""
from pathlib import Path
import hashlib,json,sys,zipfile

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'delivery_manifest.json').read_text(encoding='utf-8'))
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery_manifest.json'}
errors=[]
if actual!=set(manifest):errors.append('file list differs from delivery manifest')
for name,record in manifest.items():
    p=(ROOT/name).resolve()
    if not p.is_relative_to(ROOT) or not p.is_file():errors.append('missing or unsafe file: '+name);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256'] or p.stat().st_size!=record['bytes']:
        errors.append('file identity differs: '+name)
archive=ROOT/'AI导购预算重审_匿名复现材料.zip'
with zipfile.ZipFile(archive) as z:
    if z.testzip() is not None:errors.append('anonymous archive CRC failure')
    archived=json.loads(z.read('SHA256SUMS.json'))
    if set(archived)!=set(z.namelist())-{'SHA256SUMS.json'}:errors.append('anonymous archive member list differs')
    if any(hashlib.sha256(z.read(n)).hexdigest()!=h for n,h in archived.items()):errors.append('anonymous archive hash differs')
print(json.dumps({'files_checked':len(manifest),'anonymous_entries_checked':len(archived),'errors':errors,'scope':'Published subset identity; not independent ethical or consumer-effect validation'},ensure_ascii=False))
sys.exit(bool(errors))
