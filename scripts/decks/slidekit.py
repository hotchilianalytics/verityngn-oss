"""Slide builder matching the Perplexity v3 release deck design.

One spec renders two ways: native PPTX shapes (editable, with speaker notes)
and an HTML twin that headless Chrome prints to PDF. The HTML twin exists
because no PPTX renderer is available on the build machine.

Run-level font properties are always written. Paragraph-level ``defRPr``
alone is not applied consistently across PowerPoint, Keynote and LibreOffice.
"""

from __future__ import annotations

import copy
import html
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

W, H = 13.333, 7.5
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


@dataclass(frozen=True)
class Theme:
    footer: str
    bg: str = "0B1420"
    card: str = "142333"
    line: str = "2B4054"
    accent: str = "51DFD0"
    accent2: str = "9CBFFF"
    title: str = "F6F8FB"
    body: str = "ACC0D0"
    foot: str = "6C879C"
    warn: str = "FFAE73"
    amber: str = "FBBF24"
    font: str = "DejaVu Sans"
    mono: str = "DejaVu Sans Mono"


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: str | None
    line: str | None = None
    round: bool = False
    line_w: float = 1.0


@dataclass
class Text:
    x: float
    y: float
    w: float
    h: float
    paras: list[str]
    size: float
    color: str
    bold: bool = False
    italic: bool = False
    align: str = "l"
    mono: bool = False
    anchor: str = "t"
    space_after: float = 5.0


@dataclass
class Image:
    path: Path
    x: float
    y: float
    w: float
    h: float


@dataclass
class Slide:
    theme: Theme
    elements: list = field(default_factory=list)
    notes: str = ""

    # ---- primitives -------------------------------------------------------
    def rect(self, x, y, w, h, fill, line=None, round=False, line_w=1.0):
        self.elements.append(Rect(x, y, w, h, fill, line, round, line_w))

    def text(self, x, y, w, h, paras, size, color, **kw):
        if isinstance(paras, str):
            paras = paras.split("\n")
        self.elements.append(Text(x, y, w, h, list(paras), size, color, **kw))

    def image(self, path, x, y, w, h):
        self.elements.append(Image(Path(path), x, y, w, h))

    # ---- composites --------------------------------------------------------
    def chrome(self, eyebrow, title, subtitle=None, source=None, page=""):
        t = self.theme
        self.rect(0, 0, 0.12, H, t.accent)
        self.text(0.62, 0.38, 11.9, 0.3, eyebrow.upper(), 10.5, t.accent, bold=True)
        self.text(0.62, 0.92, 12.05, 1.1, title, 34 if len(title) <= 42 else 28, t.title, bold=True)
        if subtitle:
            self.text(0.64, 2.08, 11.8, 0.62, subtitle, 17, t.body)
        self.rect(0.62, 6.93, 12.05, 0.01, t.line)
        self.text(0.64, 7.09, 7.0, 0.22, t.footer, 9.5, t.body, bold=True)
        if source:
            self.text(0.65, 6.57, 12.0, 0.3, source, 8.8, t.foot)
        self.text(11.6, 7.07, 1.04, 0.23, page, 10, t.body, align="r")

    def card(self, x, y, w, h, label=None, heading=None, body=None, edge=None,
             label_color=None, heading_size=18.5, body_size=13.5, pad=0.2):
        t = self.theme
        self.rect(x, y, w, h, t.card, t.line, round=True)
        if edge:
            self.rect(x, y, 0.06, h, edge)
        cy = y + 0.16
        if label:
            self.text(x + pad, cy, w - 2 * pad, 0.28, label.upper(), 10.5, label_color or t.accent, bold=True)
            cy += 0.36
        if heading:
            lines = heading.count("\n") + 1
            self.text(x + pad, cy, w - 2 * pad, 0.36 * lines * heading_size / 18.5, heading,
                      heading_size, t.title, bold=True)
            cy += 0.42 * lines * heading_size / 18.5 + 0.06
        if body:
            self.text(x + pad, cy, w - 2 * pad, y + h - cy - 0.1, body, body_size, t.body)

    def stat(self, x, y, w, h, number, label, sub=None, color=None, number_size=50):
        t = self.theme
        self.rect(x, y, w, h, t.card, t.line, round=True)
        self.text(x + 0.22, y + 0.16, w - 0.44, 0.95, number, number_size, color or t.accent, bold=True)
        self.text(x + 0.22, y + 0.16 + number_size / 50 * 1.08, w - 0.44, 0.4, label, 19, t.title, bold=True)
        if sub:
            self.text(x + 0.22, y + 0.16 + number_size / 50 * 1.08 + 0.5, w - 0.44, h - 1.9, sub, 12.5, t.body)

    def band(self, text, color=None, y=6.02, h=0.48):
        t = self.theme
        self.rect(0.64, y, 12.03, h, t.card)
        self.text(0.83, y + 0.1, 11.65, h - 0.12, text, 14.5, color or t.accent, bold=True)

    def table(self, x, y, widths, rows, row_h=0.42, header=True, size=12.5,
              cell_style=None):
        """rows: list of lists of str. cell_style(r, c, value) -> (fill, color, bold) or None."""
        t = self.theme
        for r, row in enumerate(rows):
            cx = x
            is_head = header and r == 0
            for c, value in enumerate(row):
                w = widths[c]
                fill, color, bold = (t.line, t.title, True) if is_head else (t.card, t.body, c == 0)
                if not is_head and cell_style:
                    style = cell_style(r, c, value)
                    if style:
                        fill, color, bold = style
                self.rect(cx, y, w - 0.04, row_h - 0.04, fill)
                self.text(cx + 0.12, y + 0.07, w - 0.28, row_h - 0.12, value,
                          (10.5 if is_head else size), color, bold=bold)
                cx += w
            y += row_h
        return y

    def notes_with_sources(self, talk: str, sources: list[str], verified="27 October 2026"):
        self.notes = talk.strip() + "\n\n\n\nSources (verified " + verified + "):\n" + "\n".join(sources)


