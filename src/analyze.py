"""Fixed descriptive estimands; Belgium requires the committed code-freeze receipt."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from accounting import decompose
from config import ROOT, COUNTRIES, YEARS, SECTORS


def save_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def run(root=ROOT, confirm=False):
    gate = json.loads((root / 'results/source_accounting.json').read_text())
    assert gate['status'] == 'PASS_SOURCE_GATE'
    countries = gate['eligible_countries']
    if confirm:
        frozen = json.loads((root / 'results/CODE_FREEZE.json').read_text())
        assert frozen['status'] == 'FROZEN_BEFORE_BELGIUM_OUTCOMES'
        for name, digest in frozen['sha256'].items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    else:
        countries = [c for c in countries if c != 'BE']
    with (root / 'data/panel.csv').open(encoding='utf-8', newline='') as f:
        raw = list(csv.DictReader(f))
    panel = {(r['country'], int(r['year']), r['nace']): r for r in raw}
    def value(c, y, s, field):
        return float(panel[c, y, s][field])
    annual, sectors, indices, ranks, sensitivity, periods = [], [], [], [], [], []
    for c in countries:
        chain = {s: 100.0 for s in SECTORS}
        for y in YEARS:
            for s in SECTORS:
                if y > YEARS[0]:
                    chain[s] *= value(c, y, s, 'output_pyp') / value(c, y-1, s, 'output_cp')
                official = value(c, y, s, 'volume_index')
                rebased = official / value(c, YEARS[0], s, 'volume_index') * 100
                indices.append({'country': c, 'year': y, 'nace': s,
                                'chained_index': chain[s], 'official_index': rebased,
                                'difference_points': chain[s] - rebased})
            if y == YEARS[0]:
                continue
            for s in SECTORS:
                r0, r1 = panel[c, y-1, s], panel[c, y, s]
                energy_log = math.log(float(r1['energy_tj']) / float(r0['energy_tj']))
                nominal = energy_log - math.log(float(r1['output_cp']) / float(r0['output_cp']))
                controlled = energy_log - math.log(float(r1['output_pyp']) / float(r0['output_cp']))
                wedge = math.log(float(r1['output_cp']) / float(r1['output_pyp']))
                opposite = abs(nominal) > 1e-10 and abs(controlled) > 1e-10 and nominal * controlled < 0
                sectors.append({'country': c, 'year': y, 'nace': s,
                                'log_intensity_current': nominal, 'log_intensity_pyp': controlled,
                                'price_wedge': wedge, 'opposite_sign': int(opposite)})
            for basis, field in [('current', 'output_cp'), ('pyp', 'output_pyp')]:
                def effects(selected):
                    return decompose([value(c, y-1, s, 'energy_tj') for s in selected],
                                     [value(c, y, s, 'energy_tj') for s in selected],
                                     [value(c, y-1, s, 'output_cp') for s in selected],
                                     [value(c, y, s, field) for s in selected])
                annual.append({'country': c, 'year': y, 'basis': basis, **effects(SECTORS)})
                for excluded in SECTORS:
                    sensitivity.append({'country': c, 'year': y, 'basis': basis,
                                        'excluded_nace': excluded,
                                        **effects([s for s in SECTORS if s != excluded])})
        for start in (2015, 2019):
            for basis in ('current', 'pyp'):
                chosen = [r for r in annual if r['country'] == c and r['basis'] == basis and r['year'] > start]
                sums = {k: math.fsum(r[k] for r in chosen)
                        for k in ('activity_tj', 'structure_tj', 'intensity_tj', 'energy_change_tj')}
                sums['residual_tj'] = math.fsum(sums[k] for k in ('activity_tj', 'structure_tj', 'intensity_tj')) - sums['energy_change_tj']
                periods.append({'country': c, 'start': start, 'end': 2023, 'basis': basis, **sums})
        intensities = {b: {s: value(c, 2023, s, 'energy_tj') / value(c, 2023, s, field)
                          for s in SECTORS} for b, field in [('current', 'output_cp'), ('pyp', 'output_pyp')]}
        ordering = {b: {s: i+1 for i, s in enumerate(sorted(SECTORS, key=lambda s: (-v[s], s)))}
                    for b, v in intensities.items()}
        for s in SECTORS:
            ranks.append({'country': c, 'year': 2023, 'nace': s,
                          'energy_per_cp': intensities['current'][s], 'energy_per_pyp': intensities['pyp'][s],
                          'current_rank': ordering['current'][s], 'pyp_rank': ordering['pyp'][s]})
    coverage = []
    for y in YEARS:
        total = math.fsum(value(c, y, s, 'energy_tj') for c in COUNTRIES for s in SECTORS)
        for c in COUNTRIES:
            energy = math.fsum(value(c, y, s, 'energy_tj') for s in SECTORS)
            coverage.append({'country': c, 'year': y, 'eligible': int(c in gate['eligible_countries']),
                             'energy_tj': energy, 'share_six_country_energy': energy / total})
    out = root / 'results' / ('analysis' if confirm else 'development')
    out.mkdir(exist_ok=True)
    for name, rows in [('annual', annual), ('sector_contrasts', sectors), ('volume_indices', indices),
                       ('rankings', ranks), ('leave_one_out', sensitivity), ('periods', periods), ('coverage', coverage)]:
        save_csv(out / (name + '.csv'), rows)
    summary = {'status': 'COMPUTED_PENDING_INDEPENDENT_CHECKS', 'countries': countries,
               'belgium_evaluated': confirm, 'sector_transitions': len(sectors),
               'opposite_sign_transitions': sum(r['opposite_sign'] for r in sectors),
               'max_official_index_gap_points': max(abs(r['difference_points']) for r in indices),
               'max_decomposition_residual_tj': max(abs(r['residual_tj']) for r in annual + sensitivity + periods)}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))
    assert summary['max_official_index_gap_points'] <= .25, 'Preserve source-series consistency failure'
    assert summary['max_decomposition_residual_tj'] <= 1e-7


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    run(confirm=args.confirm)
