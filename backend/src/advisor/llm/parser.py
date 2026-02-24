import json
import re
from typing import Any

def parse_llm_json(content: str) -> dict[str, Any] | list[Any]:
    """Parse JSON from LLM output, handling markdown code blocks."""
    # Strip markdown code blocks if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if match:
        content = match.group(1)
    
    return json.loads(content)
