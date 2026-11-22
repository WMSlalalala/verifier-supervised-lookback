"""Build the NC State presentation for Verifier-Supervised Look-Back.

Usage: python build_slides.py ncsu_template.pptx assets Slides.pptx
       powershell -File export_pdf.ps1 -In <full path to Slides.pptx> -Out <full path to Slides.pdf>   (needs PowerPoint)

The template supplies the official NC State master, layouts and masthead;
any existing slide is removed and the talk is rebuilt from scratch.
"""
import re
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

BASE, ASSETS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

RED = RGBColor(0xCC, 0x00, 0x00)
DEEP = RGBColor(0x99, 0x00, 0x00)
DARK = RGBColor(0x1F, 0x23, 0x28)
GREY = RGBColor(0x45, 0x4B, 0x52)
MUTED = RGBColor(0x6B, 0x71, 0x78)
LINE = RGBColor(0xD0, 0xD3, 0xD6)
PALE = RGBColor(0xF2, 0xF3, 0xF4)
ROSE = RGBColor(0xFB, 0xEA, 0xEA)
HEAD = RGBColor(0x35, 0x3A, 0x3F)
BAR = RGBColor(0x9A, 0xA0, 0xA6)
TEAL = RGBColor(0x11, 0x69, 0x63)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT, MONO = "Arial", "Consolas"
REPO = "https://github.com/WMSlalalala/verifier-supervised-lookback"

prs = Presentation(str(BASE))
ids = prs.slides._sldIdLst
for sid in list(ids):
    prs.part.drop_rel(sid.get(qn("r:id")))
    ids.remove(sid)
LAYOUT = {l.name: l for l in prs.slide_layouts}
page = [0]


# ---------------------------------------------------------------- helpers
def glue(t):
    """Keep relations and arrows attached to the numbers they belong to."""
    for a, b in (("≤ ", "≤ "), ("≥ ", "≥ "), (" → ", " → "),
                 (" = ", " = "), ("(p", "(p")):
        t = t.replace(a, b)
    return t


def style_run(r, size, color, bold=False, italic=False, font=FONT, link=None):
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    if link:
        r.hyperlink.address = link


def bulletize(p, indent=13, char="•", color=None):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Pt(indent)))
    pPr.set("indent", str(-Pt(indent)))
    if color is not None:
        clr = etree.SubElement(pPr, qn("a:buClr"))
        srgb = etree.SubElement(clr, qn("a:srgbClr"))
        srgb.set("val", str(color))
    fnt = etree.SubElement(pPr, qn("a:buFont"))
    fnt.set("typeface", FONT)
    ch = etree.SubElement(pPr, qn("a:buChar"))
    ch.set("char", char)


def text(slide, x, y, w, h, paras, size=14, color=GREY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font=FONT, after=0, bullet=False, line=None, name=None):
    """paras: list of str | list of (text, opts) runs | dict(runs=..., bullet=, size=, after=)."""
    box = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        spec = para if isinstance(para, dict) else {"runs": para}
        runs = spec["runs"]
        if isinstance(runs, str):
            runs = [(runs, {})]
        p.alignment = spec.get("align", align)
        p.space_after = Pt(spec.get("after", after))
        if line or spec.get("line"):
            p.line_spacing = spec.get("line", line)
        psize = spec.get("size", size)
        for t, o in runs:
            r = p.add_run()
            r.text = t if font == MONO else glue(t)
            style_run(r, o.get("size", psize), o.get("color", spec.get("color", color)),
                      o.get("bold", spec.get("bold", bold)), o.get("italic", False),
                      o.get("font", font), o.get("link"))
        if spec.get("bullet", bullet):
            bulletize(p, spec.get("indent", 13), color=spec.get("bucolor"))
    return box


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None, name=None):
    s = slide.shapes.add_shape(shape, Pt(x), Pt(y), Pt(w), Pt(h))
    if name:
        s.name = name
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    if radius is not None:
        s.adjustments[0] = radius
    return s


def label_shape(s, value, size, color, bold=True, align=PP_ALIGN.CENTER):
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = value
    style_run(r, size, color, bold)


def picture(slide, path, x, y, w, h, name=None):
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    pw, ph = iw * k, ih * k
    pic = slide.shapes.add_picture(str(path), Pt(x + (w - pw) / 2), Pt(y + (h - ph) / 2), Pt(pw), Pt(ph))
    if name:
        pic.name = name
    return pic


TIMES = ["0:00-0:10", "0:10-1:00", "1:00-1:50", "1:50-2:50", "2:50-3:30", "3:30-4:10", "4:10-5:05",
         "5:05-5:45", "5:45-6:50", "6:50-7:45", "7:45-8:15", "8:15-9:05", "9:05-9:30", "9:30-9:35", None]


def notes(slide, body):
    """Speaker notes, prefixed with the slide's slot in the 10-minute schedule."""
    body = re.sub(r"^\[[^\]]*\]\s*", "", body)
    idx = prs.slides.index(slide)
    if idx < len(TIMES) and TIMES[idx]:
        body = f"[{TIMES[idx]}] " + body
    slide.notes_slide.notes_text_frame.text = body


