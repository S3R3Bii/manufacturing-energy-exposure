"""Original vector figures from the verified panel; record actual plotted coordinates."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ['BE', 'DE', 'FR', 'NL']
NAMES = {'BE': 'Belgium', 'DE': 'Germany', 'FR': 'France', 'NL': 'Netherlands'}
BLUE, GOLD, INK = '#205E85', '#B86F11', '#24333D'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelcolor': INK,
                     'text.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
                     'pdf.fonttype': 42, 'svg.fonttype': 'none', 'savefig.facecolor': 'white'})


def rows(name):
    with (ROOT / 'results/analysis' / (name + '.csv')).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    (ROOT / 'paper/images').mkdir(parents=True, exist_ok=True)
    bindings = {}
    def save(fig, name):
        for extension in ['svg', 'png']:
            fig.savefig(out / (name + '.' + extension), dpi=180, metadata={'Creator': 'Manufacturing energy exposure study'})
        # Matplotlib emits insignificant line-end spaces inside SVG path data.
        svg_path = out / (name + '.svg')
        svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines())+'\n', encoding='utf-8')
        fig.savefig(ROOT / 'paper/images' / (name + '.pdf'), metadata={'Creator': 'Manufacturing energy exposure study', 'CreationDate': None, 'ModDate': None})
        plt.close(fig)
    periods = rows('periods')
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    bindings['intensity'] = []
    y = np.arange(4)
    for basis, shift, color, hatch, label in [('current', -.18, BLUE, '///', 'Current-price output'),
                                               ('pyp', .18, GOLD, '', 'Matched previous-year prices')]:
        values = [float(next(r['intensity_tj'] for r in periods if r['country']==c and r['start']=='2019' and r['basis']==basis))/1000 for c in COUNTRIES]
        marks = ax.barh(y+shift, values, .32, color=color, hatch=hatch, label=label)
        for c, mark in zip(COUNTRIES, marks):
            bindings['intensity'].append({'country': c, 'basis': basis, 'width_pj': mark.get_width()})
            ax.text(mark.get_width()-16, mark.get_y()+mark.get_height()/2, f'{mark.get_width():,.1f}', ha='right', va='center', fontsize=9)
    ax.set_yticks(y, [NAMES[c] for c in COUNTRIES])
    ax.invert_yaxis()
    ax.set_xlim(-1780, 30)
    ax.axvline(0, color=INK, linewidth=.8)
    ax.set_xlabel('Linked intensity contribution, 2019–2023 (PJ)')
    ax.set_title('Output price basis and the attributed intensity contribution', loc='left', fontsize=12, pad=40)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.01), ncol=2, frameon=False, fontsize=9)
    ax.grid(axis='x', alpha=.15)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=.16, right=.98, bottom=.17, top=.77)
    save(fig, 'intensity_contributions')
    sectors = rows('sector_contrasts')
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    bindings['contrasts'] = []
    for opposite, marker, color, label in [('0', 'o', BLUE, 'Same sign or numerical zero'), ('1', 'x', GOLD, 'Opposite signs')]:
        chosen = [r for r in sectors if r['opposite_sign']==opposite]
        x = [float(r['log_intensity_current'])*100 for r in chosen]
        y = [float(r['log_intensity_pyp'])*100 for r in chosen]
        marks = ax.scatter(x, y, marker=marker, c=color, s=18, alpha=.65, label=f'{label} (n={len(chosen)})')
        for row, xy in zip(chosen, marks.get_offsets()):
            bindings['contrasts'].append({'country': row['country'], 'year': int(row['year']), 'nace': row['nace'],
                                          'x': float(xy[0]), 'y': float(xy[1]), 'opposite_sign': int(opposite)})
    all_xy = [r[k] for r in bindings['contrasts'] for k in ['x', 'y']]
    low, high = min(all_xy)-5, max(all_xy)+5
    ax.plot([low, high], [low, high], color=INK, linestyle=':', linewidth=.8, label='Identical log change')
    ax.axhline(0, color=INK, linewidth=.7); ax.axvline(0, color=INK, linewidth=.7)
    ax.set(xlim=(low, high), ylim=(low, high), xlabel='Current-price intensity change (100 × log ratio)',
           ylabel='Matched-price intensity change (100 × log ratio)')
    ax.set_title('Annual industry intensity changes: all 608 transitions', loc='left', fontsize=12)
    ax.legend(frameon=False, fontsize=9, loc='upper left')
    fig.subplots_adjust(left=.13, right=.97, top=.90, bottom=.15)
    save(fig, 'industry_contrasts')
    rankings = rows('rankings')
    codes = [r['nace'] for r in rankings if r['country']=='BE']
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 9.1), sharex=True, sharey=True)
    bindings['ranks'] = []
    for ax, c in zip(axes.flat, COUNTRIES):
        chosen = {r['nace']: r for r in rankings if r['country']==c}
        for i, s in enumerate(codes):
            r = chosen[s]; before, after = int(r['current_rank']), int(r['pyp_rank'])
            ax.plot([before, after], [i, i], color='#9DA8AD', linewidth=1)
            a, = ax.plot(before, i, 'o', color=BLUE, markerfacecolor='white', markersize=5)
            b, = ax.plot(after, i, 'D', color=GOLD, markersize=3.5)
            bindings['ranks'].append({'country': c, 'nace': s, 'current_rank': float(a.get_xdata()[0]), 'pyp_rank': float(b.get_xdata()[0])})
        ax.set_title(NAMES[c], loc='left', fontsize=11)
        ax.set_yticks(range(19), codes, fontsize=9)
        ax.tick_params(labelleft=True, labelbottom=True)
        ax.set_xticks([1, 5, 10, 15, 19])
        ax.set_xlim(.3, 19.7)
        ax.set_ylim(18.7, -.7)
        ax.grid(axis='x', alpha=.15)
        ax.set_xlabel('Energy/output rank (1 = highest)')
    fig.suptitle('2023 industry ranks under two output price bases', x=.04, ha='left', fontsize=12)
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([], [], marker='o', color=BLUE, markerfacecolor='white', linestyle='', label='Current-price output'),
                        Line2D([], [], marker='D', color=GOLD, linestyle='', label='Previous-year-price output')],
               loc='upper center', bbox_to_anchor=(.5, .954), ncol=2, frameon=False, fontsize=9)
    fig.subplots_adjust(left=.13, right=.98, top=.89, bottom=.07, hspace=.27, wspace=.35)
    save(fig, 'industry_rankings')
    (out / 'figure_bindings.json').write_text(json.dumps(bindings, indent=2)+'\n', encoding='utf-8')
    print('Exported three original figures and actual artist-coordinate bindings')


if __name__ == '__main__':
    main()
