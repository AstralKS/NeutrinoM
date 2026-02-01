"""Architecture pattern analysis.

Identifies architectural patterns from code structure and organization.
"""

from typing import Any

from advisor.database.models import ArchitecturePattern

# Common directory patterns indicating architecture
ARCHITECTURE_INDICATORS = {
    "clean_architecture": {
        "patterns": ["domain", "usecases", "entities", "infrastructure", "adapters"],
        "name": "Clean Architecture",
        "description": "Separation of concerns with domain-centric design",
    },
    "mvc": {
        "patterns": ["models", "views", "controllers"],
        "name": "MVC (Model-View-Controller)",
        "description": "Classic separation of data, presentation, and logic",
    },
    "mvvm": {
        "patterns": ["models", "views", "viewmodels"],
        "name": "MVVM (Model-View-ViewModel)",
        "description": "UI pattern with data binding",
    },
    "microservices": {
        "patterns": ["services/", "api-gateway", "shared/"],
        "name": "Microservices",
        "description": "Distributed services architecture",
    },
    "modular": {
        "patterns": ["modules/", "packages/", "libs/"],
        "name": "Modular Monolith",
        "description": "Single deployable with modular boundaries",
    },
    "layered": {
        "patterns": ["presentation", "business", "data", "persistence"],
        "name": "Layered Architecture",
        "description": "Horizontal layers of responsibility",
    },
    "event_driven": {
        "patterns": ["events/", "handlers/", "subscribers/", "publishers/"],
        "name": "Event-Driven",
        "description": "Communication via events and messages",
    },
    "serverless": {
        "patterns": ["functions/", "lambda/", "serverless.yml"],
        "name": "Serverless",
        "description": "Function-as-a-Service deployment",
    },
    "nextjs_app": {
        "patterns": ["app/", "pages/", "components/", "lib/"],
        "name": "Next.js App Structure",
        "description": "Next.js App Router pattern",
    },
    "fastapi_standard": {
        "patterns": ["routers/", "schemas/", "crud/", "core/"],
        "name": "FastAPI Standard",
        "description": "FastAPI recommended project structure",
    },
}


class ArchitectureAnalyzer:
    """Analyzes repository structure for architectural patterns."""

    def analyze(
        self,
        file_tree: list[dict[str, Any]],
        file_contents: dict[str, str],
    ) -> list[ArchitecturePattern]:
        """Analyze architecture patterns from repository structure.

        Args:
            file_tree: List of files in repository.
            file_contents: Map of file path to content.

        Returns:
            List of detected architecture patterns with confidence.
        """
        patterns = []

        # Get all directory names
        directories = self._extract_directories(file_tree)
        all_paths = " ".join([item["path"].lower() for item in file_tree])

        for arch_info in ARCHITECTURE_INDICATORS.values():
            evidence = []
            matches = 0

            for pattern in arch_info["patterns"]:
                if pattern.endswith("/"):
                    # Check for directory
                    if pattern.rstrip("/") in directories:
                        evidence.append(f"Found '{pattern}' directory")
                        matches += 1
                else:
                    # Check in paths
                    if pattern.lower() in all_paths:
                        evidence.append(f"Found '{pattern}' in structure")
                        matches += 1

            if matches > 0:
                confidence = min(matches / len(arch_info["patterns"]), 1.0)
                if confidence >= 0.3:  # Minimum threshold
                    patterns.append(
                        ArchitecturePattern(
                            pattern_name=arch_info["name"],
                            confidence=round(confidence, 2),
                            evidence=evidence,
                            description=arch_info["description"],
                        )
                    )

        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        # If no patterns detected, infer from structure
        if not patterns:
            patterns.append(
                ArchitecturePattern(
                    pattern_name="Simple/Flat Structure",
                    confidence=0.5,
                    evidence=["No recognizable architectural patterns"],
                    description="Minimal or flat project structure",
                )
            )

        return patterns[:5]  # Top 5 patterns

    def _extract_directories(self, file_tree: list[dict[str, Any]]) -> set[str]:
        """Extract unique directory names from file tree."""
        directories = set()
        for item in file_tree:
            parts = item["path"].split("/")
            # Add each directory level
            for part in parts[:-1]:
                directories.add(part.lower())
        return directories
