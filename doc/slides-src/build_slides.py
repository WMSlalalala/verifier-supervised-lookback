"""Build the NC State presentation for Verifier-Supervised Look-Back.

Usage: python build_slides.py ncsu_template.pptx assets Slides.pptx
       powershell -File export_pdf.ps1 -In <full path to Slides.pptx> -Out <full path to Slides.pdf>   (needs PowerPoint)

The template supplies the official NC State master, layouts and masthead;
any existing slide is removed and the talk is rebuilt from scratch.
"""
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
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


def notes(slide, body):
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

# ---------------------------------------------------------------- 4 key idea
s = new_slide("The missing label is already in the demonstration")
text(s, 36, 86, 648, 20, [[("To train look-back, we need one label: ", {"bold": True, "color": DARK}),
                           ("which earlier screen holds the answer?", {})]], size=15, color=GREY)
bw, gap, x0, ybox = 48, 6, 36, 142
for i in range(12):
    x = x0 + i * (bw + gap)
    hit, cur = i in (4, 5, 6), i == 11
    b = rect(s, x, ybox, bw, 50, ROSE if hit else (WHITE if cur else PALE),
             line=RED if hit else (DARK if cur else LINE), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08,
             name=f"Screen {i}")
    label_shape(b, f"Screen\n{i}", 10, DEEP if hit else DARK, bold=hit or cur)
    if i < 11:
        chip = rect(s, x + 10, ybox + 56, bw - 20, 18, RED if hit else WHITE, line=None if hit else LINE,
                    shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3, name=f"Label {i}")
        label_shape(chip, "1" if hit else "0", 11, WHITE if hit else MUTED)
text(s, x0 + 4 * (bw + gap) - 8, 116, 3 * bw + 2 * gap + 16, 22, "OCR contains the typed text", size=11,
     color=RED, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)
text(s, 440, 112, 244, 26,
     [[("TYPE at step 11: ", {}), ("“Electronic Study”", {"bold": True})]], size=11, color=DARK,
     align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.BOTTOM)
text(s, x0 + 11 * (bw + gap) - 10, ybox + 56, bw + 20, 30, "absent\nnow", size=10, color=MUTED,
     align=PP_ALIGN.CENTER)
steps = [
    ("1", "Read the typed text", "The demonstration stores the string the user entered at step t."),
    ("2", "Search earlier screens", "Run OCR on screens 0 ... t−1 and test whether the normalized "
                                    "string occurs."),
    ("3", "Label all matches", "Matching screens are positives, all others negatives: "
                               "Vₜ = { i < t : aₜ ⊂ OCR(i) }."),
]
for k, (n, head, body) in enumerate(steps):
    x = 36 + k * 222
    number_badge(s, x, 236, n, d=26)
    text(s, x + 36, 236, 168, 26, head, size=14, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x, 268, 204, 60, body, size=13, color=GREY)
card(s, 36, 334, 648, 40, fill=ROSE, name="Idea takeaway")
text(s, 50, 338, 620, 32, [[("No human annotation, no teacher model. ", {"bold": True, "color": DEEP}),
                            ("At test time the typed text is hidden, so the model must find the screen from the task "
                             "and the screens alone.", {})]], size=13, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[1:50-2:40] So what training look-back really lacks is one label: at each text entry, which earlier "
         "screen holds the answer. Our observation is that the demonstration already contains it, because it records "
         "the text the user actually typed. In the example, the log says the user typed Electronic Study at step 11. "
         "We run OCR on every earlier screen and search for that string. Screens 4, 5 and 6 contain it, so they get "
         "label 1, and every other screen gets 0. This needs no human annotation and no teacher model. At test time "
         "the typed text is hidden, so the model must find the screen from the task and the screens alone.")

# ---------------------------------------------------------------- 5 contributions
s = new_slide("Contributions")
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
    y = 92 + k * 94
    card(s, 36, y, 648, 84, name=f"Contribution {n}")
    number_badge(s, 50, y + 12, n, d=30)
    text(s, 94, y + 10, 440, 20, head, size=14, color=DARK, bold=True)
    text(s, 94, y + 33, 440, 48, body, size=13, color=GREY)
    text(s, 540, y + 14, 136, 32, big, size=21, color=RED, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 540, y + 48, 136, 28, lab, size=10, color=MUTED, align=PP_ALIGN.CENTER)
