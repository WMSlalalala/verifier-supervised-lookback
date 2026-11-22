import sys; sys.path.insert(0,'.')
from deck import *
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
p=deck(); N=[0]
def S(t=None,sub=None):
    N[0]+=1; s=blank(p); footer(s,N[0])
    if t: title(s,t,sub)
    return s
def card(s,x,y,w,h,head,body,hc=RED,fill=LT,bs=14,hs=15):
    box(s,x,y,w,h,fill=fill)
    f=tb(s,x+0.28,y+0.26,w-0.56,h-0.5)
    para(f,head,size=hs,bold=True,color=hc,first=True,space_after=10)
    if isinstance(body,str): body=[(body,{})]
    for t,o in body: para(f,t,size=o.get('size',bs),color=o.get('color',BLACK),
                          bold=o.get('bold',False),italic=o.get('italic',False),space_after=o.get('sa',8))
def bl(s,x,y,w,items,size=16,gap=7):
    f=tb(s,x,y,w,0.4*len(items)+0.3)
    for i,t in enumerate(items):
        if isinstance(t,str): para(f,t,size=size,bullet=True,first=(i==0),space_after=gap)
        else: para(f,t[0],size=t[1].get('size',size),color=t[1].get('color',BLACK),
                   bold=t[1].get('bold',False),bullet=True,first=(i==0),space_after=gap)
def stat(s,x,y,w,big,small,color=RED,bigsize=40):
    f=tb(s,x,y,w,0.75); para(f,big,size=bigsize,bold=True,color=color,first=True,space_after=2,align=PP_ALIGN.CENTER)
    g=tb(s,x,y+0.72,w,0.6); para(g,small,size=13,color=MUT,first=True,space_after=0,align=PP_ALIGN.CENTER)

# ========== 1 TITLE ==========
s=redslide(p,'Verifier-Supervised Look-Back',[
 ('Label-Free Screen Retrieval for Delayed Information Needs in Mobile GUI Agents',{'size':19,'sa':26}),
 ('Mingshuo Wang',{'size':17,'bold':True,'sa':4}),
 ('North Carolina State University',{'size':14,'color':C(0xF2,0xC9,0xC9),'sa':20}),
 ('github.com/WMSlalalala/verifier-supervised-lookback',{'size':12,'color':C(0xF2,0xC9,0xC9)})]); N[0]+=1
notes(s,'A phone agent often has to type something it saw many screens ago. This talk is about teaching it which screen to re-read, without anyone labelling data.')

# ========== 2 OUTLINE ==========
s=S('What this talk is about')
for i,(n,t) in enumerate([('1','A failure mode in long phone-agent tasks that current benchmarks cannot show'),
 ('2','Why the two obvious fixes are both stuck at the prompting stage'),
 ('3','The idea: the test that finds the problem also labels it, for free'),
 ('4','What that supervision buys, and what it does not'),
 ('5','Two evaluation traps that changed my conclusions more than any method did')]):
    y=1.60+i*0.86; hot=(i==2); c=box(s,0.50,y,0.48,0.48,fill=RED if hot else LT)
    f=c.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,n,size=15,bold=True,color=WHITE if hot else MUT,first=True,space_after=0,align=PP_ALIGN.CENTER)
    g=tb(s,1.18,y-0.05,6.9,0.60,MSO_ANCHOR.MIDDLE); para(g,t,size=15,bold=hot,first=True,space_after=0)
card(s,8.60,1.60,4.25,2.45,'The one-line summary',
 'Training beats architecture here. The free labels lift both designs I tried, and which design wins is not statistically separable.')
notes(s,'Five parts. The third is the actual idea; the last is the part most worth your attention.')

# ========== 3 BACKGROUND ==========
s=S('Background: what a phone GUI agent does')
f=tb(s,0.45,1.45,6.6,0.35); para(f,'Input at every step',size=16,bold=True,first=True,space_after=0)
bl(s,0.70,1.93,6.4,['the task, written in plain English','one screen — here, its OCR text','the actions it has taken so far'])
f=tb(s,0.45,3.60,6.6,0.4); para(f,[('Output: one action — ',{}),('tap, scroll, or type.',{'bold':True,'color':RED})],size=16,first=True,space_after=0)
f=tb(s,0.45,4.10,6.6,0.4); para(f,'The screen changes, and the same policy runs again.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.80,6.6,1.0); para(f,'A long cross-app task runs 15–30 screens. My setting is offline: the trajectory is given, and the agent must produce the action at one chosen step.',size=14,color=MUT,first=True,space_after=0)
for i,(txt,fill,col) in enumerate([('screen t',LT,MUT),('the agent picks an action',RED,WHITE),('screen t + 1',LT,MUT)]):
    y=1.80+i*1.30; b=box(s,8.45,y,3.40,0.85,fill=fill)
    f=b.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,txt,size=14,bold=(i==1),color=col,first=True,space_after=0,align=PP_ALIGN.CENTER)
    if i<2:
        a=s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW,I(10.05),I(y+0.88),I(0.20),I(0.38))
        a.fill.solid(); a.fill.fore_color.rgb=GRAY; a.line.fill.background(); a.shadow.inherit=False
f=tb(s,8.45,5.55,3.40,0.4); para(f,'…and the loop repeats',size=13,color=MUT,first=True,space_after=0,align=PP_ALIGN.CENTER)
notes(s,'Nothing exotic: one screen in, one action out, repeat. The thing to hold on to is that the agent sees one screen at a time.')

# ========== 4 PROBLEM ==========
s=S('The failure mode: the answer left the screen long ago')
img(s,'problem.png',0.30,1.45,12.73)
notes(s,'A real trajectory from GUI-Odyssey. Screen 6 is a music app search result; "Electronic Study" is the fifth of 42 items. Screen 11 is a chat app with the keyboard up. Seven screens apart, and the app changed in between.')