# ---- PPTX rendering ---------------------------------------------------------

_ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
_ANCHOR = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}


def _rgb(hex_):
    return RGBColor.from_string(hex_)


def render_pptx_slide(prs: Presentation, spec: Slide):
    layout = next(l for l in prs.slide_layouts if l.name == "Blank")
    s = prs.slides.add_slide(layout)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = _rgb(spec.theme.bg)
    for e in spec.elements:
        if isinstance(e, Rect):
            shp = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE if e.round else MSO_SHAPE.RECTANGLE,
                Inches(e.x), Inches(e.y), Inches(e.w), Inches(e.h),
            )
            if e.round:
                shp.adjustments[0] = 0.1
            if e.fill:
                shp.fill.solid()
                shp.fill.fore_color.rgb = _rgb(e.fill)
            else:
                shp.fill.background()
            if e.line:
                shp.line.color.rgb = _rgb(e.line)
                shp.line.width = Pt(e.line_w)
            else:
                shp.line.fill.background()
            shp.shadow.inherit = False
        elif isinstance(e, Text):
            tb = s.shapes.add_textbox(Inches(e.x), Inches(e.y), Inches(e.w), Inches(e.h))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.vertical_anchor = _ANCHOR[e.anchor]
            for i, para in enumerate(e.paras):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.alignment = _ALIGN[e.align]
                p.space_after = Pt(e.space_after)
                run = p.add_run()
                run.text = para
                f = run.font
                f.size = Pt(e.size)
                f.bold = e.bold
                f.italic = e.italic
                f.name = spec.theme.mono if e.mono else spec.theme.font
                f.color.rgb = _rgb(e.color)
        elif isinstance(e, Image):
            s.shapes.add_picture(str(e.path), Inches(e.x), Inches(e.y), Inches(e.w), Inches(e.h))
    if spec.notes:
        s.notes_slide.notes_text_frame.text = spec.notes
    return s


def move_slide(prs: Presentation, slide, new_index: int):
    lst = prs.slides._sldIdLst
    for sld_id in list(lst):
        if prs.slides.part.related_part(sld_id.rId) is slide.part:
            lst.remove(sld_id)
            lst.insert(new_index, sld_id)
            return
    raise ValueError("slide not found")


