"""Text chunker — sentence-aware splitting into 300–800 token segments.

Each chunk is semantically self-contained:
- No mid-sentence splits
- No mid-paragraph splits when avoidable
- Chunk size bounded by config-specified token range
"""

from __future__ import annotations

import re

from trend_engine.config import get_settings


def _approx_token_count(text: str) -> int:
    """Fast approximate token count (words * 1.3 ≈ tokens for English)."""
    return int(len(text.split()) * 1.3)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex heuristics."""
    # Split on sentence-ending punctuation followed by whitespace
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]


def chunk_text(text: str) -> list[str]:
    """Split text into chunks of 300–800 tokens.

    Strategy:
    1. Split into paragraphs
    2. Accumulate paragraphs into chunks
    3. If a paragraph alone exceeds max, split into sentences
    4. If a sentence alone exceeds max, split at word boundary (last resort)

    Returns:
        List of text chunks, each 300–800 tokens.
    """
    settings = get_settings()
    min_tokens = settings.chunk_min_tokens
    max_tokens = settings.chunk_max_tokens

    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    def _flush() -> None:
        nonlocal current_parts, current_tokens
        if current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts = []
            current_tokens = 0

    for para in paragraphs:
        para_tokens = _approx_token_count(para)

        # If paragraph itself exceeds max, split into sentences
        if para_tokens > max_tokens:
            _flush()
            sentences = _split_sentences(para)
            sent_parts: list[str] = []
            sent_tokens = 0

            for sent in sentences:
                s_tokens = _approx_token_count(sent)

                # If single sentence exceeds max — hard split at word boundary
                if s_tokens > max_tokens:
                    if sent_parts:
                        chunks.append(" ".join(sent_parts))
                        sent_parts = []
                        sent_tokens = 0
                    words = sent.split()
                    word_buf: list[str] = []
                    word_tok = 0
                    for word in words:
                        wt = _approx_token_count(word)
                        if word_tok + wt > max_tokens and word_buf:
                            chunks.append(" ".join(word_buf))
                            word_buf = []
                            word_tok = 0
                        word_buf.append(word)
                        word_tok += wt
                    if word_buf:
                        sent_parts.extend(word_buf)
                        sent_tokens += word_tok
                    continue

                if sent_tokens + s_tokens > max_tokens and sent_parts:
                    chunks.append(" ".join(sent_parts))
                    sent_parts = []
                    sent_tokens = 0

                sent_parts.append(sent)
                sent_tokens += s_tokens

            if sent_parts:
                # Add remaining sentences to current chunk or start new one
                remaining = " ".join(sent_parts)
                remaining_tokens = _approx_token_count(remaining)
                if current_tokens + remaining_tokens <= max_tokens:
                    current_parts.append(remaining)
                    current_tokens += remaining_tokens
                else:
                    _flush()
                    current_parts.append(remaining)
                    current_tokens = remaining_tokens
            continue

        # Normal accumulation
        if current_tokens + para_tokens > max_tokens:
            _flush()

        current_parts.append(para)
        current_tokens += para_tokens

    _flush()

    # Merge undersized trailing chunk with previous if possible
    if len(chunks) >= 2:
        last = chunks[-1]
        if _approx_token_count(last) < min_tokens:
            prev = chunks[-2]
            merged = prev + "\n\n" + last
            if _approx_token_count(merged) <= max_tokens:
                chunks[-2] = merged
                chunks.pop()

    return chunks