def new_slide(title):
    s = prs.slides.add_slide(LAYOUT["Title Only"])
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Pt(36), Pt(44), Pt(648), Pt(36)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = title
    style_run(r, 24, DARK, True)
    page[0] += 1
    text(s, 640, 384, 44, 12, str(page[0] + 1), size=10, color=MUTED, align=PP_ALIGN.RIGHT, name="Page number")
    return s


def caption(slide, value, y=384, w=590):
    text(slide, 36, y, w, 12, value, size=10, color=MUTED, name="Caption")


def table(slide, x, y, widths, heights, rows, size=12, head=HEAD, focus=(), strong=(), name=None, header_rows=1,
          merges=()):
    shp = slide.shapes.add_table(len(rows), len(widths), Pt(x), Pt(y), Pt(sum(widths)), Pt(sum(heights)))
    if name:
        shp.name = name
    tbl = shp.table
    tbl.first_row = False
    tbl.horz_banding = False
    for j, wd in enumerate(widths):
        tbl.columns[j].width = Pt(wd)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Pt(heights[i])
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left, c.margin_right = Pt(7), Pt(6)
            c.margin_top = c.margin_bottom = Pt(1)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            if i < header_rows:
                c.fill.fore_color.rgb = head
            elif i in focus:
                c.fill.fore_color.rgb = ROSE
            else:
                c.fill.fore_color.rgb = PALE if (i - header_rows) % 2 == 0 else WHITE
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = glue(val)
            if i < header_rows:
                style_run(r, size - 1, WHITE, True)
            else:
                hot = (i, j) in strong
                style_run(r, size, RED if hot else DARK, hot or (i in focus and j == 0))
    for (r0, c0), (r1, c1) in merges:
        tbl.cell(r0, c0).merge(tbl.cell(r1, c1))
    return tbl


def card(slide, x, y, w, h, fill=PALE, name=None):
    return rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04, name=name)


def number_badge(slide, x, y, value, d=30, fill=RED):
    b = rect(slide, x, y, d, d, fill, shape=MSO_SHAPE.OVAL, name=f"Badge {value}")
    label_shape(b, value, 14, WHITE)
    return b


def code(slide, x, y, w, h, lines, size=10.5):
    card(slide, x, y, w, h, fill=RGBColor(0xF4, 0xF5, 0xF6), name="Code background")
    paras = []
    for ln in lines:
        col = MUTED if ln.lstrip().startswith("#") else DARK
        paras.append({"runs": [(ln if ln else " ", {"color": col})]})
    return text(slide, x + 10, y + 8, w - 20, h - 16, paras, size=size, font=MONO, name="Code")


# ---------------------------------------------------------------- 1 title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
ph = {p.placeholder_format.idx: p for p in s.placeholders}
for idx, (val, x, y, w, h, size, bold, col) in {
    0: ("Verifier-Supervised Look-Back", 60, 104, 600, 56, 36, True, DARK),
    1: ("for Delayed Information Needs in Mobile GUI Agents", 60, 160, 600, 30, 19, False, GREY),
}.items():
    t = ph[idx]
    t.left, t.top, t.width, t.height = Pt(x), Pt(y), Pt(w), Pt(h)
    tf = t.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = val
    style_run(r, size, col, bold)
text(s, 60, 232, 600, 24, "Mingshuo Wang", size=18, color=DARK, bold=True, align=PP_ALIGN.CENTER)
text(s, 60, 258, 600, 20, "North Carolina State University", size=14, color=GREY, align=PP_ALIGN.CENTER)
text(s, 60, 300, 600, 18, "Final project presentation  ·  Fall 2026", size=12, color=MUTED, align=PP_ALIGN.CENTER)
text(s, 60, 324, 600, 16, [[("github.com/WMSlalalala/verifier-supervised-lookback", {"color": TEAL, "link": REPO})]],
     size=12, align=PP_ALIGN.CENTER)
notes(s, "[0:00-0:15] Hi, I'm Mingshuo Wang. This project asks how a mobile GUI agent can find text that has "
         "already left the screen, and shows that the labels needed to train this skill are already inside "
         "ordinary demonstrations.")

# ---------------------------------------------------------------- 2 background
s = new_slide("Long tasks need text that has already left the screen")
text(s, 36, 88, 648, 34, [
    {"runs": "Agents such as AppAgent, Mobile-Agent-v2 and UI-TARS now finish multi-step tasks in real apps, and "
             "AITW, AndroidControl and GUI-Odyssey moved evaluation to long, cross-app tasks.", "size": 13},
], color=GREY)
text(s, 36, 124, 648, 18, [[("At step 11 the title ", {}), ("Electronic Study", {"italic": True}),
                            (" is gone. Which earlier screen holds it?", {})]],
     size=15, color=DARK, bold=True)
picture(s, ASSETS / "scenario.png", 36, 148, 648, 230, name="Scenario figure")
caption(s, "GUI-Odyssey episode 4671561041722435; screenshots CC BY 4.0 (Lu et al., ICCV 2025).")
notes(s, "[0:15-1:00] Mobile GUI agents such as AppAgent, Mobile-Agent-v2 and UI-TARS can now finish multi-step "
         "tasks in real apps, and datasets like AITW, AndroidControl and GUI-Odyssey moved to long cross-app tasks. "
         "Longer tasks create a specific need. In this GUI-Odyssey episode the user listens to music in Pandora and "
         "then opens Tumblr to send its title to a friend. At step 11 the message box is open, but the title "
         "Electronic Study is no longer on screen; it appeared on screens 4, 5 and 6. So before typing, the agent "
         "must decide which earlier screen to re-read, and then copy the right string from it.")

