"""Retarget local working-copy links to files or source-index stubs in this clone."""
from pathlib import Path
from urllib.parse import unquote,quote
import json,os,re

ROOT=Path(__file__).resolve().parents[1]

def main():
    inventory=json.loads((ROOT/'provenance/source_inventory.json').read_text(encoding='utf-8'))
    omitted={x['original'] for x in inventory if x['status']=='indexed_only'}
    changed=[]; unresolved=[]
    def resolve(base,target):
        t=unquote(target.strip('<>'))
        if re.match(r'^(https?:|mailto:|data:|#|codex:|plugin:)',t,re.I):return None
        path,sep,anchor=t.partition('#')
        if not path:return None
        candidates=[(base/path).resolve(),(ROOT/path).resolve()]
        if candidates[0].is_relative_to(ROOT) and candidates[0].is_file(): return None
        for marker in ['research/','literature/','stage1/','planning/']:
            at=path.find(marker)
            if at>=0:candidates.append((ROOT/path[at:]).resolve())
        for c in candidates:
            if not c.is_relative_to(ROOT):continue
            dest=c
            if not dest.is_file():
                if dest.with_name(dest.name+'.source.md').is_file():dest=dest.with_name(dest.name+'.source.md')
                elif dest.with_name(dest.name+'.local-record').is_file():dest=dest.with_name(dest.name+'.local-record')
                elif dest.relative_to(ROOT).as_posix() in omitted:dest=ROOT/'provenance/PUBLICATION_SCOPE.md'
                else:continue
            return quote(os.path.relpath(dest,base).replace('\\','/'),safe='/._-')+(sep+anchor if sep else '')
        return False
    for p in ROOT.rglob('*.md'):
        if '.git' in p.parts:continue
        s=p.read_text(encoding='utf-8-sig')
        def repl(m):
            new=resolve(p.parent,m.group(2))
            if new is False:
                unresolved.append({'file':p.relative_to(ROOT).as_posix(),'target':m.group(2)})
                return m.group(0)
            return m.group(0) if new is None else m.group(1)+'('+new+')'
        new=re.sub(r'(!?\[[^\]\n]*\])\((<?[^\n)]+>?)\)',repl,s)
        if new!=s:p.write_text(new,encoding='utf-8');changed.append(p.relative_to(ROOT).as_posix())
    # Original navigation HTML has local PDF links too.
    for p in (ROOT/'literature').glob('*.html'):
        s=p.read_text(encoding='utf-8-sig')
        def href(m):
            new=resolve(p.parent,m.group(2))
            return m.group(0) if not new else m.group(1)+new+m.group(3)
        new=re.sub(r'(href=[\"\x27])([^\"\x27]+)([\"\x27])',href,s)
        if new!=s:p.write_text(new,encoding='utf-8');changed.append(p.relative_to(ROOT).as_posix())
    report={'changed':changed,'unresolved_legacy_links':unresolved,'note':'Historic references to private local attachments or optional absent files may remain as text; current README/planning links are checked below.'}
    (ROOT/'provenance/link_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'rewritten_files':len(changed),'unresolved_legacy_links':len(unresolved)},ensure_ascii=False))

if __name__=='__main__':main()
