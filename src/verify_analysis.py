"""Independent 50-digit Decimal reconstruction; imports no primary analysis code."""
import argparse
import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
ROOT = Path(__file__).resolve().parents[1]
D = Decimal
SECTORS = ['C10-C12', 'C13-C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21', 'C22',
           'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29', 'C30', 'C31_C32', 'C33']


def verify(root=ROOT, confirm=False):
    out = root / 'results' / ('analysis' if confirm else 'development')
    countries = ['BE', 'DE', 'FR', 'NL'] if confirm else ['DE', 'FR', 'NL']
    with (root / 'data/panel.csv').open(encoding='utf-8', newline='') as f:
        panel = {(r['country'], int(r['year']), r['nace']): r for r in csv.DictReader(f)}
    def v(c, y, s, field):
        return D(panel[c, y, s][field])
    expected = {name: [] for name in ['annual', 'sector_contrasts', 'volume_indices',
                                     'rankings', 'leave_one_out', 'periods', 'coverage']}
    def decomposition(c, y, chosen, basis):
        pairs = [(v(c, y-1, s, 'energy_tj'), v(c, y, s, 'energy_tj'),
                  v(c, y-1, s, 'output_cp'), v(c, y, s, 'output_cp' if basis == 'current' else 'output_pyp'))
                 for s in chosen]
        a0, a1 = sum(p[2] for p in pairs), sum(p[3] for p in pairs)
        activity = structure = intensity = D(0)
        for e0, e1, q0, q1 in pairs:
            weight = e0 if e0 == e1 else (e1 - e0) / (e1.ln() - e0.ln())
            # Independent log differences avoid the primary ratio/log1p path.
            activity += weight * (a1.ln() - a0.ln())
            structure += weight * ((q1.ln() - a1.ln()) - (q0.ln() - a0.ln()))
            intensity += weight * ((e1.ln() - q1.ln()) - (e0.ln() - q0.ln()))
        e0, e1 = sum(p[0] for p in pairs), sum(p[1] for p in pairs)
        change = e1 - e0
        return dict(activity_tj=activity, structure_tj=structure, intensity_tj=intensity,
                    energy_change_tj=change, residual_tj=activity+structure+intensity-change,
                    energy0_tj=e0, energy1_tj=e1)
    for c in countries:
        index = dict.fromkeys(SECTORS, D(100))
        for y in range(2015, 2024):
            for s in SECTORS:
                if y > 2015:
                    index[s] = index[s] * v(c, y, s, 'output_pyp') / v(c, y-1, s, 'output_cp')
                official = D(100) * v(c, y, s, 'volume_index') / v(c, 2015, s, 'volume_index')
                expected['volume_indices'].append(dict(country=c, year=y, nace=s,
                    chained_index=index[s], official_index=official, difference_points=index[s]-official))
                if y > 2015:
                    energy = v(c, y, s, 'energy_tj').ln() - v(c, y-1, s, 'energy_tj').ln()
                    nominal = energy - v(c, y, s, 'output_cp').ln() + v(c, y-1, s, 'output_cp').ln()
                    controlled = energy - v(c, y, s, 'output_pyp').ln() + v(c, y-1, s, 'output_cp').ln()
                    wedge = v(c, y, s, 'output_cp').ln() - v(c, y, s, 'output_pyp').ln()
                    assert abs(controlled - nominal - wedge) < D('1e-40')
                    expected['sector_contrasts'].append(dict(country=c, year=y, nace=s,
                        log_intensity_current=nominal, log_intensity_pyp=controlled, price_wedge=wedge,
                        opposite_sign=int(abs(nominal)>D('1e-10') and abs(controlled)>D('1e-10') and nominal*controlled<0)))
            if y > 2015:
                for basis in ['current', 'pyp']:
                    expected['annual'].append(dict(country=c, year=y, basis=basis, **decomposition(c, y, SECTORS, basis)))
                    for excluded in SECTORS:
                        expected['leave_one_out'].append(dict(country=c, year=y, basis=basis,
                            excluded_nace=excluded, **decomposition(c, y, [s for s in SECTORS if s != excluded], basis)))
        for start in [2015, 2019]:
            for basis in ['current', 'pyp']:
                rows = [r for r in expected['annual'] if r['country']==c and r['basis']==basis and r['year']>start]
                sums = {field: sum(r[field] for r in rows) for field in ['activity_tj', 'structure_tj', 'intensity_tj', 'energy_change_tj']}
                endpoint = sum(v(c, 2023, s, 'energy_tj') - v(c, start, s, 'energy_tj') for s in SECTORS)
                assert sums['energy_change_tj'] == endpoint
                sums['residual_tj'] = sums['activity_tj'] + sums['structure_tj'] + sums['intensity_tj'] - endpoint
                expected['periods'].append(dict(country=c, start=start, end=2023, basis=basis, **sums))
        intensity = {basis: {s: v(c, 2023, s, 'energy_tj') / v(c, 2023, s, field) for s in SECTORS}
                     for basis, field in [('current', 'output_cp'), ('pyp', 'output_pyp')]}
        orders = {basis: {s: i+1 for i, s in enumerate(sorted(SECTORS, key=lambda s: (-rates[s], s)))}
                  for basis, rates in intensity.items()}
        for s in SECTORS:
            expected['rankings'].append(dict(country=c, year=2023, nace=s,
                energy_per_cp=intensity['current'][s], energy_per_pyp=intensity['pyp'][s],
                current_rank=orders['current'][s], pyp_rank=orders['pyp'][s]))
    for y in range(2015, 2024):
        totals = {c: sum(v(c, y, s, 'energy_tj') for s in SECTORS) for c in ['BE', 'DE', 'ES', 'FR', 'IT', 'NL']}
        for c, energy in totals.items():
            expected['coverage'].append(dict(country=c, year=y, eligible=int(c in ['BE', 'DE', 'FR', 'NL']),
                energy_tj=energy, share_six_country_energy=energy/sum(totals.values())))
    comparisons, max_delta, tables = 0, D(0), {}
    for name, rows in expected.items():
        with (out / (name + '.csv')).open(encoding='utf-8', newline='') as f:
            actual = list(csv.DictReader(f))
        assert len(actual) == len(rows), name
        for source, target in zip(rows, actual):
            assert set(source) == set(target), name
            for key, value in source.items():
                if isinstance(value, str):
                    assert value == target[key], (name, key, value, target[key])
                    continue
                given = D(target[key])
                delta = abs(D(value) - given)
                tolerance = max(D('1e-7'), D('1e-9') * abs(D(value)))
                assert delta <= tolerance, (name, key, delta, tolerance)
                comparisons += 1
                max_delta = max(delta, max_delta)
        tables[name] = len(rows)
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['countries'] == countries and summary['belgium_evaluated'] == confirm
    assert summary['sector_transitions'] == len(expected['sector_contrasts'])
    assert summary['opposite_sign_transitions'] == sum(r['opposite_sign'] for r in expected['sector_contrasts'])
    max_gap = max(abs(r['difference_points']) for r in expected['volume_indices'])
    assert max_gap <= D('.25')
    assert abs(D(str(summary['max_official_index_gap_points'])) - max_gap) <= D('1e-7')
    report = dict(status='PASS', precision_digits=50, absolute_tolerance=1e-7, relative_tolerance=1e-9,
                  independent_numeric_comparisons=comparisons, max_absolute_difference=float(max_delta),
                  tables=tables, countries=countries,
                  scope='All reported effects, linked endpoints, omitted-industry effects, contrasts, indices, ranks and coverage; no primary analysis helper imported.')
    (out / 'INDEPENDENT_CHECK.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', action='store_true')
    verify(confirm=parser.parse_args().confirm)