# ---------------------------------------------------------------- 3 existing approaches
s = new_slide("Existing approaches leave the answer hard to find")
cards = [
    ("1", "Full history in the prompt", "Lost in the Middle · RULER · Visual Haystacks",
     "The answer competes with every menu, button and message, and the prompt grows each step. "
     "Long inputs are used unevenly.", "54.8%", "localization, 14B full-history prompt"),
    ("2", "Summaries or notes per screen", "ReadAgent · MemGPT · Mobile-Agent-E · GUI-Rise",
     "Written before the agent knows what it needs, so the answer is easily dropped. "
     "Summarizers are often tied to one agent.", "41.0%", "localization, screen index"),
    ("3", "Active look-back (recent)", "PAL-UI, Findings of IJCNLP-AACL 2026",
     "Learns to retrieve earlier screenshots, but logs never mark which screen to revisit; "
     "labels come from a teacher model.", "8.6K", "teacher-synthesized examples"),
]
for k, (n, head, cites, body, big, lab) in enumerate(cards):
    x = 36 + k * 222
    card(s, x, 90, 204, 226, name=f"Approach card {n}")
    number_badge(s, x + 12, 102, n, d=24)
    text(s, x + 44, 100, 150, 30, head, size=14, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 12, 134, 182, 28, cites, size=10, color=MUTED)
    text(s, x + 12, 164, 182, 96, body, size=13, color=GREY)
    text(s, x + 12, 262, 182, 30, big, size=24, color=RED if k < 2 else DARK, bold=True)
    text(s, x + 12, 292, 182, 16, lab, size=10, color=MUTED)
card(s, 36, 326, 648, 48, fill=ROSE, name="Verified problem")
text(s, 50, 330, 620, 40, [[("Verified problem: ", {"bold": True, "color": DEEP}),
                            ("prompting alone does not reliably find the source screen. An untrained 7B per-screen "
                             "model reaches 50.0%, and the 14B prompt falls from 68.0% (t ≤ 15) to 46.0% (t ≥ 16).", {})]],
     size=13, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[1:00-1:50] There are three existing ways to handle this. First, put the entire history into the prompt. "
         "The answer then competes with every menu and message, and long-context studies show models use long inputs "
         "unevenly; in our data a 14B full-history prompt finds the right screen only 54.8 percent of the time. "
         "Second, write a summary or note per screen and retrieve through it. Summaries are written before the agent "
         "knows what it will need, so the answer gets dropped; our screen index reaches 41 percent. Summarizers are "
         "also often tied to one agent, for example GUI-Rise rewards summaries by its own agent's later actions. "
         "Third, and most recent, PAL-UI trains an agent to look back, but because logs never say which screen to "
         "revisit, it synthesizes 8.6 thousand examples with a teacher model; hand labels would require reading a "
         "whole trajectory per decision. Bottom line: prompting alone does not reliably find the source screen, and "
         "later steps are much harder.")