# ========== 5 DEFINITION ==========
s=S('Why this one step decides the whole task')
f=tb(s,0.45,1.50,7.3,0.6); para(f,[('A ',{}),('delayed information need',{'bold':True,'color':RED}),(' is a step where the text the agent must type',{})],size=16,first=True,space_after=0)
bl(s,0.70,2.20,7.0,['appeared verbatim on an earlier screen, and','does not appear on the current one'])
f=tb(s,0.45,3.45,7.3,0.8); para(f,'It cannot be guessed from the task description: "share the name of the album" does not say which album.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.40,7.3,0.6); para(f,'Get it wrong and the task fails, however good the rest of the policy is.',size=16,bold=True,first=True,space_after=0)
card(s,8.25,1.60,4.60,3.10,'Why the second clause matters',[
 ('If the text is also on the current screen, the agent can copy it and needs no memory at all.',{'sa':10}),
 ('Dropping this clause silently broke my first round of experiments — slide 26.',{'size':13,'color':MUT,'italic':True})])
notes(s,'The second clause matters later. If the answer is also on the current screen, there is no memory problem to solve.')

# ========== 6 PREVALENCE ==========
s=S('How often does it happen? The usual benchmarks say never')
table(s,[['','tasks','steps','avg. length','delayed needs found'],
 ['AITZ','2,504','18,643','7.4 screens',('0',{'color':MUT,'bold':True})],
 ['GUI-Odyssey (all)','7,735','118,791','15.4 screens',('not mined',{'color':MUT})],
 ['   my sample, full OCR','273','4,338','15.9 screens',('89 steps  (2.05%)',{'color':RED,'bold':True})]],
 0.45,1.55,12.4,colw=[I(3.4),I(1.5),I(1.8),I(2.2),I(3.5)],fs=13,head_fs=12,row_h=0.42)
stat(s,0.70,3.65,3.0,'31%','of sampled tasks contain at least one')
stat(s,4.30,3.65,3.0,'5','screens is the median gap; the max is 27',color=INDIGO)
stat(s,7.90,3.65,3.0,'56%','of gaps are 5 screens or more',color=INDIGO)
f=tb(s,0.70,5.45,11.4,0.9)
para(f,'A short benchmark cannot contain the problem: the task ends before a gap can open.',size=15,first=True,space_after=0)
notes(s,'AITZ is the benchmark most of this area uses. Its tasks average 7.4 steps, so it contains zero of these cases. The problem is real but invisible to the standard evaluation.')

# ========== 7 NEEDLE ==========
s=S('And the answer is not the salient thing on its screen')
f=tb(s,0.45,1.55,7.0,0.6); para(f,'On its source screen, the needed string sits at',size=16,first=True,space_after=0)
bl(s,0.70,2.20,6.8,[('median rank 13 of 33 OCR elements',{'bold':True}),('never first',{'bold':True})])
f=tb(s,0.45,3.45,7.0,1.2); para(f,'So a one-line summary written as the agent goes will almost never contain it: summarising happens before anyone knows what will be needed.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.85,7.0,0.9); para(f,'This rules out the rolling-summary family of memory designs for this particular need.',size=14,color=MUT,first=True,space_after=0)
card(s,8.05,1.70,4.80,2.6,'In the running example',[
 ('"Electronic Study" is the 5th of 42 items on a search-results screen — one row among seven near-identical rows.',{})])
notes(s,'This is why writing a summary as you go does not work. At the time you write it you have no idea that this one row will matter nine screens later.')

# ========== 8 OPTION 1 ==========
s=S('Existing option 1: keep the whole history in the prompt')
f=tb(s,0.45,1.55,7.2,0.6); para(f,'Put the OCR text of every earlier screen into one call and ask for the answer.',size=16,first=True,space_after=0)
bl(s,0.70,2.30,6.9,['1,241 tokens on average; 4,584 for the longest trajectory','nothing is thrown away','one model call'])
box(s,8.20,1.70,4.65,2.5)
f=tb(s,8.48,1.96,4.1,0.35); para(f,'Finds the right screen',size=15,bold=True,color=RED,first=True,space_after=0)
kv(s,8.48,2.45,4.1,[('early in a task  (t ≤ 15)','68.0 %',BLACK),
                    ('late in a task  (t ≥ 16)','46.0 %',RED),
                    ('overall','54.8 %',BLACK)],size=14,gap=0.40)
f=tb(s,8.20,4.45,4.65,0.8); para(f,'It degrades exactly where long tasks need it.',size=14,color=MUT,first=True,space_after=0)
notes(s,'The simplest thing that could work. It is also the strongest prompted baseline, and it is the one everyone compares against.')

# ========== 9 OPTION 2 ==========
s=S('Existing option 2: a one-line index per screen')
f=tb(s,0.45,1.55,7.2,0.7); para(f,'The gist-and-lookup design from long-document reading (ReadAgent), applied to screens:',size=16,first=True,space_after=0)
for i,t in enumerate(['a writer model writes ≤32 tokens per screen','the reader picks one line','that screen is re-read in full']):
    y=2.35+i*0.52; c=box(s,0.70,y,0.36,0.36,fill=LT)
    f=c.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,str(i+1),size=12,bold=True,color=MUT,first=True,space_after=0,align=PP_ALIGN.CENTER)
    g=tb(s,1.22,y-0.02,6.3,0.42,MSO_ANCHOR.MIDDLE); para(g,t,size=15,first=True,space_after=0)
f=tb(s,0.45,4.10,7.2,0.8); para(f,'Cheap, and nothing is lost: the full screen is still available later.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.85,7.2,0.6); para(f,'This is the design I started the project believing in.',size=14,color=MUT,italic=True,first=True,space_after=0)
box(s,8.20,1.70,4.65,1.9)
f=tb(s,8.48,1.96,4.1,0.35); para(f,'Finds the right screen',size=15,bold=True,color=RED,first=True,space_after=0)
kv(s,8.48,2.45,4.1,[('screen index','41.0 %',RED),('full history','54.8 %',BLACK)],size=14,gap=0.40)
f=tb(s,8.20,3.85,4.65,1.4); para(f,'It is worse than just keeping everything, and slide 25 shows that no amount of rewriting the lines fixes it.',size=14,first=True,space_after=0)
notes(s,'I built this first. It is the obvious design if you have read the long-context literature. It loses, and the negative result is on slide 25.')

# ========== 10 THE WALL ==========
s=S('The wall: both are prompted, and training needs labels')
for i,(t,sub,fill,col) in enumerate([('full history','prompted',LT,MUT),('screen index','prompted',LT,MUT)]):
    x=0.45+i*3.35; b=box(s,x,1.80,3.10,1.15,fill=fill)
    f=b.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,t,size=16,bold=True,first=True,space_after=3,align=PP_ALIGN.CENTER)
    para(f,sub,size=13,color=col,align=PP_ALIGN.CENTER,space_after=0)
a=s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,I(7.05),I(2.22),I(0.55),I(0.30))
a.fill.solid(); a.fill.fore_color.rgb=RED; a.line.fill.background(); a.shadow.inherit=False
b=box(s,7.85,1.80,3.10,1.15,fill=PINK,line=RED)
f=b.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
para(f,'trained look-back',size=16,bold=True,color=RED,first=True,space_after=3,align=PP_ALIGN.CENTER)
para(f,'needs labelled examples',size=13,color=MUT,align=PP_ALIGN.CENTER,space_after=0)
f=tb(s,0.45,3.55,6.0,1.4); para(f,'To train either design, somebody has to say which earlier screen was the right one — for every step of every trajectory.',size=16,first=True,space_after=0)
card(s,6.95,3.45,5.90,1.75,'The going rate',[
 ('PAL-UI, the one trained look-back agent I know of, paid for 8,600 hand-written step-level instructions to get that signal.',{})])
