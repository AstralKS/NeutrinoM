"""Architecture snapshot generation — structured JSON per cluster.

Infers architectural patterns from member document content.
Uses LLM to analyze representative chunks and produce structured output.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from trend_engine.config import TrendEngineSettings, get_settings
from trend_engine.db.client import get_http_client

logger = logging.getLogger(__name__)

_ARCHITECTURE_PROMPT = """Analyze the following technical content snippets (all from the same topic cluster) and generate a structured architecture snapshot.

Content snippets:
{snippets}

Return ONLY a valid JSON object with this exact structure:
{{
  "detected_layers": ["list of architectural layers like Frontend, Backend, Database, Infra, ML Pipeline, etc."],
  "primary_patterns": ["list of architectural patterns like REST API, Event-driven, microservices, etc."],
  "dependency_graph": {{
    "ComponentA": ["ComponentB", "ComponentC"],
    "ComponentB": []
  }},
  "risk_zones": ["list of identified architectural risks"],
  "confidence": 0.0
}}

Set confidence between 0.0 and 1.0 based on how much evidence supports the analysis.
If the content is insufficient, return minimal data with low confidence.
Return ONLY the JSON, no markdown, no explanation."""


async def generate_architecture_snapshot(
    representative_chunks: list[str],
    settings: TrendEngineSettings | None = None,
) -> dict[str, Any]:
    """Generate architecture snapshot from cluster's representative chunks.

    Args:
        representative_chunks: Top chunks (by centroid similarity) from the cluster.
        settings: Engine settings.

    Returns:
        Structured architecture snapshot dict.
    """
    cfg = settings or get_settings()

    if not representative_chunks:
        return _empty_snapshot()

    snippets = "\n\n---\n\n".join(
        f"Snippet {i+1}:\n{chunk[:1500]}"
        for i, chunk in enumerate(representative_chunks[:5])
    )

    prompt = _ARCHITECTURE_PROMPT.format(snippets=snippets)

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
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Parse JSON from response (strip markdown fences if present)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        snapshot = json.loads(content)
        # Validate required keys
        for key in ["detected_layers", "primary_patterns", "dependency_graph", "risk_zones", "confidence"]:
            if key not in snapshot:
                snapshot[key] = _empty_snapshot()[key]

        return snapshot

    except Exception as exc:
        logger.error(f"Architecture snapshot generation failed: {exc}")
        return _empty_snapshot()


def _empty_snapshot() -> dict[str, Any]:
    return {
        "detected_layers": [],
        "primary_patterns": [],
        "dependency_graph": {},
        "risk_zones": [],
        "confidence": 0.0,
    }
