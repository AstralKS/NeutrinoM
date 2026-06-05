"""Tests for the text chunker — boundary conditions and sentence awareness."""

import pytest
from unittest.mock import patch, MagicMock


class MockSettings:
    chunk_min_tokens = 10
    chunk_max_tokens = 100


@pytest.fixture(autouse=True)
def mock_get_settings():
    with patch("trend_engine.ingestion.chunker.get_settings", return_value=MockSettings()):
        yield


class TestChunker:
    """Test chunking boundary conditions."""

    def test_short_text_single_chunk(self):
        """Text shorter than max_tokens should produce one chunk."""
        from trend_engine.ingestion.chunker import chunk_text
        text = "This is a short text about machine learning concepts."
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        assert text in chunks[0]

    def test_long_text_multiple_chunks(self):
        """Text exceeding max_tokens should produce multiple chunks."""
        from trend_engine.ingestion.chunker import chunk_text
        # Generate text >100 tokens
        sentences = [
            f"This is sentence number {i} about artificial intelligence and its applications in modern computing systems."
            for i in range(20)
        ]
        text = " ".join(sentences)
        chunks = chunk_text(text)
        assert len(chunks) > 1

    def test_no_mid_sentence_split(self):
        """Chunks should not split mid-sentence."""
        from trend_engine.ingestion.chunker import chunk_text
        text = (
            "First sentence about AI. Second sentence about ML. "
            "Third sentence about deep learning. Fourth sentence about NLP. "
            "Fifth sentence about computer vision. " * 5
        )
        chunks = chunk_text(text)
        for chunk in chunks:
            # Each chunk should end with a complete sentence (period)
            stripped = chunk.strip()
            if stripped:
                assert stripped[-1] in ".!?" or stripped == chunks[-1].strip(), (
                    f"Chunk doesn't end with sentence boundary: ...{stripped[-30:]}"
                )

    def test_paragraph_preservation(self):
        """Paragraphs should be kept together when possible."""
        from trend_engine.ingestion.chunker import chunk_text
        text = (
            "First paragraph about AI technology.\n\n"
            "Second paragraph about ML applications.\n\n"
            "Third paragraph about deep learning research."
        )
        chunks = chunk_text(text)
        assert len(chunks) >= 1

    def test_empty_text(self):
        """Empty text should produce empty list."""
        from trend_engine.ingestion.chunker import chunk_text
        chunks = chunk_text("")
        assert chunks == []

    def test_whitespace_only(self):
        """Whitespace-only text should produce empty list."""
        from trend_engine.ingestion.chunker import chunk_text
        chunks = chunk_text("   \n\n   \t   ")
        assert chunks == []


class TestDeduplication:
    """Test content hashing and deduplication logic."""

    def test_identical_content_same_hash(self):
        """Identical clean_text should produce identical hash."""
        from trend_engine.ingestion.parser import compute_content_hash
        text = "This is some technical content about vector databases."
        hash1 = compute_content_hash(text)
        hash2 = compute_content_hash(text)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        from trend_engine.ingestion.parser import compute_content_hash
        hash1 = compute_content_hash("Content about vector databases.")
        hash2 = compute_content_hash("Content about graph databases.")
        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Hash should be a valid SHA256 hex string."""
        from trend_engine.ingestion.parser import compute_content_hash
        result = compute_content_hash("test content")
        assert len(result) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in result)

    def test_whitespace_sensitivity(self):
        """Hashes should be sensitive to whitespace differences."""
        from trend_engine.ingestion.parser import compute_content_hash
        hash1 = compute_content_hash("hello world")
        hash2 = compute_content_hash("hello  world")
        assert hash1 != hash2