notes(s,'This is the gap the project is about. Everyone prompts, because the labels are expensive. PAL-UI is the exception and it shows what the exception costs.')

# ========== 11 THE IDEA ==========
s=S('The idea: the labels are already there')
img(s,'idea.png',0.65,1.50,12.0)
notes(s,'Same trajectory as before. The verifier I need anyway to mine the case also tells me, for every earlier screen, whether it holds the answer. That column of zeros and a one is a free training label.')

# ========== 12 CONTRIBUTIONS ==========
s=S('Contributions')
items=[('Problem and labels','I define the delayed information need, build an automatic verifier that both mines and labels it, and measure how common it is: absent from AITZ, present in 31% of sampled GUI-Odyssey tasks.'),
 ('Method','Verifier-supervised look-back: training a look-back policy on labels the verifier produces for free, with two instantiations that share one objective.'),
 ('Finding','The supervision is the lever, not the architecture. It lifts a one-call reader by 10.6 points and a per-screen scorer by 22.3; the two are not separable (p = 0.086), and the decomposition gain is confined to 8–12 screens back (p = 0.003).'),
 ('Validation and honesty','An external sample confirms the margin; ablations show the design is insensitive to its settings; and I report two evaluation filters whose absence changed my conclusions — including one result I had to retract.')]
for i,(h,b) in enumerate(items):
    y=1.50+i*1.32; c=box(s,0.50,y,0.42,0.42,fill=RED)
    f=c.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,str(i+1),size=13,bold=True,color=WHITE,first=True,space_after=0,align=PP_ALIGN.CENTER)
    g=tb(s,1.12,y-0.04,11.7,1.2)
    para(g,h,size=15,bold=True,color=RED,first=True,space_after=4)
    para(g,b,size=14,space_after=0)
notes(s,'Four contributions. The fourth one — reporting what I had to retract — is the one I would defend hardest; it is why I trust the other three.')
# ========== 13 VERIFIER ==========
s=S('The verifier, precisely')
f=tb(s,0.45,1.50,7.2,0.5); para(f,'To mine a case at step t, I already need a test:',size=16,first=True,space_after=0)
box(s,0.60,2.10,7.0,1.15,fill=LT)
f=tb(s,0.85,2.32,6.5,0.8)
para(f,'typed text  ∈  OCR(screen i)   for some i < t',size=15,bold=True,first=True,space_after=6,align=PP_ALIGN.CENTER)
para(f,'and   typed text  ∉  OCR(screen t)',size=15,bold=True,color=RED,space_after=0,align=PP_ALIGN.CENTER)
f=tb(s,0.45,3.50,7.2,1.1); para(f,'Run the same test on every earlier screen instead of stopping at the first hit, and it returns the set of screens that contain the answer.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.75,7.2,0.8); para(f,'That set is the label: screen i is positive if and only if it is in the set.',size=16,bold=True,first=True,space_after=0)
card(s,8.15,1.55,4.70,1.6,'What this costs',[('one substring test per screen',{'bold':True,'sa':6}),
 ('no annotator, no model in the loop, no heuristic',{'size':13,'color':MUT})])
card(s,8.15,3.52,4.70,2.1,'What it does not cover',[('only verbatim re-typing',{'bold':True,'sa':6}),
 ('Visual attributes, comparisons and aggregates are out of scope — so all my counts are a lower bound.',{'size':13,'color':MUT})])
notes(s,'The whole idea is in this slide. The test is not a proxy or a heuristic: it is exactly the definition of the problem, applied to every screen instead of one.')

# ========== 14 FUNNEL ==========
s=S('Building the dataset: the mining funnel')
stages=[('431','string candidates',LT,MUT),('127','pass the OCR check',LT,MUT),('91','verified cases',LT,MUT),('85','the short set',PINK,RED)]
for i,(n,lab,fill,col) in enumerate(stages):
    x=0.60+i*3.12; b=box(s,x,1.55,2.70,1.0,fill=fill,line=RED if i==3 else None)
    f=b.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,n,size=22,bold=True,color=col,first=True,space_after=2,align=PP_ALIGN.CENTER)
    para(f,lab,size=12,color=MUT,space_after=0,align=PP_ALIGN.CENTER)
    if i<3:
        a=s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,I(x+2.76),I(1.95),I(0.30),I(0.20))
        a.fill.solid(); a.fill.fore_color.rgb=GRAY; a.line.fill.background(); a.shadow.inherit=False
for i,t in enumerate(['','269 fail (mostly OCR misreads)\n35 have no OCR output','− 36  answer also on\nthe current screen','− 6  answer in the\ntask instructions']):
    if not t: continue
    f=tb(s,0.60+i*3.12,2.62,2.70,0.8)
    for k,line in enumerate(t.split('\n')): para(f,line,size=11,color=MUT,first=(k==0),space_after=2,align=PP_ALIGN.CENTER)
