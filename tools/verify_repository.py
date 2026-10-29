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

def verify_domestic_analysis(checks,errors):
    """Read current domestic artifacts; append aggregate checks without writing."""
    domestic=ROOT/'research/domestic_data_reanalysis_20261029'
    raw=domestic/'source/author_original/data/study4_memory_data.csv'
    expected_sha='dec91f502f9fb40f2f89e9e980e981edcf1670e928a91d911a60464c815b0360'
    primary_target=-0.1597075405
    raw_ok=raw.is_file() and digest(raw)==expected_sha
    checks.append({'check':'current_domestic_source_csv_sha256','role':'current_domestic',
                   'pass':raw_ok,'expected_sha256':expected_sha})
    if not raw_ok:errors.append('current domestic source CSV differs from the fixed author version')
    try:
        meta=json.loads((domestic/'results/run_metadata.json').read_text(encoding='utf-8'))
        audit=json.loads((domestic/'validation/独立复算.json').read_text(encoding='utf-8'))
        with raw.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
        campus_labels={'Campus session','Campus resident session'}
        campus=sum(r['Testing_Channel'] in campus_labels for r in rows)
        online=sum(r['Testing_Channel']=='Online/network test' for r in rows)
        cells=[('No Memory','No Control'),('No Memory','Editable Dashboard'),
               ('Relevant Memory','No Control'),('Relevant Memory','Editable Dashboard'),
               ('Intrusive Memory','No Control'),('Intrusive Memory','Editable Dashboard')]
        counts=[sum((r['Memory_Type'],r['Control_Interface'])==cell for r in rows) for cell in cells]
        population_ok=(len(rows)==516 and len({r['Participant_ID'] for r in rows})==516
            and all(18<=float(r['Age'])<=62 for r in rows) and campus==403 and online==113
            and counts==[88,88,84,84,86,86])
        checks.append({'check':'current_domestic_analysis_population','role':'current_domestic',
                       'pass':population_ok,'participants':len(rows),
                       'campus_sensitivity_n':campus,'online_network_n':online,'cell_counts':counts})
        if not population_ok:errors.append('current domestic population structure differs from the documented sample')
        with (domestic/'results/contrasts.csv').open(encoding='utf-8-sig',newline='') as f:
            contrasts=list(csv.DictReader(f))
        primary=[r for r in contrasts if r['sample']=='all_516' and r['metric']=='trust_mean'
                 and r['contrast']=='primary_intrusive_gap_change']
        analysis_ok=(meta['participants']==516 and meta['campus_sensitivity_n']==403
            and meta['cell_counts']==[88,88,84,84,86,86]
            and meta['bootstrap_repetitions']==5000 and meta['seeds']==[20261029,20261030]
            and meta['new_behavior_generated'] is False and meta['missing_imputed'] is False
            and meta['primary_metric']=='trust_mean'
            and meta['primary_contrast']=='primary_intrusive_gap_change'
            and len(primary)==1 and abs(float(primary[0]['estimate'])-primary_target)<1e-9)
        checks.append({'check':'current_domestic_observed_analysis','role':'current_domestic',
                       'pass':analysis_ok,'participants':meta['participants'],
                       'campus_sensitivity_n':meta['campus_sensitivity_n'],
                       'bootstrap_repetitions':meta['bootstrap_repetitions'],
                       'primary_delta':float(primary[0]['estimate']) if len(primary)==1 else None})
        if not analysis_ok:errors.append('current domestic run or primary contrast differs from the documented analysis')
        independent_primary=[r for r in audit.get('contrasts',{}).get('comparisons',[])
            if r.get('sample')=='all_516' and r.get('metric')=='trust_mean'
            and r.get('contrast')=='primary_intrusive_gap_change']
        audit_ok=(audit.get('within_scope_pass') is True
            and audit.get('input_identity',{}).get('sha256')==expected_sha
            and audit.get('source_integrity',{}).get('participants')==516
            and audit.get('cell_estimates',{}).get('rows_checked')==56
            and audit.get('contrasts',{}).get('rows_checked')==84
            and audit.get('ols_coefficients',{}).get('rows_checked')==12
            and audit.get('trust_item_frequencies',{}).get('rows_checked')==252
            and len(independent_primary)==1
            and abs(float(independent_primary[0]['estimate_python'])-primary_target)<1e-9)
        checks.append({'check':'current_domestic_independent_recalculation','role':'current_domestic',
                       'pass':audit_ok,'within_scope_pass':audit.get('within_scope_pass')})
        if not audit_ok:errors.append('current domestic independent recalculation is missing or inconsistent')
    except (OSError,ValueError,KeyError,TypeError,csv.Error):
        # Do not print exception values: they can contain local paths or raw data.
        checks.append({'check':'current_domestic_required_artifacts','role':'current_domestic','pass':False})
        errors.append('current domestic required artifacts are missing or invalid')

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

    verify_domestic_analysis(checks,errors)
    removal=json.loads((ROOT/'provenance/removed_simulations_20261029.json').read_text(encoding='utf-8'))
    retired_present=[x['path'] for x in removal['removed_files'] if (ROOT/x['path']).is_file()]
    checks.append({'check':'retired_simulation_files_absent','pass':not retired_present,'removed_files':len(removal['removed_files'])})
    if retired_present:errors.append('retired simulation files have reappeared')

    inventory=json.loads((ROOT/'provenance/source_inventory.json').read_text(encoding='utf-8'))
    for r in inventory:
        if r['status']=='included':
            p=ROOT/r['destination']
            if not p.is_file() or digest(p)!=r['published_sha256']:errors.append('source inventory mismatch: '+r['destination'])
    checks.append({'check':'source_inventory','files':len(inventory)})
    report={'date':'2026-10-30','scope':'published bytes, provenance, JSON/Python syntax, accidental credentials/private locators, current domestic source identity and selected aggregate results; retired foreign-data and synthetic analysis files absent from the current tree; not a new analysis or independent human validation','files':len(current),'total_bytes':sum(x['bytes'] for x in current.values()),'checks':checks,'errors':errors,'pass':not errors}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if not errors else 1

if __name__=='__main__':sys.exit(main())
