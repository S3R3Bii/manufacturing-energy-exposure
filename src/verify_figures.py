"""Compare every retained artist coordinate with reviewed tables and check vector text."""
import csv
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
bindings = json.loads((ROOT / 'figures/figure_bindings.json').read_text())
def table(name):
    with (ROOT / 'results/analysis' / (name+'.csv')).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))
count = 0
def close(a, b):
    global count
    assert math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-7), (a, b)
    count += 1
periods = {(r['country'], r['basis']): r for r in table('periods') if r['start']=='2019'}
assert len(bindings['intensity']) == 8
for r in bindings['intensity']:
    close(r['width_pj'], float(periods[r['country'], r['basis']]['intensity_tj'])/1000)
contrasts = {(r['country'], int(r['year']), r['nace']): r for r in table('sector_contrasts')}
assert len(bindings['contrasts']) == len(contrasts) == 608
assert len({(r['country'], r['year'], r['nace']) for r in bindings['contrasts']}) == 608
for r in bindings['contrasts']:
    source = contrasts[r['country'], r['year'], r['nace']]
    close(r['x'], float(source['log_intensity_current'])*100)
    close(r['y'], float(source['log_intensity_pyp'])*100)
    assert r['opposite_sign'] == int(source['opposite_sign'])
ranks = {(r['country'], r['nace']): r for r in table('rankings')}
assert len(bindings['ranks']) == len(ranks) == 76
for r in bindings['ranks']:
    for k in ['current_rank', 'pyp_rank']:
        close(r[k], ranks[r['country'], r['nace']][k])
for name, text in [('intensity_contributions', '2019'), ('industry_contrasts', '608'), ('industry_rankings', '2023')]:
    svg = (ROOT / 'figures' / (name+'.svg')).read_text(encoding='utf-8')
    assert '<svg' in svg and text in svg
    for suffix in ['.png', '.svg']:
        assert (ROOT / 'figures' / (name+suffix)).stat().st_size > 1000
report = {'status':'PASS', 'plotted_numeric_coordinates_checked':count,
          'scope':'Actual Matplotlib artist coordinates against every reviewed plotted source row; SVG labels and file presence. Separate rendered visual inspection is required.'}
(ROOT / 'results/FIGURE_CHECK.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