f=tb(s,0.60,3.80,6.1,0.4); para(f,'Four independent samples of trajectories',size=16,bold=True,first=True,space_after=0)
table(s,[['set','cases','note'],['short','85','median step 11'],['long','53','t ≥ 16'],['late-mined','50','t ≥ 16'],
 [('external',{'color':RED,'bold':True}),('93',{'color':RED,'bold':True}),('frozen-design holdout',{'color':RED,'bold':True})]],
 0.60,4.30,6.1,colw=[I(1.9),I(1.3),I(2.9)],fs=12,head_fs=11,row_h=0.34)
card(s,7.30,3.95,5.55,2.0,'How they are used',[
 ('The first three — 188 cases in 170 trajectories — carry all training and cross-validation.',{'sa':8}),
 ('The external set is touched once, at the very end.',{'bold':True})])
notes(s,'431 raw candidates down to 85 clean ones. The two subtractions in the middle are the two evaluation traps I will come back to.')

# ========== 15 METHOD 1 ==========
s=S('Method 1: the per-screen scorer')
f=tb(s,0.45,1.50,7.0,0.45); para(f,'One call per earlier screen. The prompt holds',size=16,first=True,space_after=0)
bl(s,0.70,2.00,6.6,['the task','the current screen’s OCR text',('one earlier screen’s OCR text',{'bold':True}),'the distance t − i'],size=15,gap=5)
f=tb(s,0.45,4.00,7.0,0.45); para(f,[('and ends with  ',{}),('"Answer Yes or No".',{'bold':True,'font':'Courier New','size':14})],size=15,first=True,space_after=0)
f=tb(s,0.45,4.55,7.0,1.0); para(f,'I take the logits of Yes and No at the answer position, softmax over those two, and train with cross-entropy, positives weighted 3 : 1.',size=15,first=True,space_after=0)
f=tb(s,0.45,5.65,7.0,0.8); para(f,'Localization = argmax over screens. No generation: t forward passes of 600–900 tokens.',size=14,color=MUT,first=True,space_after=0)
box(s,8.00,1.55,4.85,3.55,fill=LT)
f=tb(s,8.30,1.80,4.3,0.35); para(f,'Configuration',size=15,bold=True,color=RED,first=True,space_after=0)
table(s,[['base','Qwen2.5-7B-Instruct'],['adapter','LoRA r = 16, q/k/v/o'],['trainable','40 M params'],['epochs','2'],
 ['learning rate','1e−4'],['batch','4 items / update'],['cost','13–27 min / fold']],
 8.30,2.28,4.25,colw=[I(1.65),I(2.60)],fs=12,head_fs=12,row_h=0.36)
f=tb(s,8.00,5.35,4.85,0.8); para(f,'188 cases → 2,861 labelled decisions, 463 of them positive.',size=14,bold=True,first=True,space_after=0)
notes(s,'One screen per call. The output is a probability, not a choice, so the history length only changes how many probabilities I compute.')

# ========== 16 METHOD 2 ==========
s=S('Method 2: the control I should have run first')
f=tb(s,0.45,1.55,7.2,0.7); para(f,'Same base model, same adapter, same labels — but the history arrives all at once.',size=16,first=True,space_after=0)
f=tb(s,0.45,2.40,7.2,1.0); para(f,'The prompt holds the task and every earlier screen; the target is the screen number, with the loss on that number only.',size=16,first=True,space_after=0)
f=tb(s,0.45,3.55,7.2,0.5); para(f,'Localization is one greedy generation of ≤ 5 tokens.',size=16,first=True,space_after=0)
f=tb(s,0.45,4.30,7.2,1.3); para(f,'Without this control, any gain I measured could have been the training rather than the architecture. It turned out to be exactly that.',size=15,color=MUT,italic=True,first=True,space_after=0)
box(s,8.15,1.70,4.70,2.7)
f=tb(s,8.43,1.96,4.1,0.35); para(f,'The only difference',size=15,bold=True,color=RED,first=True,space_after=0)
f=tb(s,8.43,2.42,4.1,0.3); para(f,'training examples from the same 188 cases',size=12,color=MUT,first=True,space_after=0)
kv(s,8.43,2.78,4.1,[('per-screen scorer','2,861',RED),('full-history reader','188',AQUA)],size=14,gap=0.38)
f=tb(s,8.43,3.62,4.1,0.7); para(f,'One case becomes t items for the scorer and a single item for the reader.',size=13,color=MUT,first=True,space_after=0)
notes(s,'This is the slide I would put first if I gave the talk again. Running this control is what changed the paper.')

# ========== 17 READ STAGE ==========
s=S('The second stage: turning a screen choice into typed text')
f=tb(s,0.45,1.50,12.4,0.5); para(f,'A 14B reader produces the final text, with the prompt shared by every condition.',size=16,first=True,space_after=0)
card(s,0.60,2.20,5.9,2.5,'Single-screen read',[
 ('task + current screen + the chosen screen only',{'bold':True,'sa':10}),
 ('Cheap, but it throws away the task state: which fields are filled, which app we are in.',{'size':13,'color':MUT})],hc=INDIGO)
card(s,6.85,2.20,5.9,2.5,'Read with history',[
 ('task + current screen + all earlier screens, with the chosen screen repeated and marked',{'bold':True,'sa':10}),
 ('Costs full history’s context plus one repeated screen.',{'size':13,'color':MUT})],hc=RED)
f=tb(s,0.60,5.05,12.2,0.6); para(f,'Slide 24 shows how much of the gain is the marking and how much is choosing the right screen.',size=14,color=MUT,first=True,space_after=0)
notes(s,'Two readers because the first one lost information I did not expect it to need. The controls on slide 24 separate the two effects.')

