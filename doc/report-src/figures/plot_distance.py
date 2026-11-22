from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

base = Path(__file__).resolve().parent
results = base.parents[2] / 'results'  # repository root
def load(name):
    return json.loads((results / (name + '.json')).read_text(encoding='utf8'))
cases = load('scorer_cases')
outcomes = [
    [r['B'] for r in load('scorer_eval_rows')],
    [r['loc'] for r in load('fullhist_trained_hist_e2e')],
    [r['loc'] for r in load('scorer_trained_hist_e2e')],
]
bins = [(1, 2), (3, 4), (5, 7), (8, 12), (13, 99)]
labels = ['1–2', '3–4', '5–7', '8–12', '13+']
colors = ['#505962', '#16756f', '#b11d38']
markers = ['x', 's', 'o']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'pdf.fonttype': 42})
fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.72))
fig.subplots_adjust(left=.13, right=.963, bottom=.27, top=.85, wspace=.6)
for ax, fn, title in zip(axes, (min, max), ('A   Earliest matching screen', 'B   Most recent matching screen')):
    d = [c['t'] - fn(c['valid']) for c in cases]
    text = []
    for j, (lo, hi) in enumerate(bins):
        members = [i for i, delta in enumerate(d) if lo <= delta <= hi]
        text.append(f'{labels[j]}  ({len(members)})')
        pct = [100*sum(seq[i] for i in members) / len(members) for seq in outcomes]
        if j%2 == 1:
            ax.axhspan(j-.47,j+.47,color='#f2f3f3',zorder=0,lw=0)
        ax.plot(pct[1:], [j,j], color='#b4bdc0',lw=2,zorder=1)
        for k,p in enumerate(pct):
            ax.scatter([p], [j+[-.13,0,.13][k]], c=colors[k], marker=markers[k], s=25, lw=1.1, zorder=3)
    ax.set_xlim(0,100)
    ax.set_ylim(4.52,-.56)
    ax.set_title(title,loc='left',size=9,weight='bold',pad=8)
    ax.set_xticks([0,25,50,75,100],['0','25','50','75','100'])
    ax.set_yticks(range(5),text)
    ax.tick_params(length=0,pad=4,labelsize=8)
    ax.grid(axis='x', color='#d9dfe1', lw=.5)
    ax.set_axisbelow(True)
    for edge in ax.spines.values(): edge.set_visible(False)
    ax.set_xlabel('Source localization (%)', fontsize=8)
items=[Line2D([],[],color=c,marker=m,linestyle='None',markersize=4.8,label=l) for c,m,l in zip(colors,markers,['Prompted full history','Trained full history','Trained per-screen scorer'])]
fig.legend(handles=items,loc='lower center',ncol=3,frameon=False,fontsize=8,handletextpad=.26,columnspacing=1.6,bbox_to_anchor=(.50,-.01))
fig.savefig(base/'distance.pdf')