# ---------------------------------------------------------------- 4 our observation
SHOT = 1344 / 2992  # width / height of a GUI-Odyssey screenshot
s = new_slide("Our observation: the log tells us where the answer is")
for k, (n, head) in enumerate([("1", "The log records what was typed"), ("2", "It is gone from the current screen"),
                               ("3", "Earlier screens still show it")]):
    x = 36 + k * 222
    card(s, x, 88, 204, 240, name=f"Observation panel {n}")
    number_badge(s, x + 12, 99, n, d=24)
    text(s, x + 44, 96, 152, 30, head, size=13, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
# panel 1: the real action log around step 11
log = [("", "..."), ("9", "CLICK"), ("10", "CLICK"), ("11", "TYPE “Electronic Study”"), ("12", "CLICK"),
       ("13", "COMPLETE")]
for i, (stp, act) in enumerate(log):
    y = 140 + i * 21
    hot = stp == "11"
    if hot:
        rect(s, 42, y - 3, 192, 20, ROSE, line=RED, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3, name="Step 11 row")
    text(s, 46, y, 20, 15, stp, size=11, color=MUTED, align=PP_ALIGN.RIGHT, font=MONO)
    text(s, 72, y, 160, 15, act, size=11, color=DEEP if hot else DARK, bold=hot, font=MONO)
text(s, 48, 274, 180, 48, "At step 11 the user typed the title; the log keeps the exact text.", size=12, color=GREY)
# panel 2: the current screen, where the title is absent
sh = 168
sw = sh * SHOT
px = 258 + (204 - sw) / 2
picture(s, ASSETS / "shot11.png", px, 132, sw, sh, name="Screen 11")
hl = rect(s, px + 0.02 * sw, 132 + 0.568 * sh, 0.96 * sw, 0.056 * sh, None, line=RED,
          shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3, name="Message box highlight")
hl.line.width = Pt(2)
text(s, 270, 304, 180, 18, "Screen 11: the title is not here", size=12, color=GREY, align=PP_ALIGN.CENTER)
# panel 3: an earlier screen that shows the title
card(s, 488, 136, 192, 60, fill=WHITE, name="Zoom frame")
picture(s, ASSETS / "crop6_row.png", 492, 140, 184, 52, name="Screen 6 row")
text(s, 492, 200, 184, 14, "Screen 6 · Pandora search results", size=10, color=MUTED, align=PP_ALIGN.CENTER)
text(s, 492, 226, 184, 40, "Found on screens 4, 5 and 6", size=15, color=RED, bold=True, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE)
text(s, 492, 272, 184, 40, "and on no other earlier screen", size=12, color=GREY, align=PP_ALIGN.CENTER)
card(s, 36, 336, 648, 38, fill=ROSE, name="Observation takeaway")
text(s, 50, 339, 620, 32, [[("Observation: ", {"bold": True, "color": DEEP}),
                            ("the typed text in the log marks which earlier screens hold the answer, so the labels "
                             "come for free.", {})]], size=13, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Here is our key observation, on the real example. First, the demonstration log records every action; at "
         "step 11 it says the user typed Electronic Study. Second, on the screen at step 11, the Tumblr message box, "
         "the title is nowhere to be seen. Third, when we search the OCR of the earlier screens for that text, we find "
         "it on screen 6, the Pandora search results, and also on screens 4 and 5, but on no other screen. So the typed "
         "text in the log tells us exactly which earlier screens hold the answer. That gives us labels for free, without "
         "human annotation or a teacher model.")

# ---------------------------------------------------------------- 6 method overview
s = new_slide("Method: labels from the log, two selectors, one reader")
picture(s, ASSETS / "method.png", 46, 84, 628, 244, name="Method figure")
parts = [("1", "Label", "match the logged text against every earlier screen's OCR"),
         ("2", "Select", "per-screen scorer or full-history selector (Qwen2.5-7B + LoRA)"),
         ("3", "Read", "a frozen Qwen2.5-14B writes the text from the marked screen")]
for k, (n, head, body) in enumerate(parts):
    x = 36 + k * 222
    number_badge(s, x, 336, n, d=24)
    text(s, x + 32, 334, 172, 44, [[(head + ": ", {"bold": True, "color": DARK}), (body, {})]], size=12,
         color=GREY)
notes(s, "[3:15-3:55] Here is the whole method. At training time, the logged text entry is matched against the OCR "
         "of every earlier screen, which labels each screen. These labels train two selectors built on Qwen2.5-7B "
         "with LoRA: a per-screen scorer and a full-history selector. At inference neither selector sees the logged "
         "text. The chosen screen is marked in the history and passed to a frozen 14B reader, which writes the text "
         "to type.")

# ---------------------------------------------------------------- 7 labels
s = new_slide("Step 1: turn the typed text into labels")
for k, (head, body) in enumerate([
        ("Search earlier screens for the typed text",
         "The log says the user typed “Electronic Study”. We look for it in the OCR of every earlier screen."),
        ("Keep only real look-back steps",
         "The text must be gone from the current screen but appear on an earlier one.")]):
    x = 36 + k * 332
    card(s, x, 90, 316, 194, name=f"Label step {k + 1}")
    number_badge(s, x + 14, 102, str(k + 1), d=26)
    text(s, x + 50, 100, 254, 30, head, size=15, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 14, 138, 288, 50, body, size=13, color=GREY)
x = 36
for j, scr in enumerate(range(3, 10)):
    hit = scr in (4, 5, 6)
    bx = x + 21 + j * 40
    b = rect(s, bx, 196, 34, 34, ROSE if hit else WHITE, line=RED if hit else LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12, name=f"Screen {scr}")
    label_shape(b, str(scr), 11, DEEP if hit else MUTED, bold=hit)
    text(s, bx, 234, 34, 14, "1" if hit else "0", size=12, color=RED if hit else MUTED, bold=True,
         align=PP_ALIGN.CENTER)
text(s, x + 14, 256, 288, 16, "contains the text → label 1, otherwise 0", size=11, color=MUTED,
     align=PP_ALIGN.CENTER)
x = 368
for j, (lab, ok) in enumerate([("Current screen:  text is gone", False), ("An earlier screen:  text is there", True)]):
    chip = rect(s, x + 14, 196 + j * 38, 288, 30, ROSE if ok else WHITE, line=RED if ok else LINE,
                shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3, name=f"Condition {j + 1}")
    label_shape(chip, lab, 13, DEEP if ok else DARK, bold=ok)
text(s, x + 14, 270, 288, 12, "(at least 3 characters, not copied from the task)", size=10, color=MUTED,
     align=PP_ALIGN.CENTER)
for k, (big, lab) in enumerate([("188", "typing steps kept"), ("2,861", "labeled screens"),
                                ("0", "human labels")]):
    x = 36 + k * 222
    card(s, x, 294, 204, 80, fill=ROSE if k == 2 else PALE, name=f"Stat {lab}")
    text(s, x + 14, 302, 176, 36, big, size=28, color=RED, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 14, 342, 176, 22, lab, size=13, color=DARK, bold=True, align=PP_ALIGN.CENTER)
notes(s, "Step one turns this observation into a rule. For every typing step, we search the earlier screens "
         "for the typed text: matching screens get label 1, the rest 0. We keep only steps where the text is "
         "gone from the current screen but appeared earlier, with at least three characters and not copied from "
         "the task. This turns 188 typing steps into 2,861 labeled screens, with no human labels.")

# ---------------------------------------------------------------- 8 selectors + reader
s = new_slide("Step 2: pick the screen, then read it")
for k, (head, body) in enumerate([
        ("Per-screen scorer (7B)",
         "Asks for each earlier screen: does it hold the text? Picks the screen with the highest yes-score."),
        ("Full-history selector (7B)",
         "Reads all earlier screens in one prompt and answers with a single screen number.")]):
    x = 36 + k * 332
    card(s, x, 90, 316, 194, name=f"Selector {k + 1}")
    text(s, x + 14, 100, 288, 24, head, size=16, color=DARK, bold=True)
    text(s, x + 14, 128, 288, 50, body, size=13, color=GREY)
x = 36
for j, (scr, hgt) in enumerate(zip(range(3, 10), (0.18, 0.62, 0.70, 0.95, 0.28, 0.16, 0.10))):
    bx, top = x + 31 + j * 38, 236 - 52 * hgt
    rect(s, bx, top, 26, 52 * hgt, RED if scr == 6 else BAR, name=f"Score bar {scr}")
    text(s, bx - 4, 238, 34, 12, str(scr), size=10, color=MUTED, align=PP_ALIGN.CENTER)
text(s, x + 14, 256, 288, 16, "highest yes-score → screen 6", size=12, color=RED, bold=True,
     align=PP_ALIGN.CENTER)
x = 368
for j in range(11):
    sel_ = j == 5
    b = rect(s, x + 14 + j * 26, 200, 22, 34, ROSE if sel_ else WHITE, line=RED if sel_ else LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15, name=f"History screen {j}")
    label_shape(b, str(j), 9, DEEP if sel_ else MUTED, bold=sel_)
text(s, x + 14, 256, 288, 16, "one prompt, one answer: “screen 5”", size=12, color=RED, bold=True,
     align=PP_ALIGN.CENTER)
card(s, 36, 294, 648, 80, fill=ROSE, name="Reader")
text(s, 50, 300, 620, 68, [
    {"runs": [("Then read: ", {"bold": True, "color": DEEP}),
              ("a 14B reader (not trained) sees the history with the chosen screen marked and writes the text to "
               "type, e.g., ", {}), ("Electronic Study", {"italic": True}), (".", {})], "after": 4},
    {"runs": "Both selectors are Qwen2.5-7B + LoRA, trained on the Step 1 labels.", "size": 12, "color": GREY},
], size=14, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[4:35-5:25] Step two: we train a 7B model to pick the screen, in one of two ways. The per-screen scorer "
         "looks at one earlier screen at a time and asks: does this screen hold the text? It picks the screen with "
         "the highest yes-score; in our example, screen 6. The full-history selector reads all earlier screens at "
         "once and simply answers with a screen number; in our example, screen 5. Both are Qwen2.5-7B with LoRA, "
         "trained on the same labels. Then a 14B reader, which we do not train, reads the chosen screen marked in the "
         "history and writes the text to type.")

# ---------------------------------------------------------------- 9 setup
s = new_slide("Experimental setup")
cols = [("Data", [
    ("GUI-Odyssey ", "first public release, 7,735 cross-app trajectories; OCR by EasyOCR"),
    ("Development: ", "188 cases from 182 trajectories, 5-fold CV grouped by trajectory"),
    ("Held-out: ", "93 cases from 90 disjoint trajectories; train once on all 188, test once")]),
    ("Baselines", [
        ("Untrained per-screen (7B): ", "same model and prompt, no adapter; isolates training"),
        ("Full-history prompt (14B): ", "numbered history, asked for the source screen"),
        ("Screen index (14B): ", "one line of ≤ 32 tokens per screen, then pick (ReadAgent-style)")]),
    ("Metrics", [
        ("Localization: ", "selected screen ∈ Vₜ, so any valid screen counts"),
        ("Typed-text accuracy: ", "normalized output contains the reference text"),
        ("Tests: ", "paired two-sided McNemar with continuity correction; one run per condition")])]
for k, (head, items) in enumerate(cols):
    x = 36 + k * 222
    card(s, x, 90, 204, 230, name=f"{head} card")
    text(s, x + 14, 100, 176, 22, head, size=16, color=RED, bold=True)
    text(s, x + 14, 128, 178, 188, [{"runs": [(a, {"bold": True, "color": DARK}), (b, {})], "after": 8}
                                    for a, b in items], size=13, color=GREY)
card(s, 36, 328, 648, 46, fill=ROSE, name="Case retention")
text(s, 50, 332, 620, 38, [[("Case retention: ", {"bold": True, "color": DEEP}),
                            ("800 sampled trajectories → 1,038 candidate entries → 188 development cases "
                             "(batches of 85, 53 and 50); 400 more trajectories → 438 candidates → 93 held-out "
                             "cases.", {})]], size=12, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[5:25-6:00] Experimental setup. We use the first public release of GUI-Odyssey with EasyOCR. The "
         "development pool has 188 cases from 182 trajectories, evaluated with five-fold cross-validation grouped by "
         "trajectory. The held-out set has 93 cases from 90 disjoint trajectories; we train once on all development "
         "cases and test once. Baselines: the untrained per-screen model isolates the effect of training, plus a 14B "
         "full-history prompt and a ReadAgent-style screen index. Localization counts any valid screen as correct; "
         "typed-text accuracy checks whether the output contains the reference; all comparisons use paired McNemar "
         "tests.")

# ---------------------------------------------------------------- result 1: main table
s = new_slide("Result 1: the free labels work")
rows = [["", "Development (188 cases)", "", "Held-out (93 cases)", ""],
        ["Selector", "Finds screen", "Types text", "Finds screen", "Types text"],
        ["Prompted screen index (14B)", "41.0", "23.9", "37.6", "18.3"],
        ["Prompted full history (14B)", "54.8", "31.4", "59.1", "23.7"],
        ["Untrained per-screen (7B)", "50.0", "35.1", "41.9", "–"],
        ["Trained full history (7B)", "65.4", "42.6", "76.3", "51.6"],
        ["Trained per-screen (7B)", "72.3", "44.7", "79.6", "49.5"]]
table(s, 36, 90, [228, 105, 105, 105, 105], [24, 24] + [30] * 5, rows, size=14, focus=(5, 6),
      strong={(6, 1), (6, 2), (6, 3), (5, 4)}, name="Main results table", header_rows=2,
      merges=(((0, 1), (0, 2)), ((0, 3), (0, 4))))
text(s, 36, 296, 648, 14, "Percent of cases. Development uses 5-fold cross-validation; held-out trajectories are "
                          "never seen in training.", size=10, color=MUTED)
card(s, 36, 318, 648, 56, fill=ROSE, name="Result 1 proves")
text(s, 50, 322, 620, 48, [[("What it proves: ", {"bold": True, "color": DEEP}),
                            ("training on labels from the log makes a 7B model find the right screen far more often "
                             "(50.0% → 72.3%; held-out 41.9% → 79.6%), beating every prompted baseline, "
                             "even at 14B.", {})]], size=14, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Result one: the free labels work. The table compares the trained selectors with three prompted ones. With the "
         "same base model, prompt and reader, training lifts the per-screen model from 50.0 to 72.3 percent of right "
         "screens, with 52 cases fixed and 10 broken, p below 0.001; typed text goes from 35.1 to 44.7 percent. On "
         "held-out trajectories it goes from 41.9 to 79.6 percent. Both trained 7B selectors beat the 14B prompts, and "
         "the two trained selectors are statistically close to each other.")

# ---------------------------------------------------------------- result 2: finding vs reading
s = new_slide("Result 2: finding the screen is no longer the hard part")
text(s, 36, 86, 648, 16, "Trained per-screen scorer with the 14B reader, 188 development cases (% of cases)",
     size=12, color=MUTED)
cd = CategoryChartData()
cd.categories = ["Types the right text, if handed a correct screen", "Types the right text", "Finds a right screen"]
cd.add_series("Percent of cases", [45.2, 44.7, 72.3])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Pt(36), Pt(106), Pt(648), Pt(200), cd)
gf.name = "Finding versus reading chart"
ch = gf.chart
ch.has_title = False
ch.has_legend = False
ch.font.size = Pt(13)
ch.font.name = FONT
plot = ch.plots[0]
plot.gap_width = 40
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format = '0.0"%"'
dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(14)
dl.font.bold = True
dl.font.color.rgb = DARK
for i, colr in enumerate([DARK, BAR, RED]):
    pt = plot.series[0].points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = colr