# ========== 18 SETUP ==========
s=S('Experimental setup')
card(s,0.50,1.50,6.0,1.75,'Cross-validation',[('5 folds over the 188 cases, grouped by trajectory so no trajectory appears in both train and test. I pool the five scored folds.',{'size':14})])
card(s,0.50,3.60,6.0,1.35,'External set',[('Train once on all 188, evaluate once on the 93 held-out cases.',{'size':14})])
card(s,0.50,5.27,6.0,1.45,'Statistics',[('Every comparison is paired on the same cases and tested with McNemar; I report the net cases that flip and the two-sided p.',{'size':14})])
f=tb(s,6.85,1.55,6.0,0.4); para(f,'Two metrics',size=16,bold=True,first=True,space_after=0)
card(s,6.85,2.05,6.0,1.5,'Localization',[('the named screen is any screen whose OCR contains the answer',{'size':14})],hc=INDIGO)
card(s,6.85,3.90,6.0,1.5,'End-to-end',[('the produced text contains the answer, normalised as in mining',{'size':14})],hc=INDIGO)
f=tb(s,6.85,5.72,6.0,1.0); para(f,'"Any valid screen" rather than "the earliest one" — slide 26 explains why that choice is worth 11–15 points on its own.',size=13,color=MUT,first=True,space_after=0)
notes(s,'Grouping folds by trajectory matters: two cases from the same trajectory share screens, so splitting them across train and test would leak.')
# ========== 19 MAIN FIGURE ==========
s=S('Main result: the free labels lift both architectures')
img(s,'labels_buy.png',1.55,1.55,10.2)
f=tb(s,0.80,5.70,5.6,0.8); para(f,'Training is worth 10.6 and 22.3 points',size=15,bold=True,first=True,space_after=3,align=PP_ALIGN.CENTER)
para(f,'p = 0.019 and p < 0.001',size=13,color=MUT,align=PP_ALIGN.CENTER,space_after=0)
f=tb(s,6.90,5.70,5.6,0.8); para(f,'Which architecture wins is not separable',size=15,bold=True,first=True,space_after=3,align=PP_ALIGN.CENTER)
para(f,'72.3 vs 65.4, net +13 cases, p = 0.086',size=13,color=MUT,align=PP_ALIGN.CENTER,space_after=0)
notes(s,'Two dumbbells. Open circle is prompted, filled is trained on the free labels. Both move a long way right. The red one moves further, but not by enough to call it.')

# ========== 20 MAIN TABLE ==========
s=S('The full picture, 188 cross-validated cases')
hdr={'fill':LT,'bold':True}
table(s,[['','condition','loc all','loc t≤15','loc t≥16','e2e all','e2e t≥16','vs scorer'],
 ['prompted','full history','54.8','68.0','46.0','31.4','20.4','+33,  <0.001'],
 ['','screen index','41.0','48.0','36.3','23.9','25.7','+59,  <0.001'],
 ['','per-screen scorer','50.0','68.0','38.1','35.1','30.1','+42,  <0.001'],
 [('trained',{'bold':True}),'full history','65.4','76.0','58.4','42.6','39.8','+13,  0.086'],
 ['',('per-screen scorer',{'bold':True,'color':RED}),('72.3',{'bold':True,'color':RED}),('80.0',{'bold':True,'color':RED}),
  ('67.3',{'bold':True,'color':RED}),('44.7',{'bold':True,'color':RED}),('42.5',{'bold':True,'color':RED}),'']],
 0.45,1.60,12.4,colw=[I(1.25),I(2.55),I(1.25),I(1.35),I(1.35),I(1.3),I(1.35),I(2.0)],fs=13,head_fs=11,row_h=0.44)
f=tb(s,0.60,4.80,5.9,1.0); para(f,'Prompting the scorer is worse than prompting full history (50.0 vs 54.8). Training reverses the order.',size=14,first=True,space_after=0)
f=tb(s,7.00,4.80,5.8,1.0); para(f,'End-to-end, supervision is worth 9.6 and 11.2 points; the architecture adds 2.1 (p = 0.45).',size=14,first=True,space_after=0)
f=tb(s,0.60,5.95,12.2,0.5); para(f,'n = 188 / 75 / 113 for the three localization columns.',size=12,color=MUT,first=True,space_after=0)
notes(s,'Read the two trained rows against the prompted row directly above each. Both gains are large; the difference between the two trained rows is not.')

# ========== 21 BY GAP ==========
s=S('Where the per-screen decomposition actually pays')
img(s,'by_gap.png',1.45,1.50,10.4)
f=tb(s,0.80,5.70,5.6,0.8); para(f,'8–12 screens back: 78.2 vs 56.4',size=15,bold=True,color=RED,first=True,space_after=3,align=PP_ALIGN.CENTER)
para(f,'net +12 cases, p = 0.003',size=13,color=MUT,align=PP_ALIGN.CENTER,space_after=0)
f=tb(s,6.90,5.70,5.6,0.8); para(f,'13+ screens back: both trained models lose',size=15,bold=True,first=True,space_after=3,align=PP_ALIGN.CENTER)
para(f,'64.5 prompted vs 41.9 and 51.6 trained',size=13,color=MUT,align=PP_ALIGN.CENTER,space_after=0)
notes(s,'One band, and only one, where scoring screens separately beats reading them together. That is where a single call has a dozen look-alike candidates to weigh at once.')

# ========== 22 EXTERNAL ==========
s=S('Checked once on data no design decision ever saw')
img(s,'external.png',0.55,1.60,6.6)
f=tb(s,7.55,1.65,5.3,1.0); para(f,'93 cases from a fourth batch of 400 trajectories, mined after every design decision was frozen, evaluated once.',size=15,first=True,space_after=0)
box(s,7.55,2.85,5.3,2.3)
f=tb(s,7.83,3.08,4.7,0.35); para(f,'End-to-end, read with history',size=15,bold=True,color=RED,first=True,space_after=0)
kv(s,7.83,3.55,4.7,[('prompted full history','23.7 %',BLACK),('trained full history','51.6 %',AQUA),
                    ('trained scorer','49.5 %',RED),('scorer, single-screen read','37.6 %',MUT)],size=13,gap=0.36)
f=tb(s,7.55,5.35,5.3,1.0); para(f,'Same story out of sample: supervision +26 points, architecture indistinguishable (p = 0.62).',size=14,color=MUT,first=True,space_after=0)
notes(s,'This is the slide that matters for whether you believe the rest. Mined after everything was frozen, evaluated once, and it reproduces the in-fold conclusion exactly.')

# ========== 23 ABLATIONS ==========
s=S('Ablations: the design is insensitive to its settings')
table(s,[['scorer variant','loc','p'],
 [('full scorer',{'bold':True}),('72.3',{'bold':True}),''],
 ['no distance in the prompt','70.7','0.61'],['positive weight 1 (not 3)','72.3','0.77'],
 ['3B base (not 7B)','68.1','0.22'],[('   3B at t ≥ 20',{'color':MUT}),('48.1',{'bold':True,'color':RED}),('vs 37.0',{'color':MUT})]],
 0.50,1.60,6.0,colw=[I(3.5),I(1.3),I(1.2)],fs=12,head_fs=11,row_h=0.38)
