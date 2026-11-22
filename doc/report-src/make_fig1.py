"""Figure 1: the verifier both mines a delayed information need and labels every earlier screen."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK,INK2,GRID='#0b0b0b','#52514e','#d8d7d2'
BLUE,ORANGE,GREEN='#2a78d6','#eb6834','#1baf7a'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(7.0,3.5)); ax.set_xlim(0,100); ax.set_ylim(0,50); ax.axis('off')

def box(x,y,w,h,txt,fc='#ffffff',ec=GRID,tc=INK,fs=6.4,lw=0.9,bold=False,r=1.4):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc,ec=ec,lw=lw,zorder=2))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,color=tc,zorder=3,
            fontweight='bold' if bold else 'normal',linespacing=1.45)
def arrow(x1,y1,x2,y2,c=INK2,lw=1.0,style='-|>'):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=7,
                                 color=c,lw=lw,zorder=1,shrinkA=1,shrinkB=1))

# ---------- row 1: trajectory ----------
ax.text(0,47.3,'A trajectory of screens, each with its OCR text',fontsize=7.4,color=INK,fontweight='bold')
xs=[1,17,33,49,65,81]; W=14
names=['screen 0','screen 1\n(source)','screen 2','…','screen t−1','screen t\n(now)']
for i,(x,nm) in enumerate(zip(xs,names)):
    src,cur=(i==1),(i==5)
    box(x,38,W,7.2,nm,fc='#fdf0e9' if src else ('#eaf2fc' if cur else '#ffffff'),
        ec=ORANGE if src else (BLUE if cur else GRID),lw=1.4 if (src or cur) else 0.9,
        fs=6.2,bold=src or cur)
    if i<5: arrow(x+W,41.6,xs[i+1],41.6,c=GRID,lw=0.9)
ax.text(24,36.0,'shows "vanilla extract"',fontsize=6.0,color=ORANGE,ha='center',style='italic')
ax.text(88,36.0,'must type it now',fontsize=6.0,color=BLUE,ha='center',style='italic')

# ---------- row 2: verifier (left) -> labels (right) ----------
box(1,24.5,44,8.0,'Verifier: one substring test per screen\ntyped text ∈ OCR(earlier)  and  ∉ OCR(now)',
    fc='#f5f5f3',ec=INK2,fs=6.3,lw=1.0)
arrow(23,38,23,32.5,c=INK2)
arrow(45,28.5,57,28.5,c=INK2,lw=1.1)
ax.text(51,29.8,'labels every\nearlier screen',fontsize=5.8,color=INK2,ha='center',linespacing=1.3)
for x,lab in zip([59,69,79,89],['0','1','0','0']):
    pos=(lab=='1'); c=ORANGE if pos else INK2
    box(x,25.0,8,7.0,lab,fc='#fdf0e9' if pos else '#ffffff',ec=c,tc=c,fs=8.4,bold=True,lw=1.3,r=1.0)
ax.text(78,34.0,'free training labels: no human looks at any of them',fontsize=6.4,
        color=INK,ha='center',fontweight='bold')

# ---------- row 3: two instantiations + read stage ----------
box(1,8.0,30,9.0,'Per-screen scorer   (7B + LoRA)\nsees ONE earlier screen at a time\n→ P(Yes), argmax over screens',
    fc='#eefaf5',ec=GREEN,fs=6.3,lw=1.3)
box(35,8.0,30,9.0,'Full-history reader   (7B + LoRA)\nsees ALL earlier screens at once\n→ emits the screen number',
    fc='#fdf0e9',ec=ORANGE,fs=6.3,lw=1.3)
box(69,8.0,30,9.0,'Read stage   (14B, shared prompt)\nfull history + chosen screen marked\n→ the text to type',
    fc='#ffffff',ec=INK2,fs=6.3,lw=1.0)
arrow(63,25.0,20,17.0,c=GREEN,lw=1.1)
arrow(79,25.0,52,17.0,c=ORANGE,lw=1.1)
ax.text(16,18.0,'2,861 labelled decisions',fontsize=6.0,color=GREEN,ha='center')
ax.text(50,18.0,'188 labelled decisions',fontsize=6.0,color=ORANGE,ha='center')
arrow(31,12.5,35,12.5,c=GRID,lw=0.9,style='-')
arrow(65,12.5,69,12.5,c=INK2,lw=1.1)
ax.text(33,13.6,'or',fontsize=6.0,color=INK2,ha='center')
ax.text(0,3.6,'Both instantiations learn the same thing from the same labels. They differ in how the history reaches the model,',
        fontsize=6.6,color=INK2)
ax.text(0,1.0,'and therefore in how many decisions one label set yields.',fontsize=6.6,color=INK2)
fig.savefig('/mnt/share/mwang49/guiodyssey/report/figures/fig1_method.pdf',bbox_inches='tight')
fig.savefig('/mnt/share/mwang49/guiodyssey/report/figures/fig1_method.png',dpi=170,bbox_inches='tight')
print('fig1 saved')
