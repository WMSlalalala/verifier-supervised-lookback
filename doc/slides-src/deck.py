"""NC State branded deck, built with python-pptx. Colors from brand.ncsu.edu."""
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

RED=C(0xCC,0x00,0x00); REYNOLDS=C(0x99,0x00,0x00); BLACK=C(0,0,0); WHITE=C(0xFF,0xFF,0xFF)
MUT=C(0x4D,0x4D,0x4D); LT=C(0xF2,0xF2,0xF2); GRAY=C(0xB2,0xB2,0xB2)
AQUA=C(0x00,0x71,0x6D); AQUA_FIG=C(0x2D,0xB5,0x97); INDIGO=C(0x41,0x56,0xA1); PINK=C(0xFD,0xEC,0xEC)
HEAD='Arial'; BODY='Calibri'
import os
FIG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'figures')+'/'
W,H=13.333,7.5

def deck():
    p=Presentation(); p.slide_width=I(W); p.slide_height=I(H)
    p.core_properties.title='Verifier-Supervised Look-Back'
    p.core_properties.author='Mingshuo Wang'
    return p

def blank(p): return p.slides.add_slide(p.slide_layouts[6])

def tb(s,x,y,w,h,anchor=MSO_ANCHOR.TOP):
    t=s.shapes.add_textbox(I(x),I(y),I(w),I(h)); f=t.text_frame
    f.word_wrap=True; f.margin_left=0; f.margin_right=0; f.margin_top=0; f.margin_bottom=0
    f.vertical_anchor=anchor
    return f

def para(f,runs,size=16,color=BLACK,bold=False,font=BODY,space_after=8,align=PP_ALIGN.LEFT,
         bullet=False,first=False,line=None,italic=False):
    pr=f.paragraphs[0] if first else f.add_paragraph()
    pr.alignment=align; pr.space_after=Pt(space_after)
    if bullet:
        pPr=pr._p.get_or_add_pPr(); pPr.set('marL','200025'); pPr.set('indent','-200025')
    if line: pr.line_spacing=line
    if isinstance(runs,str): runs=[(runs,{})]
    for k,(txt,o) in enumerate(runs):
        r=pr.add_run(); r.text=('•  ' if (bullet and k==0) else '')+txt
        r.font.size=Pt(o.get('size',size)); r.font.bold=o.get('bold',bold)
        r.font.color.rgb=o.get('color',color); r.font.name=o.get('font',font)
        r.font.italic=o.get('italic',italic)
    return pr

def title(s,text,sub=None):
    f=tb(s,0.45,0.30,12.45,0.80,MSO_ANCHOR.MIDDLE)
    para(f,text,size=28,bold=True,font=HEAD,first=True,space_after=0)
    if sub:
        g=tb(s,0.45,1.06,12.45,0.34); para(g,sub,size=13,color=MUT,first=True,space_after=0)

def footer(s,n):
    f=tb(s,0.45,7.00,7.0,0.3); para(f,'Verifier-Supervised Look-Back',size=10,color=MUT,first=True,space_after=0)
    g=tb(s,9.0,7.00,3.9,0.3); para(g,f'Mingshuo Wang  ·  NC State      {n}',size=10,color=MUT,
        first=True,space_after=0,align=PP_ALIGN.RIGHT)

def box(s,x,y,w,h,fill=LT,line=None,radius=True):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                          I(x),I(y),I(w),I(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line: sh.line.color.rgb=line; sh.line.width=Pt(1.5)
    else: sh.line.fill.background()
    sh.shadow.inherit=False
    if radius:
        try: sh.adjustments[0]=0.08
        except Exception: pass
    sh.text_frame.text=''
    return sh

def redslide(p,heading,lines,n=None):
    s=blank(p)
    bg=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,I(W),I(H))
    bg.fill.solid(); bg.fill.fore_color.rgb=RED; bg.line.fill.background(); bg.shadow.inherit=False
    f=tb(s,0.95,1.45,11.4,4.6)
    para(f,heading,size=40,bold=True,color=WHITE,font=HEAD,first=True,space_after=22)
    for txt,o in lines: para(f,txt,size=o.get('size',18),color=o.get('color',WHITE),
                             bold=o.get('bold',False),space_after=o.get('sa',14))
    return s

def img(s,name,x,y,w):
    return s.shapes.add_picture(FIG+name,I(x),I(y),width=I(w))

def table(s,data,x,y,w,colw=None,fs=12,head_fs=12,row_h=0.3):
    rows,cols=len(data),len(data[0])
    g=s.shapes.add_table(rows,cols,I(x),I(y),I(w),I(row_h*rows)).table
    if colw:
        for i,cw in enumerate(colw): g.columns[i].width=Emu(int(cw))
    for ri,row in enumerate(data):
        g.rows[ri].height=I(row_h)
        for ci,cell in enumerate(row):
            txt,opt=(cell,{}) if isinstance(cell,str) else cell
            c=g.cell(ri,ci); c.text=''
            c.margin_left=I(0.06); c.margin_right=I(0.06); c.margin_top=0; c.margin_bottom=0
            c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb=opt.get('fill', LT if ri==0 else WHITE)
            pr=c.text_frame.paragraphs[0]; pr.alignment=opt.get('align', PP_ALIGN.LEFT if ci==0 else PP_ALIGN.RIGHT)
            r=pr.add_run(); r.text=txt
            r.font.size=Pt(head_fs if ri==0 else fs); r.font.name=BODY
            r.font.bold=opt.get('bold', ri==0); r.font.color.rgb=opt.get('color', BLACK)
    return g

def notes(s,text): s.notes_slide.notes_text_frame.text=text


def kv(s,x,y,w,rows,size=14,gap=0.30,label_color=BLACK,val_color=None,bold_val=True):
    """Label left, value right-aligned at x+w. rows = [(label, value, color|None), ...]"""
    for i,row in enumerate(rows):
        lab,val=row[0],row[1]; col=row[2] if len(row)>2 else (val_color or BLACK)
        yy=y+i*gap
        f=tb(s,x,yy,w-1.35,gap); para(f,lab,size=size,color=label_color,first=True,space_after=0)
        g=tb(s,x+w-1.35,yy,1.35,gap)
        para(g,val,size=size,bold=bold_val,color=col,first=True,space_after=0,align=PP_ALIGN.RIGHT)