table(s,[['read stage: which screen is marked','e2e','p'],
 ['gold source screen  (ceiling)','45.2','1.00'],
 [('the scorer’s choice',{'bold':True,'color':RED}),('44.7',{'bold':True,'color':RED}),''],
 ['the scorer’s top two','45.2','1.00'],['the most recent screen','38.8','0.10'],
 ['a random earlier screen','36.7',('0.018',{'color':RED,'bold':True})]],
 6.80,1.60,6.0,colw=[I(3.7),I(1.2),I(1.1)],fs=12,head_fs=11,row_h=0.38)
f=tb(s,0.50,4.25,6.0,1.3); para(f,'Nothing I tuned mattered much — which is consistent with the labels, not the recipe, doing the work.',size=14,color=MUT,first=True,space_after=0)
f=tb(s,6.80,4.25,6.0,1.9); para(f,'Repeating any screen is worth 5–7 of the 13 points over prompted full history; choosing the right one is worth the rest. The scorer already sits at this reader’s ceiling.',size=14,color=MUT,first=True,space_after=0)
notes(s,'Left: the method does not depend on my hyperparameters. Right: the gain is not just "put a screen in twice" — a random screen gets you about half of it.')

# ========== 24 INDEX NEGATIVE ==========
s=S('The negative result: why the index route is closed')
table(s,[['condition','loc %'],['no history','e2e 2.4'],['full history, prompted','65.9'],['per-screen summary','23.5'],
 ['screen index, prompt-only','49.4'],['BM25  (task + current screen)','10.6'],['BM25  (gold text as query)','92.9'],
 [('per-screen scorer',{'bold':True,'color':RED}),('77.6',{'bold':True,'color':RED})]],
 0.50,1.60,6.0,colw=[I(4.5),I(1.5)],fs=12,head_fs=11,row_h=0.36)
table(s,[['writer variant / oracle','loc %'],['trained with DPO  (on its own test cases)','45.9'],
 ['forced two-field format','47.1'],['values allowed in the line','49.4'],['three lines per screen','43.5'],
 ['retrieval prompt, every screen','44.7'],[('oracle: best single line',{'color':MUT}),('58.8–65.9',{'color':MUT})],
 [('oracle: best of five per case',{'color':MUT}),('76.5',{'color':MUT})]],
 6.80,1.60,6.0,colw=[I(4.5),I(1.5)],fs=12,head_fs=11,row_h=0.36)
f=tb(s,0.50,4.60,6.0,1.1); para(f,'Five ways of training or re-prompting the writer: none passes plain full history.',size=14,first=True,space_after=0)
f=tb(s,6.80,4.60,6.0,1.5); para(f,'An oracle that hand-picks the best line reaches full-history level and no higher — the ceiling is the screen itself, not the writing.',size=14,first=True,space_after=0)
notes(s,'I spent most of the project here. Worth saying out loud: the oracle row is what convinced me to stop. If a perfect line-picker only ties full history, better writing cannot win.')
# ========== 25 TRAP 1 ==========
s=S('Trap 1: scoring only the earliest matching screen')
f=tb(s,0.45,1.55,7.2,1.0); para(f,'My miner labels the earliest screen containing the answer. But a value typed once reappears — in confirmation pages, in lists, in the chat you just sent.',size=16,first=True,space_after=0)
stat(s,0.70,2.80,2.6,'47%','of short-set cases have two or more valid screens')
f=tb(s,3.70,2.90,4.0,1.2); para(f,'Scoring only the earliest one marks a reader wrong for naming a screen that does contain the answer.',size=15,first=True,space_after=0)
card(s,8.15,1.70,4.70,2.2,'Switching to "any valid screen"',[
 ('screen index          + 15.3 points',{'bold':True,'color':RED,'sa':8}),
 ('full history             + 11.8 points',{'bold':True,'color':AQUA})])
f=tb(s,8.15,4.10,4.70,1.6); para(f,'The bias is larger than every writer-training effect I measured, and it hits the two arms unequally — the index tends to name a later screen.',size=14,color=MUT,first=True,space_after=0)
notes(s,'A metric bug, not a method bug. It systematically penalised the arm I was trying to improve, which is the worst kind.')

# ========== 26 TRAP 2 ==========
s=S('Trap 2: the bug that made a bad method look great')
f=tb(s,0.45,1.55,7.0,0.45); para(f,'My first mining rule asked only:',size=16,first=True,space_after=0)
box(s,0.60,2.05,6.7,0.65,fill=LT)
f=tb(s,0.85,2.22,6.2,0.4); para(f,'is the typed text on an earlier screen?',size=15,italic=True,color=MUT,first=True,space_after=0)
f=tb(s,0.45,2.95,7.0,0.45); para(f,'It should have asked:',size=16,first=True,space_after=0)
box(s,0.60,3.45,6.7,0.65,fill=PINK,line=RED)
f=tb(s,0.85,3.62,6.2,0.4); para(f,'…and not on the current one?',size=15,bold=True,color=RED,first=True,space_after=0)
f=tb(s,0.45,4.40,7.0,1.0); para(f,'Without the second clause the answer is sitting on the current screen and the agent needs no memory at all.',size=16,first=True,space_after=0)
box(s,8.15,1.60,4.70,1.95)
f=tb(s,8.43,1.82,4.1,0.35); para(f,'Contaminated cases',size=15,bold=True,color=RED,first=True,space_after=0)
kv(s,8.43,2.28,4.1,[('short set','28 %',BLACK),('long set','58 %',RED),('long set, gap 1–2','38 of 39',MUT)],size=13,gap=0.36)
box(s,8.15,3.90,4.70,2.0)
f=tb(s,8.43,4.12,4.1,0.35); para(f,'A shortcut that "won"',size=15,bold=True,color=RED,first=True,space_after=0)
f=tb(s,8.43,4.52,4.1,0.3); para(f,'a rule that re-reads the two previous screens',size=12,color=MUT,first=True,space_after=0)
kv(s,8.43,4.90,4.1,[('on contaminated data','+ 17.3',MUT),('on clean data','− 22.7',RED)],size=13,gap=0.36)
notes(s,'This is the one I want you to remember. 58 percent of my long-task cases needed no memory at all, and a method that exploited that looked like a breakthrough.')