va = ch.value_axis
va.minimum_scale, va.maximum_scale = 0, 85
va.has_major_gridlines = False
va.visible = False
ca = ch.category_axis
ca.format.line.color.rgb = LINE
ca.tick_labels.font.size = Pt(13)
ca.tick_labels.font.color.rgb = DARK
card(s, 36, 318, 648, 56, fill=ROSE, name="Result 2 proves")
text(s, 50, 322, 620, 48, [[("What it proves: ", {"bold": True, "color": DEEP}),
                            ("the selector now finds the screen, but reading is the bottleneck: even a screen known to "
                             "be correct lifts typed-text accuracy only from 44.7% to 45.2%.", {})]],
     size=14, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Result two: finding the screen is no longer the hard part. The trained scorer finds a right screen in 72.3 "
         "percent of cases, but the reader types the right text in only 44.7 percent; of the 136 right screens, 62 still "
         "give the wrong text. And when we hand the reader a screen we know is correct, accuracy rises only to 45.2 "
         "percent. So the remaining bottleneck is reading: picking the right string on the screen and copying it "
         "exactly. The report also covers look-back distance, ablations and two evaluation pitfalls.")

# ---------------------------------------------------------------- 16 related work
s = new_slide("Related work: how we differ")
for x, w, lab in [(50, 180, "Line of work"), (246, 208, "What they do"), (470, 200, "What we do")]:
    text(s, x, 88, w, 14, lab, size=11, color=MUTED, bold=True)
