"""Slide figure: the problem, told with real screenshots from GUI-Odyssey."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from PIL import Image
SH='/mnt/share/mwang49/guiodyssey/shots'
RED,AQUA,INDIGO='#CC0000','#2db597','#4156a1'
INK,MUT,GRAY='#000000','#4d4d4d','#cccccc'
plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42})
EP='4671561041722435'; SRC,NEED=6,11
fig=plt.figure(figsize=(13.33,5.6)); fig.patch.set_facecolor('white')

def shot(ax,i,box=None,dim=False):
    im=Image.open(f'{SH}/{EP}_{i}.png'); W,H=im.size
    ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(GRAY); s.set_linewidth(1.2)
    if box:
        x0,y0,x1,y1=box
        ax.add_patch(Rectangle((x0-14,y0-14),(x1-x0)+28,(y1-y0)+28,fill=False,ec=RED,lw=4))
    if dim: ax.imshow([[(1,1,1,0.55)]],extent=[0,W,H,0],aspect='auto')
    return W,H

# --- source screen (big, left) ---
axL=fig.add_axes([0.035,0.10,0.20,0.74]); shot(axL,SRC,box=[306,1686,642,1743])
axL.set_title(f'Screen {SRC}   a music app',fontsize=12,color=INK,pad=7)
fig.text(0.135,0.055,'the agent sees "Electronic Study"\n5th of 42 items on this screen',
         ha='center',fontsize=11,color=RED,fontweight='bold',linespacing=1.3)

# --- middle screens (small, dimmed) ---
for k,i in enumerate([7,8,9,10]):
    ax=fig.add_axes([0.275+k*0.093,0.30,0.078,0.40]); shot(ax,i,dim=True)
    ax.set_title(f'{i}',fontsize=10,color=MUT,pad=3)
fig.text(0.41,0.215,'4 more screens, and the app changes',ha='center',fontsize=11,color=MUT)
fig.text(0.41,0.775,'gap = 7 screens',ha='center',fontsize=13,color=INK,fontweight='bold')
fig.add_artist(FancyArrowPatch((0.245,0.50),(0.272,0.50),transform=fig.transFigure,
               arrowstyle='-|>',mutation_scale=16,color=MUT,lw=1.6))
fig.add_artist(FancyArrowPatch((0.655,0.50),(0.687,0.50),transform=fig.transFigure,
               arrowstyle='-|>',mutation_scale=16,color=MUT,lw=1.6))

# --- need screen (big, right) ---
axR=fig.add_axes([0.695,0.10,0.20,0.74]); shot(axR,NEED)
axR.set_title(f'Screen {NEED}   a chat app',fontsize=12,color=INK,pad=7)
fig.text(0.795,0.055,'must type "Electronic Study" now\nit is nowhere on this screen',
         ha='center',fontsize=11,color=INK,fontweight='bold',linespacing=1.3)

# --- right-hand caption ---
fig.text(0.915,0.70,'The task:',fontsize=12,color=MUT)
fig.text(0.915,0.645,'"Listen to an album of\nElectronic style, then\nshare the name of\nthe album."',
         fontsize=12.5,color=INK,linespacing=1.45,va='top')
fig.text(0.915,0.40,'The screen that held\nthe answer is gone.',fontsize=12.5,color=RED,
         fontweight='bold',linespacing=1.4,va='top')
fig.text(0.915,0.27,'Which earlier screen\nshould it re-read?',fontsize=13.5,color=INK,
         fontweight='bold',linespacing=1.4,va='top')
fig.savefig('/mnt/share/mwang49/guiodyssey/slides/figures/problem.png',dpi=145,
            bbox_inches='tight',facecolor='white')
print('problem.png saved')