# ========== 27 RETRACTION ==========
s=S('What I had to retract, and what it cost')
items=[('I optimised against the wrong localization metric for two rounds of writer training (trap 1). Both rounds were null either way, so the conclusion survived — but the bias was bigger than the effect I was chasing.',MUT),
 ('I reported a gating method as a solved problem before finding trap 2. On clean data it loses by 23 points. It is in the paper as a negative result, not a method.',RED),
 ('The end-to-end numbers were the tell: localization moved from 0% to 90% on short gaps while end-to-end stayed at 28%.',MUT)]
for i,(t,col) in enumerate(items):
    y=1.60+i*1.45; c=box(s,0.50,y,0.42,0.42,fill=col)
    f=c.text_frame; f.margin_left=0;f.margin_right=0;f.margin_top=0;f.margin_bottom=0; f.vertical_anchor=MSO_ANCHOR.MIDDLE
    para(f,str(i+1),size=13,bold=True,color=WHITE,first=True,space_after=0,align=PP_ALIGN.CENTER)
    g=tb(s,1.12,y-0.05,11.7,1.3); para(g,t,size=15,first=True,space_after=0)
box(s,0.50,5.85,12.35,0.75,fill=LT)
f=tb(s,0.80,6.02,11.8,0.45); para(f,'A metric that improves while the task does not is a bug, not a result. Both filters are one line of code each.',size=14,bold=True,first=True,space_after=0,align=PP_ALIGN.CENTER)
notes(s,'I would rather show you this slide than have someone find it in the code. The third point is the general lesson: watch the metric you actually care about.')

# ========== 28 LIMITATIONS ==========
s=S('Limitations')
f=tb(s,0.50,1.50,6.0,0.4); para(f,'Where the method fails',size=16,bold=True,color=RED,first=True,space_after=0)
bl(s,0.70,1.98,5.8,[('13+ screens back: both trained models fall below prompting. Training on cases whose median gap is 5 teaches a distance prior that misfires at the tail; removing the distance feature does not fix it.',{'size':14}),
 ('t ≥ 20 (n = 27): the 7B scorer ties prompting at 37.0; the trained full-history reader gets 44.4 and a 3B scorer 48.1.',{'size':14})],gap=12)
f=tb(s,7.00,1.50,5.85,0.4); para(f,'Scope of the evidence',size=16,bold=True,color=INDIGO,first=True,space_after=0)
bl(s,7.20,1.98,5.6,[('one dataset, one OCR engine; the external set is from the same corpus',{'size':14}),
 ('training labels and the evaluation metric are the same substring check',{'size':14}),
 ('spot check of 20 cases: all labelled screens really showed the text, but in 5 the agent had typed it itself earlier — a weaker kind of need',{'size':14}),
 ('each condition is a single training run',{'size':14})],gap=10)
notes(s,'The 13+ band is the honest hole. If someone asks what I would do next, it is this: train on a gap-balanced sample and see whether the prior is really the cause.')

# ========== 29 CODE ==========
s=S('Code and how the experiments were run')
box(s,0.50,1.55,6.0,4.1,fill=LT)
f=tb(s,0.75,1.80,5.5,3.7)
code=[('# 1. mine + label  (CPU)',MUT),('python src/verify_long.py',BLACK),('python src/build_scorer_data.py',BLACK),
 ('',BLACK),('# 2. train, 5 folds by trajectory',MUT),('for f in 0 1 2 3 4; do',BLACK),
 ('  FOLD=$f python src/train_scorer.py',BLACK),('  FOLD=$f python src/train_fullhist.py',BLACK),('done',BLACK),
 ('',BLACK),('# 3. the external set',MUT),('FOLD=ext python src/train_scorer.py',BLACK)]
for i,(t,col) in enumerate(code): para(f,t if t else ' ',size=11.5,color=col,font='Courier New',first=(i==0),space_after=3)
box(s,6.85,1.55,5.95,4.1,fill=LT)
f=tb(s,7.10,1.80,5.45,3.7)
code2=[('# 4. read stage + controls',MUT),('SRC=trained HIST=1 \\',BLACK),('  python src/read_scorer.py',BLACK),
 ('MARK=gold|recent|random|top2',BLACK),('',BLACK),('# 5. every table in the report',MUT),
 ('python src/analyze_all.py',BLACK),('',BLACK),('# ablations: one env var each',MUT),
 ('NODIST=1   # drop the distance',BLACK),('POSW=1     # unweighted loss',BLACK),('MODEL=Qwen/Qwen2.5-3B-Instruct',BLACK)]
for i,(t,col) in enumerate(code2): para(f,t if t else ' ',size=11.5,color=col,font='Courier New',first=(i==0),space_after=3)
f=tb(s,0.50,5.90,12.35,0.9); para(f,'87 scripts, 112 result files, the derived OCR data, both papers, this deck and the full experiment log — including the retracted results — are all in the repository. configure.sh repoints the hardcoded paths to your machine.',size=13,color=MUT,first=True,space_after=0)
notes(s,'Everything is in the repo, including the scripts for the experiments that failed. configure.sh is the one thing you need to run before anything else.')

# ========== 30 RELATED WORK ==========
s=S('Related work, in three lines')
rows=[('Cross-episode memory','AutoDroid, AppAgent, Agent Workflow Memory, Synapse, Mobile-Agent-E’s tips store how to do a task. My question is what this episode showed.',INDIGO),
 ('Write-ahead notes and look-back','GUI-Rise’s rolling summary and Mobile-Agent-E’s note-taker write before the need is known. PAL-UI trains look-back on 8.6K curated labels — exactly the supervision my verifier replaces.',RED),
 ('Gist-and-lookup, learned retrieval','ReadAgent, MemGPT, Generative Agents retrieve from short lines; doc2query and Toolformer train the writer or the caller from downstream signal. I train the retriever, after finding the writer’s ceiling is the screen itself.',AQUA)]