notes(s, "[2:40-3:15] This gives three contributions. First, we verify the problem: prompting alone tops out "
         "around 55 percent localization and gets worse late in a trajectory. Second, we solve the missing-label "
         "problem: from 188 logged entries we derive 2,861 case-screen labels with zero human labels, and training "
         "lifts a 7B per-screen model from 50.0 to 72.3 percent with the same prompt and reader. Third, we evaluate "
         "extensively, including 93 held-out cases where localization goes from 41.9 to 79.6 percent.")

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
notes(s, "[3:55-4:35] Step one is how we get the labels. The log tells us the user typed Electronic Study. We search "
         "the OCR of every earlier screen for that text: screens 4, 5 and 6 contain it, so they get label 1, and the "
         "others get 0. We only keep steps where the text is gone from the current screen but appeared earlier, so "
         "the model really has to look back. This turns 188 typing steps into 2,861 labeled screens, with no human "
         "labels at all.")

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

# ---------------------------------------------------------------- 10 main results
s = new_slide("Main results: derived labels improve selection")
rows = [["", "Development (n = 188)", "", "Held-out (n = 93)", ""],
        ["Selector", "Loc.", "Text", "Loc.", "Text"],
        ["Prompted screen index (14B)", "41.0", "23.9", "37.6", "18.3"],
        ["Prompted full history (14B)", "54.8", "31.4", "59.1", "23.7"],
        ["Untrained per-screen (7B)", "50.0", "35.1", "41.9", "–"],
        ["Trained full history (7B)", "65.4", "42.6", "76.3", "51.6"],
        ["Trained per-screen (7B)", "72.3", "44.7", "79.6", "49.5"]]
table(s, 36, 90, [180, 66, 66, 66, 66], [22, 22] + [24] * 5, rows, size=12, focus=(5, 6),
      strong={(6, 1), (6, 2), (6, 3), (5, 4)}, name="Main results table", header_rows=2,
      merges=(((0, 1), (0, 2)), ((0, 3), (0, 4))))
text(s, 36, 258, 444, 12, "Localization and typed-text accuracy, % of cases; development uses 5-fold CV.",
     size=10, color=MUTED)
text(s, 36, 276, 444, 100, [
    {"runs": [("Same model, prompt and reader: ", {"bold": True, "color": DARK}),
              ("+22.3 pts localization (52 wins, 10 losses, p < 0.001); typed text 66 → 84 cases (p = 0.0013).",
               {})], "bullet": True, "after": 5},
    {"runs": [("Training beats a larger prompt: ", {"bold": True, "color": DARK}),
              ("trained full history 123 vs 103 of 188 for the 14B prompt (p = 0.019).", {})],
     "bullet": True, "after": 5},
    {"runs": [("Trained selectors are close: ", {"bold": True, "color": DARK}),
              ("scorer +13 sources (p = 0.086), +4 texts (p = 0.45).", {})], "bullet": True},
], size=13, color=GREY)
for k, (big, lab) in enumerate([("72.3%", "development localization\n(untrained: 50.0%)"),
                                ("79.6%", "held-out localization\n(untrained: 41.9%)")]):
    y = 90 + k * 144
    card(s, 500, y, 184, 134, fill=ROSE if k == 0 else PALE, name=f"Callout {big}")
    text(s, 512, y + 18, 160, 50, big, size=40, color=RED, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 512, y + 76, 160, 44, lab, size=12, color=DARK, align=PP_ALIGN.CENTER)
notes(s, "[6:00-6:50] Main results. With the base model, prompt and reader fixed, training raises the per-screen "
         "model from 50.0 to 72.3 percent localization: 52 cases flip to correct and 10 flip back, p below 0.001. "
         "Typed-text accuracy rises from 35.1 to 44.7 percent. On the held-out set, localization goes from 41.9 to "
         "79.6 percent. The trained full-history selector also beats the larger 14B prompt, 123 versus 103 of 188. "
         "The two trained selectors are statistically close: both architectures benefit from the same labels, and "
         "the remaining difference between them is not reliable.")

