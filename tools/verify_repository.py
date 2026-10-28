"""Verify published bytes and core numerical results using Python stdlib only."""
from pathlib import Path
import argparse, csv, hashlib, json, re, sys, zipfile

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'provenance/SHA256SUMS.json'
REPORT=ROOT/'provenance/repository_verification.json'
EXCLUDED={'provenance/SHA256SUMS.json','provenance/repository_verification.json'}

def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in {'.git','__pycache__'} for x in p.relative_to(ROOT).parts) and p.relative_to(ROOT).as_posix() not in EXCLUDED)

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write-manifest',action='store_true');args=ap.parse_args()
    checks=[];errors=[]
    current={p.relative_to(ROOT).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size} for p in files()}
    if args.write_manifest:
        MANIFEST.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
    if not MANIFEST.is_file():raise SystemExit('Missing manifest; create with --write-manifest')
    expected=json.loads(MANIFEST.read_text(encoding='utf-8'))
    if current!=expected:errors.append('published file list, hash or byte count differs from manifest')
    checks.append({'check':'repository_sha256','pass':current==expected,'files':len(current)})

    # Secrets are reported by file and category, never by matched values.
    patterns={
        'access_token':re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'),
        'private_chat_url':re.compile(r'https?://(?:yuanbao\.tencent\.com|tencent\.yuanbao)/chat[^\s"<>]*',re.I),
        'wechat_identifier':re.compile(r'wxid_[A-Za-z0-9]{6,}'),
        'personal_machine_path':re.compile(r'[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2}[A-Za-z0-9_\-]{2,}[\\/]'),
    }
    text_ext={'.md','.txt','.json','.csv','.py','.m','.html','.bib','.ris','.log','.local-record'}
    for p in files():
        name=p.relative_to(ROOT).as_posix()
        if p.stat().st_size>=100_000_000:errors.append('oversized Git file: '+name)
        if p.suffix.lower() in text_ext:
            try:s=p.read_text(encoding='utf-8-sig')
            except UnicodeDecodeError:continue
            for kind,pat in patterns.items():
                if pat.search(s): errors.append(kind+': '+name)
            if p.suffix=='.json':
                try:json.loads(s)
                except json.JSONDecodeError:errors.append('invalid JSON: '+name)
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                bad=z.testzip()
                if bad:errors.append('ZIP CRC failure: '+name)
                for member in z.namelist():
                    if Path(member).suffix.lower() in text_ext:
                        try:s=z.read(member).decode('utf-8-sig')
                        except UnicodeDecodeError:continue
                        for kind,pat in patterns.items():
                            if pat.search(s):errors.append(kind+': '+name+'!'+member)
        if p.suffix=='.docx':
            with zipfile.ZipFile(p) as z:
                for member in z.namelist():
                    if member.endswith(('.xml','.rels')):
                        s=z.read(member).decode('utf-8')
                        for kind,pat in patterns.items():
                            if pat.search(s):errors.append(kind+': '+name+'!'+member)
        if p.suffix=='.py':
            try:compile(p.read_text(encoding='utf-8-sig'),name,'exec')
            except SyntaxError as e:errors.append('Python syntax: '+name+': '+str(e))

    tab=ROOT/'research/simulation_goal_repair_20261028/results/all_summary.csv'
    with tab.open(encoding='utf-8-sig',newline='') as f: records=list(csv.DictReader(f))
    base={r['policy']:r for r in records if r['scenario']=='base' and r['rule']=='bounded_default' and r['type']=='1'}
    targets={'D1_R0_C0':(0.13465,0.4648),'D1_R1_C0':(0.41015,0.356025),'D1_R0_C1':(0.195475,0.440525),'D1_R1_C1':(0.51695,0.312525)}
    for p,(review,pending) in targets.items():
        r=base[p];ok=abs(float(r['goal_reviewed'])-review)<1e-10 and abs(float(r['dependent_unreviewed_upgrade'])-pending)<1e-10
        checks.append({'check':'corrected_baseline_'+p,'pass':ok})
        if not ok:errors.append('corrected baseline changed: '+p)

    inventory=json.loads((ROOT/'provenance/source_inventory.json').read_text(encoding='utf-8'))
    for r in inventory:
        if r['status']=='included':
            p=ROOT/r['destination']
            if not p.is_file() or digest(p)!=r['published_sha256']:errors.append('source inventory mismatch: '+r['destination'])
    checks.append({'check':'source_inventory','files':len(inventory)})
    report={'date':'2026-10-29','scope':'published bytes, provenance, JSON/Python syntax, accidental credentials/private locators and selected corrected baseline values; not a new simulation or human validation','files':len(current),'total_bytes':sum(x['bytes'] for x in current.values()),'checks':checks,'errors':errors,'pass':not errors}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if not errors else 1

if __name__=='__main__':sys.exit(main())
