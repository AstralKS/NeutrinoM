"""Cluster labeling — LLM-generated labels with membership-shift detection.

Labels are only regenerated when:
- Cluster has no existing label (newly formed)
- Membership has shifted more than 30% since last label assignment

Label contract: noun phrase under 10 words, no verbs, no marketing language.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import numpy as np

from trend_engine.config import TrendEngineSettings, get_settings
from trend_engine.db.client import get_http_client

logger = logging.getLogger(__name__)

_LABEL_PROMPT = """You are labeling a technical topic cluster. Below are the 5 most representative text chunks from this cluster.

{chunks}

Generate a concise label for this cluster:
- Must be a noun phrase
- Under 10 words
- No verbs
- No marketing language
- Describe the technical topic precisely

Return ONLY the label text, nothing else."""


async def generate_cluster_label(
    representative_chunks: list[str],
    settings: TrendEngineSettings | None = None,
) -> str | None:
    """Generate a label for a cluster using LLM.

    Args:
        representative_chunks: Top chunks by centroid similarity.

    Returns:
        Label string or None on failure.
    """
    cfg = settings or get_settings()

    if not representative_chunks:
        return None

    chunk_text = "\n\n---\n\n".join(
        f"Chunk {i+1}:\n{c[:800]}"
        for i, c in enumerate(representative_chunks[:cfg.label_top_k_chunks])
    )

    prompt = _LABEL_PROMPT.format(chunks=chunk_text)

    try:
        client = get_http_client()
        resp = await client.post(
            f"{cfg.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 50,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        label = data["choices"][0]["message"]["content"].strip().strip('"\'')

        # Validate: under 10 words
        if len(label.split()) > 10:
            label = " ".join(label.split()[:10])

        return label

    except Exception as exc:
        logger.error(f"Label generation failed: {exc}")
        return None


def should_relabel(
    current_member_ids: set[str],
    previous_member_ids: set[str],
    threshold: float | None = None,
) -> bool:
    """Detect if membership has shifted enough to warrant re-labeling.

    Args:
        current_member_ids: Set of chunk IDs in current cluster.
        previous_member_ids: Set of chunk IDs from previous run.
        threshold: Shift fraction threshold (default from config).

    Returns:
        True if membership shift exceeds threshold.
    """
    if threshold is None:
        threshold = get_settings().membership_shift_threshold

    if not previous_member_ids:
        return True  # New cluster, needs label

    new_members = current_member_ids - previous_member_ids
    removed_members = previous_member_ids - current_member_ids
    shift = (len(new_members) + len(removed_members)) / len(previous_member_ids)

    return shift > threshold


def get_representative_chunks(
    chunk_texts: list[str],
    chunk_embeddings: list[list[float]],
    centroid: list[float],
    top_k: int = 5,
) -> list[str]:
    """Select the top-k chunks by cosine similarity to the centroid.

    Args:
        chunk_texts: All chunk texts in the cluster.
        chunk_embeddings: Corresponding embeddings.
        centroid: Cluster centroid vector.

    Returns:
        Top-k chunk texts sorted by similarity to centroid.
    """
    if not chunk_texts or not chunk_embeddings:
        return []

    centroid_arr = np.array(centroid, dtype=np.float32)
    similarities = []

    for emb in chunk_embeddings:
        emb_arr = np.array(emb, dtype=np.float32)
        # Cosine similarity
        dot = np.dot(centroid_arr, emb_arr)
        norm_c = np.linalg.norm(centroid_arr)
        norm_e = np.linalg.norm(emb_arr)
        if norm_c > 0 and norm_e > 0:
            sim = dot / (norm_c * norm_e)
        else:
            sim = 0.0
        similarities.append(float(sim))

    # Get top-k indices
    indexed = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, _ in indexed[:top_k]]

    return [chunk_texts[i] for i in top_indices]