rows = [
    ("GUI agents", "SeeClick, OS-Atlas, UI-TARS",
     "Decide where to act on the current screen.", "Find which earlier screen holds the answer."),
    ("Memory for GUI agents", "Mobile-Agent-v2, GUI-Rise, PAL-UI",
     "Save notes before knowing what is needed; PAL-UI learns from a teacher model.",
     "Search the history once we know what to type; labels come free from the log."),
    ("Long-context models", "Lost in the Middle, RULER",
     "Use long inputs unevenly.", "Pick one screen instead of reading everything at once."),
    ("Distant supervision", "DrQA, DPR",
     "Text that contains a known answer becomes a training label.", "The same idea, applied to phone screens."),
]
for k, (name, ex, they, we) in enumerate(rows):
    y = 106 + k * 67
    card(s, 36, y, 648, 61, name=f"Related row {k + 1}")
    text(s, 50, y + 8, 186, 46, [{"runs": name, "bold": True, "color": DARK, "size": 13, "after": 2},
                                 {"runs": ex, "color": MUTED, "size": 10}], size=13, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 246, y + 8, 208, 46, they, size=12, color=GREY, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 470, y + 8, 200, 46, we, size=12, color=DEEP, bold=True, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Briefly, how we differ from related work. GUI agents mostly decide where to act on the current screen; we "
         "find which earlier screen holds the answer. Memory methods save notes before they know what will be needed, "
         "and PAL-UI learns look-back from a teacher model; we search the history once we know what to type, with "
         "labels from the log. Long-context models use long inputs unevenly, so we select one screen. And our labeling "
         "is distant supervision, like DrQA and DPR, applied to phone screens.")

