"""Source-bound manuscript claims, reviewed hashes, PDF text and bounded active-content checks."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from pypdf import PdfReader
ROOT = Path(__file__).resolve().parents[1]


def main():
    tex = (ROOT / 'paper/main.tex').read_text(encoding='utf-8')
    reader = PdfReader(ROOT / 'paper/manuscript.pdf')
    assert len(reader.pages) == 7
    extracted = '\n'.join(p.extract_text() for p in reader.pages)
    assert all(len(p.extract_text()) > 200 for p in reader.pages)
    assert 'not peer reviewed' in extracted and '82 (13.5%' in extracted
    def rows(name):
        with (ROOT / 'results/analysis' / (name+'.csv')).open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    periods, sectors, ranks, omissions = [rows(n) for n in ['periods', 'sector_contrasts', 'rankings', 'leave_one_out']]
    names = {'BE':'Belgium','DE':'Germany','FR':'France','NL':'Netherlands'}
    for c, name in names.items():
        pair = {r['basis']: r for r in periods if r['country']==c and r['start']=='2019'}
        expected = name+' & '+' & '.join(f"{float(v)/1000:,.1f}" for v in [pair['pyp']['energy_change_tj'], pair['current']['intensity_tj'], pair['pyp']['intensity_tj']])
        assert expected in tex, expected
        choices = {s: sum(float(r['intensity_tj']) for r in omissions if r['country']==c and r['basis']=='pyp' and r['excluded_nace']==s and int(r['year'])>2019)/1000
                   for s in sorted({r['excluded_nace'] for r in omissions})}
        expected = name+' & '+f"{float(pair['pyp']['intensity_tj'])/1000:,.1f}"+' & ['+f'{min(choices.values()):,.1f}, {max(choices.values()):,.1f}'+']'
        assert expected in tex, expected
        top = {b:{r['nace'] for r in ranks if r['country']==c and int(r[b+'_rank'])<=5} for b in ['current','pyp']}
        assert len(top['current'] & top['pyp']) == 5
    count = sum(int(r['opposite_sign']) for r in sectors)
    assert len(sectors)==608 and count==82
    assert f'{count} ({100*count/len(sectors):.1f}\\%)' in tex
    assert [sum(int(r['opposite_sign']) for r in sectors if r['country']==c) for c in names] == [22,18,24,18]
    assert [sum(int(r['opposite_sign']) for r in sectors if r['year']==str(y)) for y in range(2016,2024)] == [7,13,12,11,7,9,10,13]
    assert [sum(r['current_rank']!=r['pyp_rank'] for r in ranks if r['country']==c) for c in names] == [6,2,0,2]
    coverage = rows('coverage')
    excluded = sum(float(r['share_six_country_energy']) for r in coverage if r['year']=='2023' and r['eligible']=='0')
    assert f'{100*excluded:.1f}\\%' in tex
    # Bind historical diagnostics to the exact committed review certificates;
    # a fresh replay may differ in its last floating-point residual digits.
    review = json.loads((ROOT / 'paper/REVIEW.json').read_text(encoding='utf-8'))
    certificates = {}
    for name, digest in review['publication_certificate_sha256'].items():
        blob = subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == digest, name
        certificates[name] = json.loads(blob)
    summary = certificates['results/analysis/summary.json']
    assert summary['max_decomposition_residual_tj'] < 1.1e-9
    assert summary['max_official_index_gap_points'] < .0118
    assert certificates['results/analysis/INDEPENDENT_CHECK.json']['independent_numeric_comparisons'] == 16724
    assert json.loads((ROOT/'results/REPLAY_CHECK.json').read_text())['csv_numeric_values_rebuilt'] == 42515
    freeze = json.loads((ROOT / 'results/CODE_FREEZE.json').read_text())
    for name, digest in freeze['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
    scope = json.loads((ROOT/'paper/PUBLICATION_SCOPE.json').read_text())
    assert scope['scope']=='independent-program-study' and scope['formal_submission_target'] is False
    assert len(scope['public_files'])==5
    for name,digest in scope['public_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
    root = reader.trailer['/Root']
    assert '/EmbeddedFiles' not in root.get('/Names', {}) and '/JavaScript' not in root.get('/Names', {})
    action = root.get('/OpenAction')
    if isinstance(action, dict):
        assert action.get('/S') == '/GoTo', action
    for page in reader.pages:
        assert '/AA' not in page
        for annotation in page.get('/Annots', []):
            item = annotation.get_object()
            assert item.get('/Subtype') != '/FileAttachment' and '/AA' not in item
            if '/A' in item:
                assert item['/A'].get('/S') in ('/URI','/GoTo')
    report = {'status':'PASS','pages':7,'scope':'Both manuscript tables; all source counts, sign reversals, annual counts, top-five stability, rank changes, exclusion share, frozen code and committed diagnostic certificates; exact approved source/PDF hashes, readable PDF text and bounded active-content checks.',
              'limitations':'Rendered review is separate; this is not peer review, proof of measurement accuracy, accessibility conformance or universal security detection.'}
    (ROOT/'results/INDEPENDENT_PAPER_CHECK.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    main()
