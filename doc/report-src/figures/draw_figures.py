"""Render editable SVG, vector PDF and a 3x PNG for the project figures."""
from __future__ import annotations

import base64
import io
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

import fitz
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


OUT = Path(__file__).resolve().parent
ASSETS = OUT / 'assets'
EP = '4671561041722435'
WIDTH, HEIGHT = 1060, 438
INK = '#182B36'
MUTED = '#4E6068'
RULE = '#BEC9CB'
SOFT = '#F1F4F4'
RED = '#B51119'
PALE_RED = '#FFF1EF'
TEAL = '#006C67'
PALE_TEAL = '#EDF7F5'
WHITE = '#FFFFFF'

for face, file in [('InterLabel', 'arial.ttf'), ('InterStrong', 'arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(face, str(Path('C:/Windows/Fonts') / file)))


class Drawing:
    def __init__(self, name, title, description):
        self.name = name
        self.pdf = canvas.Canvas(str(OUT / f'{name}.pdf'), pagesize=(WIDTH, HEIGHT), pageCompression=1)
        self.pdf.setTitle(title)
        self.pdf.setAuthor('Mingshuo Wang, North Carolina State University')
        self.pdf.setSubject(description)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">', f'<title>{escape(title)}</title>', f'<desc>{escape(description)}</desc>']
        self.box(0, 0, WIDTH, HEIGHT, WHITE)

    def box(self, x, y, w, h, fill='none', stroke='none', sw=1, r=0):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        if stroke != 'none':
            self.pdf.setStrokeColor(colors.HexColor(stroke))
        if fill != 'none':
            self.pdf.setFillColor(colors.HexColor(fill))
        self.pdf.setLineWidth(sw)
        self.pdf.roundRect(x, HEIGHT-y-h, w, h, r, int(stroke!='none'), int(fill!='none'))

    def path(self, points, color=RULE, width=1.5, fill=None):
        pts = ' '.join(f'{x},{y}' for x, y in points)
        element = 'polygon' if fill else 'polyline'
        self.svg.append(f'<{element} points="{pts}" stroke="{color}" fill="{fill or "none"}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')
        p = self.pdf.beginPath()
        p.moveTo(points[0][0], HEIGHT-points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, HEIGHT-y)
        if fill:
            p.close()
            self.pdf.setFillColor(colors.HexColor(fill))
        self.pdf.setLineWidth(width)
        self.pdf.setLineJoin(1)
        self.pdf.setLineCap(1)
        self.pdf.setStrokeColor(colors.HexColor(color))
        self.pdf.drawPath(p, stroke=1, fill=int(bool(fill)))

    def arrow(self, pts, color=INK, width=1.8, head=6):
        self.path(pts, color, width)
        x1, y1 = pts[-2]
        x2, y2 = pts[-1]
        a = math.atan2(y2-y1, x2-x1)
        left = (x2-head*math.cos(a-0.55), y2-head*math.sin(a-0.55))
        right = (x2-head*math.cos(a+0.55), y2-head*math.sin(a+0.55))
        self.path([left,(x2,y2),right],color,width)

    def text(self, x, y, value, size=21, bold=False, color=INK, align='start'):
        family = 'InterStrong' if bold else 'InterLabel'
        self.pdf.setFillColor(colors.HexColor(color))
        self.pdf.setFont(family, size)
        draw = {'start': self.pdf.drawString, 'end': self.pdf.drawRightString, 'middle': self.pdf.drawCentredString}[align]
        draw(x, HEIGHT-y, value)
        weight = '700' if bold else '400'
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{align}">{escape(value)}</text>')

    def bitmap(self, img, x, y, w, h):
        img = img.convert('RGB')
        img.thumbnail((int(w*4+1),int(h*4+1)), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=92, optimize=True, subsampling=0)
        data = buffer.getvalue()
        self.svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" xlink:href="data:image/jpeg;base64,{base64.b64encode(data).decode()}"/>')
        self.pdf.drawImage(ImageReader(io.BytesIO(data)), x, HEIGHT-y-h, w, h)

    def save(self):
        self.pdf.save()
        (OUT / f'{self.name}.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        doc=fitz.open(OUT / f'{self.name}.pdf')
        for scale,suffix in [(3,''),(1,'-preview')]:
            dest = OUT if not suffix else ASSETS
            doc[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).save(dest/f'{self.name}{suffix}.png')
        doc.close()


def screen(fig, step, x, y, w, h, hilite=None, color=RED):
    im = Image.open(ASSETS / f'{EP}_{step}.png')
    fig.bitmap(im, x,y,w,h)
    fig.box(x,y,w,h,'none',RULE,0.9)
    if hilite:
        a,b,c,d=hilite
        W,H=im.size
        fig.box(x+w*a/W,y+h*b/H,w*(c-a)/W,h*(d-b)/H,'none',color,2.6,1.5)
    return im


def scenario():
    f=Drawing('scenario','A music title must survive an app switch',
              'Annotated screenshots from GUI-Odyssey (Lu et al., ICCV 2025, CC BY 4.0), episode 4671561041722435. The Electronic Study title appears on screens 4, 5, and 6. The logged action types it on screen 11 in Tumblr.')
    f.box(7,5,1046,48,SOFT,r=3)
    f.text(23,36,'TASK',17,True,MUTED)
    f.path([(87,17),(87,41)],RULE,1.5)
    f.text(103,37,'Listen to electronic music, then share its title in a message.',25,True)

    f.text(10,88,'SCREEN 6',18,True,RED)
    f.text(10,120,'Find the title in Pandora',24,True)
    f.text(398,88,'SCREENS 7–10',18,True,MUTED)
    f.text(398,120,'Switch apps',24,True)
    f.text(662,88,'SCREEN 11',18,True,TEAL)
    f.text(662,120,'Compose a message in Tumblr',24,True)
    f.path([(374,76),(374,410)],RULE,1)
    f.path([(638,76),(638,410)],RULE,1)

    yy=140; h=267.2; w=120
    src=screen(f,6,10,yy,w,h,(268,1630,733,1833),RED)
    f.path([(76,yy+h*1730/2992),(97,yy+h*1730/2992),(144,237)],RED,2)
    f.box(144,171,215,75,WHITE,RED,1.8,4)
    src_crop = src.crop((290,1651,698,1789))
    f.bitmap(src_crop,148,175,207,67)
    f.text(147,277,'The same title',21,True)
    f.text(147,303,'also appears on',21)
    f.text(147,329,'screens 4 and 5.',21)

    # Two representative intermediate screens, shown at equal scale.
    for step,x in [(8,398),(9,514)]:
        screen(f,step,x,158,96,213.7)
        lab='8 · Feed' if step==8 else '9 · Inbox'
        f.text(x+48,402,lab,19,True,MUTED,'middle')
    f.arrow([(496,260),(509,260)],MUTED,1.5,5)

    dst=screen(f,11,662,yy,w,h,(41,1676,1305,1870),TEAL)
    f.path([(778,yy+h*1760/2992),(790,yy+h*1760/2992),(812,231)],TEAL,2)
    f.box(811,170,240,66,WHITE,TEAL,1.8,4)
    dst_crop=dst.crop((163,1738,555,1836))
    f.bitmap(dst_crop,815,174,232,58)
    f.text(812,269,'Logged TYPE action',19,True,TEAL)
    f.text(812,299,'“Electronic Study”',24,True)
    f.text(812,337,'The title is absent',20)
    f.text(812,363,'from current OCR.',20)
    f.save()


def method():
    f=Drawing('method','Verifier supervision and source selection',
              'During training, matching the logged TYPE string against normalized OCR yields a binary label per readable earlier screen. The full-history locator target is the latest positive. At inference the task, current OCR and earlier OCR feed either trained 7B locator; a shared 14B model reads the selected OCR with history to predict the text.')
    f.box(6,7,1048,155,PALE_RED,r=5)
    f.box(6,7,7,155,RED)
    f.text(27,37,'TRAINING',18,True,RED)
    f.text(27,76,'Logged TYPE',24,True)
    f.text(27,111,'“Electronic Study”',24)
    f.arrow([(233,92),(258,92)],RED,2.2)
    f.text(277,76,'Match against OCR',24,True)
    f.text(277,108,'Absent now, present',20)
    f.text(277,133,'on an earlier screen',20)
    f.arrow([(513,92),(543,92)],RED,2.2)
    f.text(563,58,'Earlier screen',17,True,MUTED)
    f.text(563,95,'Match label',18,True,RED)
    # Concrete slice of the eleven candidate screens of the Figure 1 trajectory.
    cols=[('…','…'),('3','0'),('4','1'),('5','1'),('6','1'),('7','0'),('…','…')]
    for idx,(number,label) in enumerate(cols):
        x=726+idx*43
        f.text(x+17,58,number,19,True,INK,'middle')
        positive=label=='1'
        f.box(x,69,34,35,RED if positive else WHITE,RED if positive else RULE,1.2,3)
        f.text(x+17,94,label,21,True,WHITE if positive else MUTED,'middle')
    f.text(563,135,'Scorer target = all labels  ·  locator target = 6',19,True)

    f.text(17,196,'INFERENCE',18,True,TEAL)
    f.path([(147,190),(1049,190)],RULE,1)
    f.text(17,256,'Agent context',24,True)
    f.text(17,291,'Task instruction',20)
    f.text(17,318,'Current screen OCR',20)
    f.text(17,345,'Earlier screen OCR',20)
    f.path([(221,300),(246,300)],TEAL,2)
    f.arrow([(246,300),(246,253),(274,253)],TEAL,2)
    f.arrow([(246,300),(246,358),(274,358)],TEAL,2)

    f.box(282,210,410,85,SOFT,r=4)
    f.text(297,237,'Per-screen scorer · 7B',23,True)
    f.text(297,264,'Score each candidate independently.',19)
    f.text(297,286,'Choose the highest P(Yes).',19)
    f.box(282,314,410,85,SOFT,r=4)
    f.text(297,341,'Full-history locator · 7B',23,True)
    f.text(297,368,'Read all earlier OCR in one prompt.',19)
    f.text(297,390,'Generate one source index.',19)
    f.text(486,309,'OR',14,True,MUTED,'middle')
    f.path([(693,253),(719,253),(719,358),(693,358)],TEAL,2)
    f.arrow([(719,300),(751,300)],TEAL,2)

    f.box(760,216,293,176,PALE_TEAL,r=5)
    f.box(760,216,6,176,TEAL)
    f.text(781,247,'Shared reader · 14B',23,True)
    f.text(781,278,'Mark the selected screen',19)
    f.text(781,302,'in the full OCR history.',19)
    f.path([(782,320),(1030,320)],'#A8C9C5',1)
    f.text(781,354,'Predict the text to type',22,True,TEAL)
    f.save()


if __name__=='__main__':
    annotations=json.loads((ASSETS/f'{EP}.json').read_text(encoding='utf-8'))
    assert annotations['steps'][11]['info']=='Electronic Study'
    scenario()
    method()
