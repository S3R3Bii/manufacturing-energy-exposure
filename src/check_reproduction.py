"""Rebuild from retained API bytes in an isolated directory; compare every CSV value."""
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    compared = 0
    with tempfile.TemporaryDirectory(prefix='manufacturing-energy-replay-') as directory:
        replay = Path(directory)
        for name in ['src', 'tests', 'data/source']:
            shutil.copytree(ROOT / name, replay / name, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(ROOT / 'PROTOCOL.md', replay / 'PROTOCOL.md')
        (replay / 'results').mkdir()
        shutil.copy2(ROOT / 'results/CODE_FREEZE.json', replay / 'results/CODE_FREEZE.json')
        for script, args in [('ingest.py', []), ('verify_source.py', []), ('analyze.py', []),
                             ('verify_analysis.py', []), ('analyze.py', ['--confirm']),
                             ('verify_analysis.py', ['--confirm'])]:
            process = subprocess.run([sys.executable, str(replay / 'src' / script), *args],
                                     cwd=replay, capture_output=True, text=True)
            if process.returncode:
                raise AssertionError(script + '\n' + process.stdout + process.stderr)
        for relative in [Path('data/observations.csv'), Path('data/panel.csv'),
                         Path('results/source_reconciliation.csv'),
                         *[p.relative_to(ROOT) for p in sorted((ROOT / 'results/development').glob('*.csv'))],
                         *[p.relative_to(ROOT) for p in sorted((ROOT / 'results/analysis').glob('*.csv'))]]:
            with (ROOT / relative).open(encoding='utf-8', newline='') as f:
                retained = list(csv.DictReader(f))
            with (replay / relative).open(encoding='utf-8', newline='') as f:
                rebuilt = list(csv.DictReader(f))
            assert len(retained) == len(rebuilt), relative
            for left, right in zip(retained, rebuilt):
                assert set(left) == set(right), relative
                for key in left:
                    try:
                        a, b = float(left[key]), float(right[key])
                    except ValueError:
                        assert left[key] == right[key], (relative, key)
                    else:
                        assert math.isfinite(a) and math.isfinite(b)
                        assert math.isclose(a, b, abs_tol=1e-7, rel_tol=1e-9), (relative, key, a, b)
                        compared += 1
        source = json.loads((ROOT / 'results/source_accounting.json').read_text())
        fresh_source = json.loads((replay / 'results/source_accounting.json').read_text())
        assert source == fresh_source
        for phase in ['development', 'analysis']:
            fresh = json.loads((replay / 'results' / phase / 'INDEPENDENT_CHECK.json').read_text())
            assert fresh['status'] == 'PASS'
    frozen = json.loads((ROOT / 'results/CODE_FREEZE.json').read_text())
    for name, digest in frozen['sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    receipt = {'status': 'PASS', 'csv_numeric_values_rebuilt': compared,
               'absolute_tolerance': 1e-7, 'relative_tolerance': 1e-9,
               'scope': 'Isolated retained-source replay of every cell, eligibility rule, annual/period effect, industry contrast, volume index, rank and sensitivity; independent Decimal and SQL checks rerun. No network or paper recompilation.'}
    (ROOT / 'results/REPLAY_CHECK.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