# ---------------------------------------------------------------- 11 finding vs reading
s = new_slide("Finding the screen is not the same as reading it")
card(s, 36, 90, 268, 116, fill=ROSE, name="Reading gap")
text(s, 50, 98, 240, 44, "62 of 136", size=34, color=RED, bold=True)
text(s, 50, 146, 240, 56, "correct selections by the trained scorer still produce the wrong text (development)",
     size=13, color=DARK)
card(s, 36, 214, 268, 82, name="Recovery")
text(s, 50, 220, 240, 30, "10 of 52", size=22, color=DARK, bold=True)
text(s, 50, 250, 240, 42, "invalid selections where the reader still recovers the text from the history",
     size=12, color=GREY)
text(s, 36, 304, 268, 70, [
    {"runs": "Held-out: 43 of 74 correct selections give the right text.", "bullet": True, "after": 4},
    {"runs": "Pandora → Tumblr: both selectors chose valid screens; both readers missed the title.",
     "bullet": True}], size=12, color=GREY)
cd = CategoryChartData()
cats = ["Random earlier screen", "Most recent screen", "Scorer's top screen", "Scorer's top two", "Known valid screen"]
vals = [36.7, 38.8, 44.7, 45.2, 45.2]
cd.categories = cats
cd.add_series("Typed-text accuracy (%)", vals)
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Pt(318), Pt(108), Pt(366), Pt(220), cd)
gf.name = "Reader control chart"
ch = gf.chart
ch.has_title = False
ch.has_legend = False
ch.font.size = Pt(11)
ch.font.name = FONT
plot = ch.plots[0]
plot.gap_width = 55
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format = "0.0"
dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(11)
dl.font.bold = True
dl.font.color.rgb = DARK
for i, colr in enumerate([BAR, BAR, RED, RED, DARK]):
    pt = plot.series[0].points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = colr
va = ch.value_axis
va.minimum_scale, va.maximum_scale, va.major_unit = 0, 50, 10
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = LINE
va.format.line.fill.background()
va.tick_labels.font.size = Pt(10)
va.tick_labels.font.color.rgb = MUTED
ca = ch.category_axis
ca.format.line.color.rgb = LINE
ca.tick_labels.font.size = Pt(11)
ca.tick_labels.font.color.rgb = DARK
text(s, 318, 88, 366, 18, "Typed-text accuracy (%) by the screen the reader sees marked", size=12, color=DARK,
     bold=True)
card(s, 318, 334, 366, 40, fill=PALE, name="Reading takeaway")
text(s, 330, 338, 342, 32, "Reading is now the bottleneck: marking a known-valid screen adds one correct entry "
                           "(85 vs 84).", size=12, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[6:50-7:30] But finding the screen is not the same as reading it. Of the scorer's 136 correct selections, "
         "62 still produce the wrong text. Conversely, 10 of 52 wrong selections still recover the text, because the "
         "full history stays in the reader's context. The chart varies only which screen the reader sees marked: "
         "marking a screen we know is valid adds just one correct entry over the scorer's choice, while marking the "
         "most recent or a random screen drops accuracy below 39 percent. So reading is now the bottleneck, as in the "
         "Pandora example, where both selectors chose valid screens and both readers missed the title.")

# ---------------------------------------------------------------- 12 distance
s = new_slide("How far back? It depends on which copy you count")
picture(s, ASSETS / "distance.png", 36, 92, 430, 190, name="Distance figure")
text(s, 36, 286, 430, 28, "Localization by distance to the earliest (A) or most recent (B) matching screen; both "
                          "panels split the same 188 development predictions.", size=10, color=MUTED)
