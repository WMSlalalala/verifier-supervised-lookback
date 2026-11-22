"""Figure 2: (a) localization by gap bucket, three conditions; (b) training effect per architecture."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT='/mnt/share/mwang49/guiodyssey'
S1,S2,S3='#2a78d6','#eb6834','#1baf7a'      # categorical slots 1-3 (validated set)
INK,INK2,GRID='#0b0b0b','#52514e','#d8d7d2'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.edgecolor':GRID,
                     'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,
                     'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})

cases=json.load(open(f'{ROOT}/scorer_cases.json'))
rows=json.load(open(f'{ROOT}/scorer_eval_rows.json'))
def probs(pfx):
    pr={}
    for f in range(5):
        for k,v in json.load(open(f'{ROOT}/{pfx}_fold{f}_probs.json')).items():
            pr[int(k)]={int(i):x for i,x in v.items()}
    return [max(pr[i],key=pr[i].get) in cases[i]['valid'] for i in range(len(cases))]
SC=probs('scorer'); FH=probs('fullhist'); B=[r['B'] for r in rows]
U=json.load(open(f'{ROOT}/scorer_untrained_probs.json'))
up={int(k):{int(i):x for i,x in v.items()} for k,v in U.items()}
UN=[max(up[i],key=up[i].get) in cases[i]['valid'] for i in range(len(cases))]
pct=lambda v: 100*sum(v)/max(len(v),1)

fig,(ax,ax2)=plt.subplots(1,2,figsize=(7.0,2.45),gridspec_kw={'width_ratios':[1.65,1]})

# ---- (a) grouped bars by gap ----
buckets=[(1,2),(3,4),(5,7),(8,12),(13,99)]
labels=['1–2','3–4','5–7','8–12','13+']
idxs=[[i for i,c in enumerate(cases) if lo<=c['gap']<=hi] for lo,hi in buckets]
ns=[len(i) for i in idxs]
series=[('Full history, prompted',B,S1),('Full history, trained',FH,S2),('Per-screen scorer, trained',SC,S3)]
x=np.arange(len(buckets)); w=0.26
for k,(nm,v,c) in enumerate(series):
    vals=[pct([v[i] for i in ix]) for ix in idxs]
    bars=ax.bar(x+(k-1)*w, vals, w*0.93, color=c, label=nm, zorder=3)
    for b,val in zip(bars,vals):
        ax.text(b.get_x()+b.get_width()/2, val+1.6, f'{val:.0f}', ha='center',
                va='bottom', fontsize=6.4, color=INK2, zorder=4)
ax.axvspan(2.5,3.5,color='#f3f2ef',zorder=0)
ax.text(3,96,'decomposition pays here',ha='center',fontsize=6.6,color=INK2,style='italic')
ax.set_xticks(x); ax.set_xticklabels([f'{l}\n(n={n})' for l,n in zip(labels,ns)])
ax.set_xlabel('gap: screens between the source screen and the need')
ax.set_ylabel('localization (%)'); ax.set_ylim(0,104)
ax.yaxis.grid(True,color=GRID,lw=.6,zorder=0); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=6.8,loc='upper left',bbox_to_anchor=(-0.02,1.19),
          ncol=1,handlelength=1.1,labelspacing=.25)
ax.set_title('(a) Localization by gap, 188 cases',fontsize=8,color=INK,loc='left',pad=22)

# ---- (b) dumbbell: prompted -> trained ----
arch=[('Full history',pct(B),pct(FH),S2),('Per-screen scorer',pct(UN),pct(SC),S3)]
for j,(nm,a,b,c) in enumerate(arch):
    y=1-j
    ax2.plot([a,b],[y,y],color=c,lw=2.4,zorder=2,solid_capstyle='round')
    ax2.scatter([a],[y],s=42,color='#ffffff',edgecolor=c,linewidth=1.8,zorder=3)
    ax2.scatter([b],[y],s=46,color=c,zorder=3)
    ax2.text(a-1.6,y,f'{a:.1f}',ha='right',va='center',fontsize=7,color=INK2)
    ax2.text(b+1.6,y,f'{b:.1f}',ha='left',va='center',fontsize=7,color=c,fontweight='bold')
    ax2.text(48.5,y+0.26,nm,ha='left',va='bottom',fontsize=7.2,color=INK)
    ax2.text((a+b)/2,y-0.30,f'+{b-a:.1f}',ha='center',va='top',fontsize=7,color=INK2)
ax2.set_xlim(44,82); ax2.set_ylim(-0.75,1.75)
ax2.set_yticks([]); ax2.spines['left'].set_visible(False)
ax2.set_xlabel('localization (%)')
ax2.xaxis.grid(True,color=GRID,lw=.6,zorder=0); ax2.set_axisbelow(True)
ax2.text(46,1.62,'○ prompted    ● trained on verifier labels',fontsize=6.8,color=INK2)
ax2.set_title('(b) What the free labels buy',fontsize=8,color=INK,loc='left',pad=22)

fig.tight_layout(w_pad=1.6)
fig.savefig('/mnt/share/mwang49/guiodyssey/report/figures/fig2_results.pdf',bbox_inches='tight')
fig.savefig('/mnt/share/mwang49/guiodyssey/report/figures/fig2_results.png',dpi=170,bbox_inches='tight')
print('saved; (a) buckets n =',ns)
print('(b) full history %.1f->%.1f  scorer %.1f->%.1f'%(pct(B),pct(FH),pct(UN),pct(SC)))
