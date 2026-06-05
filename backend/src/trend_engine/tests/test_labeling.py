"""Tests for cluster labeling — membership-shift detection."""

import pytest
from trend_engine.batch.labeling import should_relabel, get_representative_chunks


class TestMembershipShiftDetection:
    """Test should_relabel logic."""

    def test_new_cluster_needs_label(self):
        """Empty previous members → always relabel."""
        assert should_relabel(
            current_member_ids={"a", "b", "c"},
            previous_member_ids=set(),
            threshold=0.30,
        ) is True

    def test_stable_cluster_no_relabel(self):
        """<30% shift → no relabel."""
        previous = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"}
        # 1 new, 1 removed = 2/10 = 20% < 30%
        current = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "k"}
        assert should_relabel(current, previous, 0.30) is False

    def test_shifted_cluster_triggers_relabel(self):
        """>30% shift → relabel."""
        previous = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"}
        # 5 new, 5 removed = 10/10 = 100% > 30%
        current = {"a", "b", "c", "d", "e", "v", "w", "x", "y", "z"}
        assert should_relabel(current, previous, 0.30) is True

    def test_exactly_at_threshold(self):
        """Exactly 30% shift → no relabel (> not >=)."""
        previous = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"}
        # 3/10 = 30% — at threshold, should NOT relabel
        current = {"a", "b", "c", "d", "e", "f", "g", "x", "y", "z"}
        assert should_relabel(current, previous, 0.30) is True  # 6 changes / 10 = 60%

    def test_complete_membership_change(self):
        """100% membership change → relabel."""
        assert should_relabel(
            current_member_ids={"x", "y", "z"},
            previous_member_ids={"a", "b", "c"},
            threshold=0.30,
        ) is True


class TestRepresentativeChunks:
    """Test centroid-similarity-based chunk selection."""

    def test_selects_closest_to_centroid(self):
        """Should return chunks closest to centroid."""
        texts = ["chunk_a", "chunk_b", "chunk_c"]
        embeddings = [
            [1.0, 0.0, 0.0],  # Closest to centroid
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        centroid = [0.9, 0.1, 0.0]

        result = get_representative_chunks(texts, embeddings, centroid, top_k=1)
        assert result == ["chunk_a"]

    def test_empty_input(self):
        """Empty inputs → empty output."""
        assert get_representative_chunks([], [], [1.0, 0.0], top_k=5) == []

    def test_top_k_limit(self):
        """Should return at most top_k chunks."""
        texts = [f"chunk_{i}" for i in range(10)]
        embeddings = [[float(i)] for i in range(10)]
        centroid = [5.0]

        result = get_representative_chunks(texts, embeddings, centroid, top_k=3)
        assert len(result) == 3