text(s, 484, 90, 200, 230, [
    {"runs": [("The answer recurs ", {"bold": True, "color": DARK}), ("in 111 of 188 cases.", {})], "after": 8},
    {"runs": [("Two distances: ", {"bold": True, "color": DARK}),
              ("to the earliest copy (median 7) or the most recent copy (median 4).", {})], "after": 8},
    {"runs": [("Earliest copy, 8–12 screens: ", {"bold": True, "color": DARK}),
              ("scorer 78.2% vs trained full history 56.4% (p = 0.003).", {})], "after": 8},
    {"runs": [("Most recent copy, 8–12: ", {"bold": True, "color": DARK}),
              ("only 23 cases; 69.6% vs 47.8% (p = 0.131).", {})], "after": 8},
    {"runs": [("Most recent copy ≥ 13 (14 cases): ", {"bold": True, "color": DARK}),
              ("prompt 8, trained full history 4, scorer 3.", {})]},
], size=12, color=GREY)
card(s, 36, 326, 648, 48, fill=ROSE, name="Distance takeaway")
text(s, 50, 330, 620, 40, [[("Takeaway: ", {"bold": True, "color": DEEP}),
                            ("distance conclusions depend on which occurrence is measured, and the groups are too small "
                             "for a precise cutoff between selectors.", {})]], size=13, color=DARK,
     anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[7:30-8:10] How far back must the model look? The answer recurs on several screens in 111 of 188 cases, "
         "so distance can be measured to the earliest copy or to the most recent one; the medians are 7 and 4 "
         "screens. Grouped by the earliest copy, the scorer's advantage concentrates at 8 to 12 screens, 78 versus "
         "56 percent, p equals 0.003. Grouped by the most recent copy, that band has only 23 cases and the difference "
         "is not significant. So conclusions about distance depend on which copy you count, and our groups are too "
         "small for a precise cutoff.")

# ---------------------------------------------------------------- 13 ablations + filters
s = new_slide("Ablations and two evaluation filters")
text(s, 36, 88, 316, 18, "Selector ablations (development localization)", size=13, color=DARK, bold=True)
table(s, 36, 110, [214, 102], [24] + [23] * 4,
      [["Variant", "Loc. (%)"], ["7B, distance, weight 3 (default)", "72.3"], ["Omit distance header", "70.7"],
       ["Positive weight 1", "72.3"], ["Smaller 3B model", "68.1"]], size=12, focus=(1,), name="Ablation table")
text(s, 36, 232, 316, 140, [
    {"runs": "Distance header: −1.6 pts (p = 0.61); class weights: no change.", "bullet": True, "after": 4},
    {"runs": "3B is weaker overall but better at t ≥ 20 (48.1% vs 37.0%).", "bullet": True, "after": 4},
    {"runs": "Screen index on the first 85 cases: 49.4% vs 65.9% with full OCR; a preference-trained writer "
             "reaches 45.9%.", "bullet": True, "after": 4},
    {"runs": "BM25: 10.6% with the task as query, 92.9% with the hidden answer.", "bullet": True},
], size=12, color=GREY)
filters = [("Filter 1: credit any valid screen",
            "40 of the first 85 cases have several valid screens. Earliest-only scoring understates the screen "
            "index by 15.3 pts and the full-history prompt by 11.8 pts.", "−15.3 pts", "if earliest-only"),
           ("Filter 2: remove current-screen leakage",
            "Unfiltered long batch (127 cases): a recent-screen rule led the full-history prompt. After removing 74 "
            "leaked cases, it trailed on the remaining 53. Finding withdrawn.", "+17.3\n→ −22.7",
            "points, before vs after")]
for k, (head, body, big, lab) in enumerate(filters):
    y = 88 + k * 146
    card(s, 368, y, 316, 138, fill=ROSE if k else PALE, name=f"Filter {k + 1}")
    text(s, 382, y + 10, 288, 20, head, size=14, color=DARK, bold=True)
    text(s, 382, y + 34, 190, 98, body, size=12, color=GREY)
    text(s, 578, y + 34, 100, 48, big, size=18 if k else 20, color=RED, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 578, y + 86, 100, 30, lab, size=10, color=MUTED, align=PP_ALIGN.CENTER)
notes(s, "[8:10-8:45] Ablations show the scorer is insensitive to its settings: removing the distance header or the "
         "class weight barely changes localization, and a 3B scorer is a bit weaker overall but better at very late "
         "steps. The screen index stays well below full OCR even with a preference-trained writer, and BM25 shows the "
         "difficulty is not knowing what to search for. Two evaluation filters matter more. First, credit any valid "
         "screen: scoring only the earliest one understates the index by 15 points. Second, remove cases whose answer "
         "is still on the current screen: before filtering, a recent-screen rule looked 17 points better than the "
         "full-history prompt; after filtering, it was 23 points worse, and we withdrew that finding.")

