import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from PIL import Image
SH='/mnt/share/mwang49/guiodyssey/shots'; ROOT='/mnt/share/mwang49/guiodyssey'
OUT='/mnt/share/mwang49/guiodyssey/slides/figures'
RED,AQUA,INDIGO='#CC0000','#2db597','#4156a1'
INK,MUT,GRAY,LGRAY='#000000','#4d4d4d','#b2b2b2','#f2f2f2'
plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,
   'axes.edgecolor':GRAY,'axes.labelcolor':MUT,'xtick.color':MUT,'ytick.color':MUT,
   'axes.spines.top':False,'axes.spines.right':False})
EP='4671561041722435'; SRC,NEED=6,11

# ================= 1. the idea =================
fig=plt.figure(figsize=(13.33,5.6)); fig.patch.set_facecolor('white')
fig.text(0.5,0.945,'The check that finds the question also answers it',ha='center',
         fontsize=19,color=INK,fontweight='bold')
for k,i in enumerate(range(0,NEED)):
    ax=fig.add_axes([0.045+k*0.083,0.47,0.070,0.34])
    im=Image.open(f'{SH}/{EP}_{i}.png'); ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
    hit=(i==SRC)
    for s in ax.spines.values(): s.set_color(RED if hit else GRAY); s.set_linewidth(3.2 if hit else 1.0)
    if not hit: ax.imshow([[(1,1,1,0.55)]],extent=[0,im.size[0],im.size[1],0],aspect='auto')
    ax.set_title(f'{i}',fontsize=10,color=INK if hit else MUT,pad=3)
    fig.add_artist(FancyBboxPatch((0.045+k*0.083,0.345),0.070,0.075,
        boxstyle='round,pad=0,rounding_size=0.012',transform=fig.transFigure,
        fc='#fdecec' if hit else 'white',ec=RED if hit else GRAY,lw=2.2 if hit else 1.0))
    fig.text(0.080+k*0.083,0.383,'1' if hit else '0',ha='center',va='center',
             fontsize=16,color=RED if hit else MUT,fontweight='bold')
fig.text(0.5,0.285,'label for every earlier screen, free — nobody looks at any of them',
         ha='center',fontsize=14,color=INK,fontweight='bold')
fig.add_artist(FancyBboxPatch((0.22,0.10),0.56,0.135,boxstyle='round,pad=0,rounding_size=0.015',
    transform=fig.transFigure,fc=LGRAY,ec=MUT,lw=1.3))
fig.text(0.5,0.195,'The verifier (one substring test per screen)',ha='center',fontsize=13.5,
         color=INK,fontweight='bold')
fig.text(0.5,0.140,'"Electronic Study"  ∈  OCR(screen i)    and    ∉  OCR(screen 11)',
         ha='center',fontsize=13,color=MUT)
fig.savefig(f'{OUT}/idea.png',dpi=145,bbox_inches='tight',facecolor='white')

# ================= data =================
cases=json.load(open(f'{ROOT}/scorer_cases.json'))
rows=json.load(open(f'{ROOT}/scorer_eval_rows.json'))
def probs(p):
    pr={}
    for f in range(5):
        for k,v in json.load(open(f'{ROOT}/{p}_fold{f}_probs.json')).items():
            pr[int(k)]={int(i):x for i,x in v.items()}
    return [max(pr[i],key=pr[i].get) in cases[i]['valid'] for i in range(len(cases))]
SC,FH=probs('scorer'),probs('fullhist'); B=[r['B'] for r in rows]
U=json.load(open(f'{ROOT}/scorer_untrained_probs.json'))
up={int(k):{int(i):x for i,x in v.items()} for k,v in U.items()}
UN=[max(up[i],key=up[i].get) in cases[i]['valid'] for i in range(len(cases))]
pct=lambda v:100*sum(v)/max(len(v),1)

# ================= 2. what the free labels buy =================
fig,ax=plt.subplots(figsize=(11.2,4.5)); fig.patch.set_facecolor('white')
pairs=[('Read the whole\nhistory in one call',pct(B),pct(FH),AQUA),
       ('Score each earlier\nscreen one at a time',pct(UN),pct(SC),RED)]
for j,(nm,a,b,c) in enumerate(pairs):
    y=1-j
    ax.plot([a,b],[y,y],color=c,lw=8,solid_capstyle='round',zorder=2)
    ax.scatter([a],[y],s=330,color='white',edgecolor=MUT,linewidth=2.5,zorder=3)
    ax.scatter([b],[y],s=360,color=c,zorder=3)
    ax.text(a-0.9,y,f'{a:.1f}',ha='right',va='center',fontsize=14,color=MUT)
    ax.text(b+1.4,y,f'{b:.1f}',ha='left',va='center',fontsize=17,color=c,fontweight='bold')
    ax.text(a-0.3,y+0.22,nm.replace('\n',' '),ha='left',va='bottom',fontsize=13,color=INK)
    ax.text((a+b)/2,y-0.27,f'+{b-a:.1f} points',ha='center',va='top',fontsize=13,
            color=c,fontweight='bold')