# ---------------------------------------------------------------- conclusion: the three contributions
s = new_slide("Conclusion: our three contributions")
rows = [
    ("1", "We verify that prompting alone often misses the source screen",
     "On 188 GUI-Odyssey typing steps: untrained 7B per-screen 50.0%, 14B full-history prompt 54.8%, screen "
     "index 41.0%. Later steps are harder: 68.0% at t ≤ 15 vs 46.0% at t ≥ 16.",
     "≤ 54.8%", "prompted localization"),
    ("2", "We solve the missing labels: derive them from demonstrations",
     "Typed text matched against earlier OCR gives 2,861 case–screen labels from 188 entries with zero "
     "human labels; two 7B selectors are trained on them.",
     "50.0 → 72.3%", "localization, same model, prompt and reader"),
    ("3", "We evaluate extensively",
     "93 held-out cases from disjoint trajectories, two definitions of look-back distance, and selector and "
     "reader ablations validate supervision that needs no human annotation.",
     "41.9 → 79.6%", "held-out localization"),
]
for k, (n, head, body, big, lab) in enumerate(rows):
    y = 88 + k * 84
    card(s, 36, y, 648, 78, name=f"Contribution {n}")
    number_badge(s, 50, y + 10, n, d=30)
    text(s, 94, y + 8, 440, 20, head, size=14, color=DARK, bold=True)
    text(s, 94, y + 29, 440, 48, body, size=13, color=GREY)
    text(s, 540, y + 10, 136, 32, big, size=21, color=RED, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 540, y + 44, 136, 28, lab, size=10, color=MUTED, align=PP_ALIGN.CENTER)
text(s, 36, 344, 648, 30, [[("Limitations: ", {"bold": True, "color": DARK}),
                            ("all results come from one dataset (GUI-Odyssey) and one OCR tool, a matching string can "
                             "occasionally be a coincidence, and we evaluate single typing steps rather than "
                             "complete tasks.", {})]], size=12, color=GREY, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "To conclude, our three contributions. First, we verified the problem: prompting alone finds the right screen "
         "only about half the time, and less often late in a task. Second, we solved the missing-label problem: the "
         "typed text in the log gives 2,861 labels with zero human labels, and training lifts a 7B model from 50.0 to "
         "72.3 percent. Third, we evaluated extensively, including 93 held-out cases where it goes from 41.9 to 79.6 "
         "percent. The main limitations: all results come from one dataset and one OCR tool, a matching string can "
         "occasionally be a coincidence, and we evaluate single typing steps rather than complete tasks.")

# ---------------------------------------------------------------- 16 code
s = new_slide("Code and running snippets")
text(s, 36, 88, 352, 18, "Recompute the main-table counts on a CPU", size=13, color=DARK, bold=True)
code(s, 36, 110, 352, 172, [
    "import json",
    "from pathlib import Path",
    "for s in (\"\", \"_more\"):",
    "  for m in (\"fullhist\", \"scorer\"):",
    "    f = Path(f\"results/{m}_trained{s}_hist_e2e.json\")",
    "    r = json.loads(f.read_text(\"utf-8\"))",
    "    print(m, len(r), sum(x[\"loc\"] for x in r),",
    "          sum(x[\"e2e\"] for x in r))",
    "# fullhist 188 123 80   scorer 188 136 84",
    "# fullhist  93  71 48   scorer  93  74 46",
], size=10.5)
text(s, 404, 88, 280, 18, "Retrain on Linux + CUDA (5 folds)", size=13, color=DARK, bold=True)
code(s, 404, 110, 280, 172, [
    "mkdir -p run-data",
    "cp data/*.json* results/*.json run-data/",
    "bash configure.sh \"$PWD/run-data\"",
    "for f in 0 1 2 3 4; do",
    "  FOLD=$f python src/train_scorer.py",
    "  FOLD=$f python src/train_fullhist.py",
    "done",
    "PREFIX=scorer SRC=trained HIST=1 \\",
    "  python src/read_scorer.py",
    "# held-out: FOLD=ext, SET=_more",
], size=10.5)
card(s, 36, 292, 648, 82, fill=PALE, name="Repository")
text(s, 50, 300, 620, 68, [
    {"runs": [("github.com/WMSlalalala/verifier-supervised-lookback", {"bold": True, "color": TEAL, "link": REPO})],
     "after": 5},
    {"runs": [("src/ ", {"bold": True, "color": DARK}), ("mining, labels, training and reading   ", {}),
              ("data/ ", {"bold": True, "color": DARK}), ("OCR records and labels   ", {}),
              ("results/ ", {"bold": True, "color": DARK}), ("per-case predictions", {})], "size": 12, "after": 4},
    {"runs": "The README maps every table and figure to the files that produce it.", "size": 12},
], size=13, color=GREY)
notes(s, "[9:35-9:55] All code, derived data and per-case predictions are on GitHub. The left snippet recomputes the "
         "main table counts from the saved predictions on a CPU with only the standard library. The right block "
         "retrains both selectors over the five folds and runs the reader; for the held-out batch use FOLD=ext and "
         "SET=_more. The README maps every table and figure to its files.")