# ---------------------------------------------------------------- 14 related work
s = new_slide("Related work")
grid = [("GUI agents and datasets",
         "AITW · AndroidControl · AITZ · AMEX · GUI-Odyssey · AndroidWorld · Auto-GUI · "
         "CogAgent · SeeClick · OS-Atlas · UI-TARS",
         "Mostly decide where to act on the current screen; we localize an earlier screen in the history."),
        ("History and memory",
         "OdysseyAgent · Mobile-Agent-v2 · Mobile-Agent-E · GUI-Rise · AppAgent · Synapse · "
         "AWM · PAL-UI",
         "Keep information before the need is known, or learn from teacher-made labels; we label from the typed "
         "text."),
        ("Long-context retrieval",
         "Lost in the Middle · RULER · Visual Haystacks · ReadAgent · MemGPT",
         "Long inputs are used unevenly; our histories are short but answers recur, so we report two distances."),
        ("Distant supervision",
         "Mintz et al. · DrQA · ORQA · DPR · monoT5 · RankGPT",
         "Answer-string matches as labels; we keep every matching screen and compare pointwise vs listwise "
         "selection.")]
for k, (head, works, diff) in enumerate(grid):
    x, y = 36 + (k % 2) * 332, 90 + (k // 2) * 144
    card(s, x, y, 316, 134, name=f"Related {head}")
    text(s, x + 14, y + 10, 288, 20, head, size=15, color=RED, bold=True)
    text(s, x + 14, y + 34, 288, 44, works, size=11, color=MUTED)
    text(s, x + 14, y + 80, 288, 50, diff, size=13, color=DARK)
notes(s, "[8:45-9:05] Briefly on related work. GUI agent work mostly decides where to act on the current screen. "
         "Memory methods decide what to keep before the need is known, or rely on teacher-made labels like PAL-UI. "
         "Long-context work shows that long inputs are used unevenly. And our labeling is distant supervision in the "
         "spirit of DrQA and DPR, applied to GUI trajectories.")

# ---------------------------------------------------------------- 15 conclusion + limitations
s = new_slide("Conclusion and limitations")
card(s, 36, 90, 316, 284, fill=ROSE, name="Conclusion")
text(s, 50, 100, 288, 22, "Conclusion", size=16, color=DEEP, bold=True)
text(s, 50, 130, 290, 236, [
    {"runs": "A recorded text entry already tells us which earlier screens hold the answer.", "bullet": True,
     "after": 10},
    {"runs": [("Zero-human labels lift localization ", {}), ("50.0 → 72.3%", {"bold": True, "color": RED}),
              (" (development) and ", {}), ("41.9 → 79.6%", {"bold": True, "color": RED}),
              (" (held-out).", {})], "bullet": True, "after": 10},
    {"runs": "Reading is the remaining bottleneck: 62 of 136 correct selections still give the wrong text.",
     "bullet": True, "after": 10},
    {"runs": [("Next: ", {"bold": True, "color": DEEP}),
              ("improve reading, and let a live agent decide when to look back (e.g., on AndroidWorld).", {})],
     "bullet": True},
], size=14, color=DARK)
card(s, 368, 90, 316, 284, name="Limitations")
text(s, 382, 100, 288, 22, "Limitations", size=16, color=DARK, bold=True)
text(s, 382, 130, 290, 236, [
    {"runs": "One corpus (GUI-Odyssey) and one OCR engine.", "bullet": True, "after": 8},
    {"runs": "Substring matches can be coincidental; OCR errors or paraphrases can hide true matches.",
     "bullet": True, "after": 8},
    {"runs": "A 20-case spot check confirms visible evidence (5 typed earlier), not that users needed memory.",
     "bullet": True, "after": 8},
    {"runs": "Localization reuses the labeling criterion, text credit allows substrings, and neither metric measures "
             "whole-task success.", "bullet": True},
], size=13, color=GREY)
notes(s, "[9:05-9:35] To conclude: a recorded text entry already tells us which earlier screens hold the answer. "
         "Training on these zero-human labels lifts localization from 50 to 72 percent on development and from 42 to "
         "80 percent on held-out cases, and reading is now the bottleneck. Limitations: one corpus and one OCR "
         "engine; substring matches can be coincidental or missed; our spot check confirms visible evidence, not that "
         "users needed memory; and our metrics measure one typing decision, not whole-task success.")

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