ax.set_xlim(47.0,81); ax.set_ylim(-0.75,1.80); ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.set_xlabel('finds a screen that holds the answer (%)',fontsize=13)
ax.xaxis.grid(True,color=LGRAY,lw=1.2,zorder=0); ax.set_axisbelow(True)
ax.annotate('prompted',xy=(pairs[0][1],1),xytext=(pairs[0][1]-0.3,1.56),fontsize=12,color=MUT,
            ha='center',arrowprops=dict(arrowstyle='-',color=GRAY,lw=1.2,shrinkA=2,shrinkB=8))
ax.annotate('trained on the free labels',xy=(pairs[0][2],1),xytext=(pairs[0][2]+1.2,1.56),
            fontsize=12,color=INK,fontweight='bold',ha='center',
            arrowprops=dict(arrowstyle='-',color=GRAY,lw=1.2,shrinkA=2,shrinkB=9))
fig.tight_layout(); fig.savefig(f'{OUT}/labels_buy.png',dpi=145,bbox_inches='tight',facecolor='white')

# ================= 3. by gap =================
fig,ax=plt.subplots(figsize=(11.4,4.7)); fig.patch.set_facecolor('white')
bk=[(1,2),(3,4),(5,7),(8,12),(13,99)]; lab=['1–2','3–4','5–7','8–12','13+']
idx=[[i for i,c in enumerate(cases) if lo<=c['gap']<=hi] for lo,hi in bk]
ser=[('one call, prompted',B,INDIGO),('one call, trained',FH,AQUA),('score each screen, trained',SC,RED)]
x=np.arange(5); w=0.26
ax.axvspan(2.5,3.5,color='#fdecec',zorder=0)
for k,(nm,v,c) in enumerate(ser):
    val=[pct([v[i] for i in ix]) for ix in idx]
    bars=ax.bar(x+(k-1)*w,val,w*0.92,color=c,label=nm,zorder=3)
    for b,vv in zip(bars,val):
        ax.text(b.get_x()+b.get_width()/2,vv+1.8,f'{vv:.0f}',ha='center',va='bottom',
                fontsize=11,color=MUT,zorder=4)
ax.annotate('scoring one screen at a time\nwins only here',xy=(3,86),xytext=(2.46,104),
            fontsize=12.5,color=RED,fontweight='bold',ha='center',linespacing=1.25,
            arrowprops=dict(arrowstyle='-|>',color=RED,lw=1.5,shrinkA=4,shrinkB=4))
ax.set_xticks(x); ax.set_xticklabels([f'{l}\n(n={len(i)})' for l,i in zip(lab,idx)],fontsize=12)
ax.set_xlabel('how many screens back the answer was',fontsize=13)
ax.set_ylabel('finds it (%)',fontsize=13); ax.set_ylim(0,112)
ax.set_yticks([0,25,50,75,100])
ax.yaxis.grid(True,color=LGRAY,lw=1.2,zorder=0); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=12,loc='upper left',bbox_to_anchor=(0,1.17),ncol=3,
          handlelength=1.3,columnspacing=1.8)
fig.tight_layout(); fig.savefig(f'{OUT}/by_gap.png',dpi=145,bbox_inches='tight',facecolor='white')

# ================= 4. external set =================
fig,ax=plt.subplots(figsize=(8.6,4.4)); fig.patch.set_facecolor('white')
names=['one call,\nprompted','screen index,\nprompted','one call,\ntrained','score each screen,\ntrained']
vals=[59.1,37.6,76.3,79.6]; cols=[INDIGO,GRAY,AQUA,RED]
bars=ax.bar(range(4),vals,0.56,color=cols,zorder=3)
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2,v+1.6,f'{v:.1f}',ha='center',fontsize=14,
            color=INK,fontweight='bold',zorder=4)
ax.set_xticks(range(4)); ax.set_xticklabels(names,fontsize=11.5)
ax.set_ylabel('finds it (%)',fontsize=13); ax.set_ylim(0,95); ax.set_yticks([0,25,50,75])
ax.yaxis.grid(True,color=LGRAY,lw=1.2,zorder=0); ax.set_axisbelow(True)
ax.text(2.5,88,'the two trained models are\nstatistically indistinguishable (p=0.63)',
        ha='center',fontsize=12,color=MUT,linespacing=1.3)
fig.tight_layout(); fig.savefig(f'{OUT}/external.png',dpi=145,bbox_inches='tight',facecolor='white')
print('idea / labels_buy / by_gap / external saved')
