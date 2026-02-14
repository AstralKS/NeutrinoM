"""Report generator module.

Produces PDF reports from markdown content using ReportLab (pure Python, no system libs).
Works on Windows, Linux, and macOS without GTK/Pango.
Renders tables as proper ReportLab Table flowables.
"""

import html.parser
import io
import logging
import re
from datetime import datetime
from html import unescape
from typing import Any

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def _markdown_to_html(md: str) -> str:
    return markdown.markdown(md or "*No content available.*", extensions=["tables"])


def _strip_html_to_plain(html_fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(html_fragment)).strip()


# Item is either (tag, text) for block elements or ("table", rows) for a table.
_BlockItem = tuple[str, Any]  # ("h1"|"h2"|"h3"|"h4"|"p"|"li", str) or ("table", list[list[str]])


class _HTMLToFlowablesParser(html.parser.HTMLParser):
    """Parse HTML into block elements and tables. Tables become 2D grids of cell text."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[_BlockItem] = []
        # Block element state
        self._block_tag: str | None = None
        self._block_text: list[str] = []
        # Table state
        self._in_table = False
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._in_cell = False
        self._cell_text: list[str] = []

    def _flush_block(self) -> None:
        if self._block_tag and self._block_text:
            self.items.append((self._block_tag, "".join(self._block_text)))
            self._block_text = []
        self._block_tag = None

    def _flush_cell(self) -> None:
        if self._in_cell:
            self._current_row.append("".join(self._cell_text).strip())
            self._cell_text = []
            self._in_cell = False

    def _flush_row(self) -> None:
        self._flush_cell()
        if self._current_row:
            self._current_table.append(self._current_row)
            self._current_row = []

    def _flush_table(self) -> None:
        self._flush_row()
        if self._current_table:
            self.items.append(("table", [list(row) for row in self._current_table]))
            self._current_table = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._flush_block()
            self._in_table = True
            self._current_table = []
            self._current_row = []
            return
        if tag in ("thead", "tbody", "tfoot"):
            return
        if tag == "tr":
            self._flush_row()
            return
        if tag in ("th", "td"):
            self._flush_cell()
            self._in_cell = True
            return
        if self._in_table:
            return
        # Block elements we emit
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "hr"):
            self._flush_block()
            self._block_tag = tag
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "table":
            self._flush_table()
            self._in_table = False
            return
        if tag in ("tr", "thead", "tbody", "tfoot"):
            self._flush_row()
            return
        if tag in ("th", "td"):
            self._flush_cell()
            return
        if self._in_table:
            return
        # Only close our block when we see the matching end tag (ignore inner tags like </strong>)
        if tag == self._block_tag:
            if self._block_text or self._block_tag == "hr":
                self.items.append((self._block_tag, "".join(self._block_text)))
                self._block_text = []
            self._block_tag = None
        return

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_text.append(data)
            return
        if self._block_tag:
            self._block_text.append(data)
            return
        # Orphan text (e.g. raw text outside any tag): treat as paragraph
        if data.strip():
            self._flush_block()
            self._block_tag = "p"
            self._block_text = [data]
        return

    def flush(self) -> None:
        self._flush_block()
        self._flush_table()
        self._in_table = False
        self._block_tag = None
        self._block_text = []


def _html_to_items(html_body: str) -> list[_BlockItem]:
    """Parse HTML into a list of (tag, content) or ("table", rows)."""
    parser = _HTMLToFlowablesParser()
    parser.feed(html_body)
    parser.flush()
    return parser.items


def _escape_reportlab(s: str) -> str:
    """Escape for reportlab Paragraph (XML-style)."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _make_table_flowable(rows: list[list[str]], styles: Any) -> Table:
    """Build a ReportLab Table from rows of cell text, with header row styling."""
    if not rows:
        return Table([[""]])
    # Each cell can be a string; ReportLab will wrap. Use Paragraph for long text.
    data = []
    for r, row in enumerate(rows):
        data_row = []
        for cell_text in row:
            text = _escape_reportlab(_strip_html_to_plain(cell_text) or cell_text)
            if not text.strip():
                text = " "
            data_row.append(Paragraph(text, styles["Normal"]))
        data.append(data_row)
    t = Table(data, repeatRows=1 if len(data) > 1 else 0)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def generate_pdf(
    report_type: str,
    repo_url: str,
    content_markdown: str,
    model_used: str | None = None,
) -> bytes:
    """Generate a PDF report from markdown content.

    Args:
        report_type: "technical" or "executive"
        repo_url: Repository URL for the report header.
        content_markdown: Full report body in markdown.
        model_used: Optional model name for the report header.

    Returns:
        PDF file as bytes.
    """
    title = (
        "Technical Analysis Report"
        if report_type == "technical"
        else "Executive Intelligence Brief"
    )
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    model = model_used or "Unknown"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        spaceAfter=12,
        borderPadding=0,
        borderWidth=0,
        borderColor=colors.black,
        bottomPadding=4,
    )
    h2_style = ParagraphStyle(
        name="ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceBefore=14,
        spaceAfter=6,
    )
    h3_style = ParagraphStyle(
        name="ReportH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        spaceBefore=10,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=16,
    )
    normal_style = ParagraphStyle(
        name="ReportNormal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=8,
    )
    list_style = ParagraphStyle(
        name="List",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4,
    )
    blockquote_style = ParagraphStyle(
        name="Blockquote",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=24,
        rightIndent=24,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.HexColor("#444444"),
    )
    pre_style = ParagraphStyle(
        name="Pre",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=9,
        leftIndent=12,
        spaceBefore=6,
        spaceAfter=6,
        backColor=colors.HexColor("#f5f5f5"),
        borderPadding=6,
    )

    story: list[Any] = []
    story.append(Paragraph(_escape_reportlab(title), title_style))
    story.append(
        Paragraph(
            _escape_reportlab(f"Repository: {repo_url}<br/>Generated: {generated}<br/>Model: {model}"),
            meta_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    body_html = _markdown_to_html(content_markdown or "*No content available.*")
    items = _html_to_items(body_html)

    for item in items:
        kind = item[0]
        if kind == "table":
            rows = item[1]
            if rows:
                story.append(Spacer(1, 0.4 * cm))
                story.append(_make_table_flowable(rows, styles))
                story.append(Spacer(1, 0.6 * cm))
            continue
        if kind == "hr":
            story.append(Spacer(1, 0.3 * cm))
            continue
        text = _escape_reportlab(_strip_html_to_plain(item[1]) or item[1])
        if not text.strip() and kind != "pre":
            continue
        if kind == "h1":
            story.append(Paragraph(text, title_style))
        elif kind == "h2":
            story.append(Paragraph(text, h2_style))
        elif kind in ("h3", "h4", "h5", "h6"):
            story.append(Paragraph(text, h3_style))
        elif kind == "li":
            story.append(Paragraph(text, list_style))
        elif kind == "blockquote":
            story.append(Paragraph(text, blockquote_style))
        elif kind == "pre":
            story.append(Paragraph(text, pre_style))
        elif kind == "p":
            story.append(Paragraph(text, normal_style))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            _escape_reportlab("Generated by Neutrino AI Development Advisor"),
            meta_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()


class ReportGenerator:
    """Generates PDF reports from analysis results."""

    def __init__(self) -> None:
        pass

    async def generate_technical_report(
        self, analysis_id: str, data: dict[str, Any]
    ) -> bytes:
        """Generate technical analysis report PDF from stored data."""
        content = data.get("technical_summary") or "No technical summary available."
        return generate_pdf(
            report_type="technical",
            repo_url=data.get("repo_url", "Unknown"),
            content_markdown=content,
            model_used=data.get("model_used"),
        )

    async def generate_executive_report(
        self, analysis_id: str, data: dict[str, Any]
    ) -> bytes:
        """Generate executive summary report PDF from stored data."""
        content = data.get("executive_summary") or "No executive summary available."
        return generate_pdf(
            report_type="executive",
            repo_url=data.get("repo_url", "Unknown"),
            content_markdown=content,
            model_used=data.get("model_used"),
        )
