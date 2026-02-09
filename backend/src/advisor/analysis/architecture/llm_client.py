"""LLM client for architecture analysis - API batching and response parsing."""

import json
import logging
import os
from typing import Any

from .models import (
    AnalysisBatch,
    ArchitecturalViolation,
    CachePattern,
    DataFlowPattern,
    DependencyNode,
    DesignPattern,
    StatePattern,
)

logger = logging.getLogger(__name__)


class LLMArchitectureClient:
    """Handles LLM API calls for architecture analysis."""

    def __init__(self, api_key: str | None = None, model_name: str = "gpt-4o"):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model_name = model_name
        self._client = None

        if self._api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def analyze_batches(
        self, batches: list[AnalysisBatch], graph: dict[str, DependencyNode],
        file_contents: dict[str, str],
    ) -> dict[str, Any]:
        """Analyze all batches and merge results."""
        results = [self._analyze_batch(b, graph, file_contents) for b in batches]
        return self._merge_results(results)

    def _analyze_batch(
        self, batch: AnalysisBatch, graph: dict[str, DependencyNode],
        file_contents: dict[str, str],
    ) -> dict[str, Any]:
        """Analyze a single batch with LLM."""
        if not self._client:
            return self._fallback_analysis(graph, file_contents)

        schema = '{"architecture_type":"str","design_patterns":[{"name":"str","description":"str","files":["str"],"confidence":0.0}],"data_flow_patterns":[{"name":"str","description":"str","files_involved":["str"],"confidence":0.0}],"state_patterns":[{"pattern":"str","files":["str"],"complexity":"str"}],"cache_patterns":[{"type":"str","location":"str","files":["str"]}],"architectural_violations":[{"rule":"str","description":"str","files_involved":["str"],"severity":"str"}]}'

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": f"Analyze {batch.category}. Return JSON: {schema}"},
                    {"role": "user", "content": f"Analyze:\n{batch.extracted_context}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000,
            )
            if content := response.choices[0].message.content:
                return self._parse_response(json.loads(content))
        except Exception as e:
            logger.warning(f"LLM failed for {batch.category}: {e}")
        return self._fallback_analysis(graph, file_contents)

    def _parse_response(self, data: dict) -> dict[str, Any]:
        """Parse and validate LLM response."""
        result: dict[str, Any] = {
            "architecture_type": data.get("architecture_type", "Unknown"),
            "design_patterns": [],
            "data_flow_patterns": [],
            "state_patterns": [],
            "cache_patterns": [],
            "architectural_violations": [],
        }

        for dp in data.get("design_patterns", []):
            result["design_patterns"].append(DesignPattern(
                name=dp.get("name", ""), description=dp.get("description", ""),
                files=dp.get("files", []), confidence=dp.get("confidence", 0.5)))

        for dfp in data.get("data_flow_patterns", []):
            result["data_flow_patterns"].append(DataFlowPattern(
                name=dfp.get("name", ""), description=dfp.get("description", ""),
                files_involved=dfp.get("files_involved", []), confidence=dfp.get("confidence", 0.5)))

        for sp in data.get("state_patterns", []):
            result["state_patterns"].append(StatePattern(
                pattern=sp.get("pattern", ""), files=sp.get("files", []),
                complexity=sp.get("complexity", "simple")))

        for cp in data.get("cache_patterns", []):
            result["cache_patterns"].append(CachePattern(
                type=cp.get("type", ""), location=cp.get("location", "server"),
                files=cp.get("files", [])))

        for v in data.get("architectural_violations", []):
            result["architectural_violations"].append(ArchitecturalViolation(
                rule=v.get("rule", ""), description=v.get("description", ""),
                files_involved=v.get("files_involved", []), severity=v.get("severity", "medium")))

        return result

    def _merge_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple batch results into one."""
        if not results:
            return {"architecture_type": "Unknown", "design_patterns": [], "data_flow_patterns": [],
                    "state_patterns": [], "cache_patterns": [], "architectural_violations": []}
        if len(results) == 1:
            return results[0]

        merged = {"architecture_type": "", "design_patterns": [], "data_flow_patterns": [],
                  "state_patterns": [], "cache_patterns": [], "architectural_violations": []}
        seen = {k: set() for k in merged if k != "architecture_type"}
        key_map = {"design_patterns": "name", "data_flow_patterns": "name", "state_patterns": "pattern",
                   "cache_patterns": "type", "architectural_violations": "rule"}

        for result in results:
            if not merged["architecture_type"] and result.get("architecture_type"):
                merged["architecture_type"] = result["architecture_type"]
            for field, attr in key_map.items():
                for item in result.get(field, []):
                    key = getattr(item, attr, None) or item.get(attr, "")
                    if key and key not in seen[field]:
                        seen[field].add(key)
                        merged[field].append(item)

        merged["architecture_type"] = merged["architecture_type"] or "Unknown"
        return merged

    def _fallback_analysis(
        self, graph: dict[str, DependencyNode], file_contents: dict[str, str],
    ) -> dict[str, Any]:
        """Fallback analysis when LLM is unavailable."""
        all_content = " ".join(file_contents.values()).lower()
        all_paths = " ".join(file_contents.keys()).lower()

        arch_type = "Monolith"
        if "controller" in all_paths and "service" in all_paths and "repository" in all_paths:
            arch_type = "Layered"
        elif "domain" in all_paths and "infrastructure" in all_paths:
            arch_type = "Hexagonal/Clean"

        state_patterns = []
        for pattern, kws in {"redux": ["redux", "createstore"], "zustand": ["zustand"], "context": ["createcontext"]}.items():
            if any(k in all_content for k in kws):
                state_patterns.append(StatePattern(pattern=pattern, files=[], complexity="simple"))

        cache_patterns = []
        if "redis" in all_content:
            cache_patterns.append(CachePattern(type="redis", location="server", files=[]))

        return {
            "architecture_type": arch_type, "design_patterns": [], "data_flow_patterns": [],
            "state_patterns": state_patterns, "cache_patterns": cache_patterns, "architectural_violations": [],
        }
