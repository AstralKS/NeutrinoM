"""HTML parser — extract body content and metadata from fetched pages."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any

logger = logging.getLogger(__name__)

# Tags whose content is navigation / boilerplate — strip entirely
_STRIP_TAGS = {
    "nav", "footer", "header", "aside", "script", "style",
    "noscript", "iframe", "svg", "form",
}

# Tags that mark structural content blocks
_BLOCK_TAGS = {"p", "div", "section", "article", "main", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}


class _ContentExtractor(HTMLParser):
    """Extract visible body text, skipping nav/footer/boilerplate."""

    def __init__(self) -> None:
        super().__init__()
        self._result: list[str] = []
        self._skip_depth = 0
        self._in_body = False
        self._title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "body":
            self._in_body = True
        if tag == "title":
            self._in_title = True
        if tag in _STRIP_TAGS:
            self._skip_depth += 1
        # Check for code blocks that are purely syntax
        if tag == "pre":
            attr_dict = dict(attrs)
            classes = attr_dict.get("class", "")
            if "highlight" in classes or "code" in classes:
                self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in _STRIP_TAGS or tag == "pre":
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag in _BLOCK_TAGS and self._result:
            self._result.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title += data.strip()
        if self._in_body and self._skip_depth == 0:
            text = data.strip()
            if text:
                self._result.append(text)

    def get_text(self) -> str:
        return " ".join(self._result)

    def get_title(self) -> str:
        return self._title.strip()


def parse_html(html: str) -> dict[str, str]:
    """Parse HTML and extract clean body text + title.

    Returns:
        {"title": str, "clean_text": str, "raw_text": str}
    """
    extractor = _ContentExtractor()
    try:
        extractor.feed(html)
    except Exception as exc:
        logger.warning(f"HTML parse error: {exc}")

    raw_text = html
    clean_text = _normalize_whitespace(extractor.get_text())
    title = extractor.get_title() or "Untitled"

    return {
        "title": title,
        "clean_text": clean_text,
        "raw_text": raw_text,
    }


def compute_content_hash(clean_text: str) -> str:
    """SHA256 of clean_text — the deduplication key."""
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


def extract_published_date(html: str) -> datetime | None:
    """Try to extract publication date from meta tags or common patterns."""
    # Try meta tags
    patterns = [
        r'<meta\s+(?:property|name)="(?:article:published_time|datePublished|date|DC\.date)"\s+content="([^"]+)"',
        r'<time[^>]+datetime="([^"]+)"',
    ]
    for pat in patterns:
        match = re.search(pat, html, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                # Handle various ISO formats
                date_str = date_str.replace("Z", "+00:00")
                return datetime.fromisoformat(date_str)
            except (ValueError, IndexError):
                continue
    return None


def _normalize_whitespace(text: str) -> str:
    """Collapse whitespace runs to single spaces, strip edges."""
    return re.sub(r"\s+", " ", text).strip()
