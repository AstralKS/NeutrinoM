"""Source configuration — deploy-time source list.

Sources are loaded from a JSON config file. No dynamic addition at runtime.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from trend_engine.models import SourceConfig

logger = logging.getLogger(__name__)

_DEFAULT_SOURCES_PATH = Path(__file__).parent.parent / "sources.json"


def load_sources(path: Path | None = None) -> list[SourceConfig]:
    """Load source configurations from a JSON file.

    Args:
        path: Path to sources.json. Defaults to trend_engine/sources.json.

    Returns:
        List of validated SourceConfig objects.
    """
    config_path = path or _DEFAULT_SOURCES_PATH
    if not config_path.exists():
        logger.warning(f"Sources config not found: {config_path}")
        return []

    with open(config_path, encoding="utf-8") as f:
        raw = json.load(f)

    sources = [SourceConfig.model_validate(s) for s in raw]
    enabled = [s for s in sources if s.enabled]
    logger.info(f"Loaded {len(enabled)}/{len(sources)} enabled sources")
    return enabled