def promote_paragraph_defaults(prs: Presentation) -> int:
    """Copy pPr/defRPr font settings onto each run's rPr where the run has none."""
    changed = 0
    for slide in prs.slides:
        for shp in slide.shapes:
            if not shp.has_text_frame:
                continue
            for p in shp.text_frame.paragraphs:
                pPr = p._p.pPr
                d = pPr.find(qn("a:defRPr")) if pPr is not None else None
                if d is None:
                    continue
                for r in p.runs:
                    rPr = r._r.get_or_add_rPr()
                    for attr in ("sz", "b", "i"):
                        if d.get(attr) is not None and rPr.get(attr) is None:
                            rPr.set(attr, d.get(attr))
                    fill = d.find(qn("a:solidFill"))
                    if fill is not None and rPr.find(qn("a:solidFill")) is None:
                        rPr.insert(0, copy.deepcopy(fill))
                    latin = d.find(qn("a:latin"))
                    if latin is not None and rPr.find(qn("a:latin")) is None:
                        rPr.append(copy.deepcopy(latin))
                    changed += 1
    return changed


# ---- HTML / PDF rendering --------------------------------------------------

def _html_element(e, theme: Theme) -> str:
    pos = f"left:{e.x}in;top:{e.y}in;width:{e.w}in;height:{e.h}in;"
    if isinstance(e, Rect):
        bg = f"background:#{e.fill};" if e.fill else ""
        border = f"border:{e.line_w}pt solid #{e.line};" if e.line else ""
        radius = f"border-radius:{0.1 * min(e.w, e.h):.3f}in;" if e.round else ""
        return f'<div class="r" style="{pos}{bg}{border}{radius}"></div>'
    if isinstance(e, Text):
        family = theme.mono if e.mono else theme.font
        fallback = "'Menlo',monospace" if e.mono else "'Helvetica Neue',Arial,sans-serif"
        just = {"t": "flex-start", "m": "center", "b": "flex-end"}[e.anchor]
        align = {"l": "left", "c": "center", "r": "right"}[e.align]
        style = (
            f"{pos}font-family:'{family}',{fallback};font-size:{e.size}pt;color:#{e.color};"
            f"font-weight:{700 if e.bold else 400};font-style:{'italic' if e.italic else 'normal'};"
            f"text-align:{align};justify-content:{just};"
        )
        paras = "".join(
            f'<p style="margin:0 0 {e.space_after}pt">{html.escape(p) or "&nbsp;"}</p>' for p in e.paras
        )
        return f'<div class="t" style="{style}">{paras}</div>'
    if isinstance(e, Image):
        return f'<img class="r" src="{e.path.resolve().as_uri()}" style="{pos}object-fit:contain"/>'
    raise TypeError(e)


def render_html(slides: list[Slide], title: str) -> str:
    body = []
    for spec in slides:
        inner = "".join(_html_element(e, spec.theme) for e in spec.elements)
        body.append(f'<section class="slide" style="background:#{spec.theme.bg}">{inner}</section>')
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><title>{html.escape(title)}</title>
<style>
@page {{ size: {W}in {H}in; margin: 0; }}
html,body {{ margin:0; padding:0; }}
.slide {{ position:relative; width:{W}in; height:{H}in; overflow:hidden; page-break-after:always; }}
.r, .t {{ position:absolute; box-sizing:border-box; }}
.t {{ display:flex; flex-direction:column; line-height:1.18; white-space:pre-wrap; }}
</style></head><body>{''.join(body)}</body></html>"""


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--virtual-time-budget=4000", f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
        check=True, capture_output=True, timeout=180,
    )


def write_outputs(slides: list[Slide], pptx_path: Path, pdf_path: Path | None, template: Path,
                  title: str) -> None:
    prs = Presentation(str(template))
    # keep the template's page size and theme, drop its slides
    lst = prs.slides._sldIdLst
    for sld_id in list(lst):
        prs.part.drop_rel(sld_id.rId)
        lst.remove(sld_id)
    for spec in slides:
        render_pptx_slide(prs, spec)
    prs.save(str(pptx_path))
    if pdf_path:
        html_path = pdf_path.with_suffix(".html")
        html_path.write_text(render_html(slides, title), encoding="utf-8")
        html_to_pdf(html_path, pdf_path)