for i,(h,b,col) in enumerate(rows):
    y=1.55+i*1.75; box(s,0.50,y,12.35,1.42,fill=LT)
    f=tb(s,0.80,y+0.20,11.8,1.05)
    para(f,h,size=15,bold=True,color=col,first=True,space_after=5)
    para(f,b,size=14,space_after=0)
notes(s,'Three families. The middle one is the closest: PAL-UI does train look-back, but it buys its labels. That is the single sentence of delta for this project.')

# ========== 31 REFERENCES ==========
s=S('References')
refs=['Lu et al. GUI Odyssey: a comprehensive dataset for cross-app GUI navigation. arXiv:2406.08451, 2024.',
 'Zhang et al. Android in the Zoo (AITZ): chain-of-action-thought for GUI agents. Findings of EMNLP, 2024.',
 'Lee et al. ReadAgent: a human-inspired reading agent with gist memory. ICML, 2024.',
 'Liu et al. PAL-UI: planning with active look-back for vision-based GUI agents. arXiv:2510.00413, 2025.',
 'Liu et al. GUI-Rise: structured reasoning and history summarization. NeurIPS, 2025.',
 'Wang et al. Mobile-Agent-E: self-evolving mobile assistant. arXiv:2501.11733, 2025.',
 'Wen et al. AutoDroid: LLM-powered task automation in Android. MobiCom, 2024.',
 'Wang et al. Agent Workflow Memory. arXiv:2409.07429, 2024.',
 'Nogueira et al. Document expansion by query prediction (doc2query). arXiv:1904.08375, 2019.',
 'Schick et al. Toolformer: language models can teach themselves to use tools. NeurIPS, 2023.',
 'Rafailov et al. Direct Preference Optimization. NeurIPS, 2023.',
 'Liu et al. Lost in the Middle: how language models use long contexts. TACL, 2024.',
 'Hsieh et al. RULER: what is the real context size of your long-context LM? arXiv:2404.06654, 2024.',
 'Qwen Team. Qwen2.5 Technical Report. arXiv:2412.15115, 2024.']
for col in (0,1):
    f=tb(s,0.50+col*6.35,1.60,6.0,5.0)
    part=refs[:7] if col==0 else refs[7:]
    for i,r in enumerate(part): para(f,r,size=12,bullet=True,first=(i==0),space_after=10)
f=tb(s,0.50,6.55,12.35,0.4); para(f,'Full bibliography (18 entries) in the report; see the repository.',size=12,color=MUT,first=True,space_after=0)

# ========== 32 TAKEAWAY ==========
s=redslide(p,'Takeaway',[
 ('The test that finds this problem also labels it, for free.',{'size':20,'bold':True,'sa':10}),
 ('That supervision is what works — not the architecture I bet on.',{'size':20,'bold':True,'sa':26}),
 ('+10.6 and +22.3 localization points from labels nobody wrote',{'size':15,'color':C(0xF2,0xC9,0xC9),'sa':8}),
 ('the two trained models are statistically indistinguishable',{'size':15,'color':C(0xF2,0xC9,0xC9),'sa':8}),
 ('the decomposition pays only at 8–12 screens back',{'size':15,'color':C(0xF2,0xC9,0xC9),'sa':8}),
 ('13+ screens back is still open',{'size':15,'color':C(0xF2,0xC9,0xC9),'sa':22}),
 ('github.com/WMSlalalala/verifier-supervised-lookback',{'size':13,'color':C(0xF2,0xC9,0xC9)})]); N[0]+=1
notes(s,'Thank you. The thing I would most like a question about is the 13+ band, or the two traps.')

# ========== 33-35 BACKUP ==========
s=S('Backup: prevalence and gap distribution')
table(s,[['','value'],['gap median','5 screens'],['gap maximum','27 screens'],['gaps ≥ 5 screens','56 %'],
 ['answer’s rank on its source screen','13th of 33'],['cases with ≥ 2 valid source screens','40 of 85  (47 %)'],
 ['sampled trajectories with full OCR','273'],['steps in them','4,338'],
 ['verified delayed needs','89   (2.05 % of steps)'],['trajectories holding at least one','85   (31 %)']],
 2.6,1.60,8.1,colw=[I(5.1),I(3.0)],fs=13,head_fs=12,row_h=0.44)
s=S('Backup: cost of each condition')
table(s,[['condition','calls at t = 16','context read'],
 ['full history, prompted','1 × 14B','1–5K tokens'],
 ['full history, trained','1 × 7B  + read stage','1–5K tokens'],
 ['per-screen scorer','16 × 7B  + read stage','≈12K tokens total'],
 [('   3B scorer',{'color':MUT}),('16 × 3B',{'color':MUT}),('same',{'color':MUT})],
 ['read with history','1 × 14B','full history + 1 repeated screen']],
 1.3,1.70,10.7,colw=[I(3.6),I(3.4),I(3.7)],fs=13,head_fs=12,row_h=0.46)
f=tb(s,1.3,4.60,10.7,1.0); para(f,'The scorer does no generation — t forward passes of 600–900 tokens, logits only.',size=15,first=True,space_after=6)
para(f,'Training: 13–27 minutes per fold on one 48GB GPU, for either architecture.',size=14,color=MUT,space_after=0)
s=S('Backup: can the scorer tell when it is wrong?')
f=tb(s,0.60,1.60,6.3,1.0); para(f,'The scorer’s maximum probability predicts whether its own localization is correct:',size=16,first=True,space_after=0)
box(s,0.75,2.70,5.9,1.0,fill=LT)
f=tb(s,1.0,2.95,5.4,0.5); para(f,'area under the ROC curve   0.768',size=17,bold=True,color=RED,first=True,space_after=0,align=PP_ALIGN.CENTER)
f=tb(s,0.60,3.95,6.3,1.3); para(f,'Falling back to prompted full history when that probability is below 0.5 raises localization from 72.3 % to 75.0 % (32 of 188 cases fall back).',size=15,first=True,space_after=0)
card(s,7.35,1.95,5.5,2.4,'Why I do not use it',[
 ('It is one more threshold tuned on the same 188 cases, and the gain is inside the noise.',{'sa':10}),
 ('It is the obvious next thing to test properly on a larger sample.',{'size':13,'color':MUT})])
