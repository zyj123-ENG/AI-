"""Check the domestic-data report against the retained observations and outputs."""
from pathlib import Path
from docx import Document
from pypdf import PdfReader
import csv
import hashlib
import json
import math
import re
import zipfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / 'domestic_data_reanalysis_20261029'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    draft = (ROOT / 'draft.md').read_text(encoding='utf-8')
    title = draft.splitlines()[0][2:]
    intro = (ROOT / '作品简介_300字内.txt').read_text(encoding='utf-8').strip()
    body, back = draft.split('## 参考文献\n\n', 1)
    refs = back.split('## 附录', 1)[0]
    docx = ROOT / (title + '_国内数据修订稿.docx')
    pdf = ROOT / (title + '_国内数据修订稿.pdf')
    doc, reader = Document(docx), PdfReader(pdf)
    writing = json.loads((ROOT / '写作与证据记录.json').read_text(encoding='utf-8'))
    meta = json.loads((DATA / 'results/run_metadata.json').read_text(encoding='utf-8'))
    audit = json.loads((DATA / 'validation/独立复算.json').read_text(encoding='utf-8'))
    source = json.loads((DATA / '来源与许可.json').read_text(encoding='utf-8'))
    checks = {
        'title_within_20': len(title) <= 20,
        'intro_within_300': len(intro) <= 300,
        'all_19_citations_resolve': set(map(int, re.findall(r'\[(\d+)\]', body)))
        == set(map(int, re.findall(r'^\[(\d+)\]', refs, re.M))) == set(range(1, 20)),
        'no_template_or_named_citation_key': not re.search(
            r'\{\{|\[(?:Fong|Huang|DATA|DOMDATA|PRE|N6|V\d|LAW\d|C\d|M\d)\]', draft),
        'old_synthetic_or_foreign_effects_removed': not any(t in body for t in
            ['51.70', '46.48', '32.15', '12.80', '120,000', '63.22%', '57.24%', '5.98个百分点', '5050']),
        'four_tables_three_images': len(doc.tables) == 4 and len(doc.inline_shapes) == 3,
        'pdf_within_10M': pdf.stat().st_size < 10_000_000,
        'no_empty_pdf_page': all(len(p.extract_text().strip()) > 100 for p in reader.pages),
        'docx_author_empty': not doc.core_properties.author and not doc.core_properties.last_modified_by,
        'pdf_author_empty': not (reader.metadata or {}).get('/Author'),
        'actual_domestic_sample_and_bootstrap': meta['participants'] == 516
        and meta['campus_sensitivity_n'] == 403 and meta['bootstrap_repetitions'] == 5000
        and meta['new_behavior_generated'] is False and meta['missing_imputed'] is False
        and meta['cell_counts'] == [88, 88, 84, 84, 86, 86]
        and meta['seeds'] == [20261029, 20261030],
        'independent_point_check_pass': audit['within_scope_pass'] is True,
        'primary_numbers_in_report': all(t in body for t in
            ['-0.160', '[-0.542, 0.220]', '0.186', '[-0.646, 0.250]']),
        'fixed_original_csv_identity': sha(DATA / 'source/author_original/data/study4_memory_data.csv')
        == 'dec91f502f9fb40f2f89e9e980e981edcf1670e928a91d911a60464c815b0360',
    }
    for name, expected in writing['source_results_sha256'].items():
        checks['unchanged_' + name] = sha(DATA / 'results' / name) == expected
    for entry in source['files']:
        p = DATA / entry['file']
        checks['original_' + p.name] = sha(p) == entry['sha256'] and p.stat().st_size == entry['bytes']
    intervals = True
    for name in ['cell_estimates.csv', 'contrasts.csv']:
        with (DATA / 'results' / name).open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                values = [float(row[k]) for k in ['estimate', 'ci_low', 'ci_high']]
                intervals = intervals and all(math.isfinite(v) for v in values) and values[1] <= values[2]
    checks['finite_ordered_intervals'] = intervals
    with zipfile.ZipFile(docx) as z:
        text = '\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith(('.xml', '.rels')))
        checks['no_tracked_edits_or_comments'] = not re.search(
            r'<w:(?:ins|del|commentRangeStart)\b', z.read('word/document.xml').decode('utf-8'))
    text += '\n'.join(p.extract_text() for p in reader.pages)
    for key, pattern in {
        'personal_machine_path': r'[A-Za-z]:[\\/]{1,2}Users[\\/]',
        'private_chat': r'https?://yuanbao\.tencent\.com/chat',
        'wechat_account': r'wxid_[A-Za-z0-9]+',
        'participant_platform_id': r'PROLIFICPID',
        'github_account': r'zyj123|github\.com/zyj',
        'access_token': r'gh[pousr]_[A-Za-z0-9]{20,}',
    }.items():
        checks['no_' + key] = not re.search(pattern, text, re.I)
    report = {
        'date': '2026-10-29', 'pass': all(checks.values()), 'checks': checks,
        'title_characters': len(title), 'intro_characters': len(intro),
        'body_cjk': writing['counts']['body_cjk'], 'pdf_pages': len(reader.pages),
        'files': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in [docx, pdf]},
        'visual_qa': {
            'all_17_pages_reviewed': True,
            'review_method': 'Each page of the final rendered 17-page document was individually inspected as a PNG; final PDF is the byte-identical PDF from that render.',
            'result': 'No empty page, clipping, overlap or missing glyph observed; both data figures and the logic figure were legible; long appendix paths left aligned.',
        },
        'evidence_scope': 'Author-observed human responses from domestic recruitment; actual base-MATLAB categorical OLS and within-original-arm participant bootstrap. Independent Python point/count/F/p checks did not independently rerun bootstrap intervals. No new consumer, unobserved treatment response or budget behavior generated.',
        'not_completed': ['author substantive review', 'real CNKI detection and appendix report',
            'defense PPT', 'full anonymous supplementary package/permanent sharing', 'official submission'],
    }
    (ROOT / '交付核对.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