# ---------------------------------------------------------------- 17 references
s = new_slide("References")
refs = [
    ("Lu et al.", "GUIOdyssey: cross-app GUI navigation dataset. ICCV 2025."),
    ("Liu et al.", "PAL-UI: Planning with active look-back for vision-based GUI agents. Findings of IJCNLP-AACL 2026."),
    ("Lee et al.", "ReadAgent: A human-inspired reading agent with gist memory. ICML 2024."),
    ("Zhang et al.", "AppAgent: Multimodal agents as smartphone users. CHI 2025."),
    ("Wang et al.", "Mobile-Agent-v2: Mobile device operation assistant. NeurIPS 2024."),
    ("Qin et al.", "UI-TARS: Automated GUI interaction with native agents. arXiv 2025."),
    ("Rawles et al.", "Android in the Wild. NeurIPS Datasets and Benchmarks 2023."),
    ("Li et al.", "On the effects of data scale on UI control agents. NeurIPS D&B 2024."),
    ("Liu et al.", "Lost in the Middle: How language models use long contexts. TACL 2024."),
    ("Hsieh et al.", "RULER: The real context size of long-context LMs. COLM 2024."),
    ("Wu et al.", "Visual Haystacks: A vision-centric needle-in-a-haystack benchmark. ICLR 2025."),
    ("Wang et al.", "Mobile-Agent-E: Self-evolving mobile assistant. arXiv 2025."),
    ("Liu et al.", "GUI-Rise: Structured reasoning and history summarization. NeurIPS 2025."),
    ("Mintz et al.", "Distant supervision for relation extraction without labeled data. ACL-IJCNLP 2009."),
    ("Chen et al.", "Reading Wikipedia to answer open-domain questions (DrQA). ACL 2017."),
    ("Karpukhin et al.", "Dense passage retrieval for open-domain QA. EMNLP 2020."),
    ("Qwen Team", "Qwen2.5 technical report. arXiv 2024."),
    ("Hu et al.", "LoRA: Low-rank adaptation of large language models. ICLR 2022."),
]
half = (len(refs) + 1) // 2
for k, chunk in enumerate((refs[:half], refs[half:])):
    text(s, 36 + k * 332, 88, 316, 284, [
        {"runs": [(f"[{i + 1 + k * half}] ", {"bold": True, "color": DARK}), (a + " ", {"bold": True, "color": DARK}),
                  (b, {})], "after": 5} for i, (a, b) in enumerate(chunk)], size=10, color=GREY)
caption(s, "Full list of 32 references with links in the report (doc/Final-Report.pdf).")
notes(s, "[9:55-10:00] These are the main references; the report lists all 32 with links.")

# ---------------------------------------------------------------- 18 thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
ph = {p.placeholder_format.idx: p for p in s.placeholders}
for idx, (val, x, y, w, h, size, bold, col) in {
    0: ("Thank you", 60, 88, 600, 52, 36, True, DARK),
    1: ("Questions?", 60, 140, 600, 28, 20, False, GREY),
}.items():
    t = ph[idx]
    t.left, t.top, t.width, t.height = Pt(x), Pt(y), Pt(w), Pt(h)
    tf = t.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = val
    style_run(r, size, col, bold)
qr = picture(s, ASSETS / "qr_repo.png", 280, 192, 160, 160, name="Repository QR code")
qr.click_action.hyperlink.address = REPO
notes(s, "Thank you. I'm happy to take questions.\n\nQ&A preparation:\n"
         "1) Coincidental substring matches? Cases need at least three normalized characters and must not appear in "
         "the task; a 20-case spot check found the target visible on every inspected source screen.\n"
         "2) Why OCR text and not screenshots? Exact matching needs text; a vision selector could be trained on the "
         "same labels.\n"
         "3) Difference from PAL-UI? PAL-UI learns when to look back and which frame, from teacher-synthesized "
         "examples; we isolate which screen and get labels from logs for free.\n"
         "4) Does it help a live agent? Not shown yet; it needs a trigger for when to look back and an interactive "
         "evaluation such as AndroidWorld.\n"
         "5) Why does the scorer win at 8-12 screens? It scores each screen independently, so a distant screen is "
         "not crowded out; the effect is significant only under the earliest-copy distance.")

prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides))
