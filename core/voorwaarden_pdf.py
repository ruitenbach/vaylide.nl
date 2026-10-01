"""De algemene voorwaarden als verzorgde pdf (bijlage bij de bestelbevestiging en download op de site).

De pdf wordt telkens opgebouwd uit het vaste sjabloon van de gevraagde versie (core/voorwaarden.py), dus een oude
bestelling krijgt altijd haar eigen versie, nooit stilzwijgend de nieuwste. Met reportlab (BSD-licentie, pure Python);
standaardletters (Times en Helvetica), zodat er niets extra's op de server nodig is.
"""
from __future__ import annotations

import html
import io
import re
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

INK = "#26211D"
GOLD = "#7A5A2E"
MUTED = "#6B625A"
LINE = "#D6C8B4"
MARK = "#FBF0D9"

# Standaardletters kennen alleen WinAnsi-tekens; enkele andere tekens vertalen we netjes.
_REPLACE = {"→": "->", "←": "<-", "≥": ">=", "≤": "<=", "✓": "v", " ": " ", "‑": "-"}


def _clean(text: str) -> str:
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text


class _Blocks(HTMLParser):
    """Zet de eenvoudige voorwaarden-HTML (h2, h3, p, ul/li, a, strong, mark) om naar blokken met reportlab-opmaak."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self.kind = None
        self.buf: list[str] = []
        self.href = None
        self.link_text: list[str] = []

    def _flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        if self.kind and text:
            self.blocks.append((self.kind, text))
        self.kind, self.buf = None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("h2", "h3", "p", "li"):
            self._flush()
            self.kind = tag
        elif tag in ("strong", "b"):
            self.buf.append("<b>")
        elif tag in ("em", "i"):
            self.buf.append("<i>")
        elif tag == "mark":
            self.buf.append(f'<font backColor="{MARK}">')
        elif tag == "a":
            self.href = attrs.get("href") or ""
            self.link_text = []
        elif tag == "br":
            self.buf.append("<br/>")

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "p", "li"):
            self._flush()
        elif tag in ("strong", "b"):
            self.buf.append("</b>")
        elif tag in ("em", "i"):
            self.buf.append("</i>")
        elif tag == "mark":
            self.buf.append("</font>")
        elif tag == "a" and self.href is not None:
            text = "".join(self.link_text)
            href = self.href
            if href.startswith("mailto:") or href.rstrip("/") == html.unescape(text).rstrip("/"):
                self.buf.append(f'<link href="{html.escape(href)}" color="{GOLD}">{text}</link>')
            else:  # beschrijvende link: in een pdf ook het adres tonen, zodat het afgedrukt bruikbaar blijft
                self.buf.append(f'<link href="{html.escape(href)}" color="{GOLD}">{text}</link> ({html.escape(href)})')
            self.href = None

    def handle_data(self, data):
        text = html.escape(_clean(data), quote=False)
        if self.href is not None:
            self.link_text.append(text)
        else:
            self.buf.append(text)


def _terms_html(version: str) -> str:
    from .views import _terms_context
    from .voorwaarden import version_info

    ctx = _terms_context(version)
    return render_to_string(version_info(version)["template"], ctx)


def render_pdf(version: str, *, order_number: str = "", compress: bool = True) -> bytes:
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import HRFlowable, Image, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

    from .voorwaarden import version_info

    info = version_info(version)
    datum = f"{info['date'].day} {_MAANDEN[info['date'].month - 1]} {info['date'].year}"
    parser = _Blocks()
    parser.feed(_terms_html(version))
    parser._flush()

    body = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14.6, textColor=INK, spaceAfter=5)
    h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=13.5, leading=17, textColor=GOLD, spaceBefore=12, spaceAfter=4)
    h3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=INK, spaceBefore=6, spaceAfter=2)
    title = ParagraphStyle("title", fontName="Times-Roman", fontSize=26, leading=30, textColor=INK, alignment=TA_CENTER)
    sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED, alignment=TA_CENTER)

    story = []
    logo = Path(settings.BASE_DIR) / "static" / "img" / "merk" / "vaylide-logo.png"
    if logo.is_file():
        story += [Image(str(logo), width=42 * mm, height=42 * mm * 240 / 350), Spacer(1, 4 * mm)]
    story.append(Paragraph("Algemene voorwaarden", title))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"{info['status']} · versie {datum}", sub))
    if order_number:
        story.append(Paragraph(f"Deze versie hoort bij bestelling <b>{html.escape(order_number)}</b>.", sub))
    if info["status"] == "Concept":
        story.append(Paragraph("Dit is een concept dat nog niet juridisch is beoordeeld.", sub))
    story += [Spacer(1, 5 * mm), HRFlowable(width="100%", thickness=0.6, color=LINE), Spacer(1, 3 * mm)]

    bullets: list = []

    def flush_bullets():
        if bullets:
            story.append(ListFlowable([ListItem(Paragraph(t, body), leftIndent=12) for t in bullets], bulletType="bullet",
                                      start="•", leftIndent=12, bulletColor=GOLD))
            bullets.clear()

    for kind, text in parser.blocks:
        if kind == "li":
            bullets.append(text)
            continue
        flush_bullets()
        if kind == "h2":
            story.append(KeepTogether([Paragraph(text, h2)]))
        elif kind == "h3":
            story.append(Paragraph(text, h3))
        else:
            story.append(Paragraph(text, body))
    flush_bullets()

    voet = f"VAYLIDE · Algemene voorwaarden, versie {datum}" + (f" · bestelling {order_number}" if order_number else "")

    class _Genummerd(rl_canvas.Canvas):
        """Voettekst met 'pagina x van y' (tweede ronde zodra het totaal bekend is)."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self.setFont("Helvetica", 8)
                self.setFillColor(MUTED)
                self.drawString(22 * mm, 12 * mm, voet)
                self.drawRightString(A4[0] - 22 * mm, 12 * mm, f"pagina {self._pageNumber} van {total}")
                super().showPage()
            super().save()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=20 * mm, bottomMargin=22 * mm,
                            title=f"Algemene voorwaarden VAYLIDE, versie {datum}", author="VAYLIDE",
                            subject=f"Algemene voorwaarden versie {version}", pageCompression=1 if compress else 0)
    doc.build(story, canvasmaker=_Genummerd)
    return buf.getvalue()


_MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november",
            "december"]
