"""Technology upgrade prioritizer for dependency and version analysis.

Identifies outdated dependencies and prioritizes upgrades based on:
- Impact: New features enabled, security fixes, performance gains
- Effort: Breaking changes, migration complexity
- Risk: Stability, compatibility concerns
- Urgency: EOL dates, security vulnerabilities
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from advisor.database.models import TechStackInfo


class UpgradeRecommendation(BaseModel):
    """Recommendation for a technology upgrade."""

    package: str
    current_version: str = ""
    recommended_version: str = ""
    category: str = ""  # framework, tool, runtime, database
    priority: str = ""  # low, medium, high, critical
    impact_score: int = Field(default=0, ge=0, le=100)
    effort_score: int = Field(default=0, ge=0, le=100)
    reason: str = ""
    breaking_changes: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    migration_steps: list[str] = Field(default_factory=list)


# Known version recommendations and EOL dates
VERSION_RECOMMENDATIONS = {
    # Node.js
    "node": {
        "eol_versions": ["12", "14", "16"],
        "recommended": "20",
        "lts_versions": ["18", "20", "22"],
    },
    # Python
    "python": {
        "eol_versions": ["2.7", "3.6", "3.7", "3.8"],
        "recommended": "3.12",
        "benefits": ["Performance improvements", "New syntax features"],
    },
    # React
    "react": {
        "major_versions": {"16": "18", "17": "18"},
        "recommended": "18",
        "benefits": ["Concurrent rendering", "Server Components", "Automatic batching"],
    },
    # Next.js
    "next": {
        "major_versions": {"12": "14", "13": "14"},
        "recommended": "14",
        "benefits": ["App Router", "Server Actions", "Turbopack"],
    },
    # TypeScript
    "typescript": {
        "major_versions": {"4": "5"},
        "recommended": "5",
        "benefits": ["Decorators", "const type parameters", "Better inference"],
    },
}

# Security-related packages that should always be updated
SECURITY_CRITICAL = [
    "express", "fastapi", "django", "flask",
    "jsonwebtoken", "bcrypt", "passport",
    "axios", "requests", "httpx",
]


class UpgradePrioritizer:
    """Prioritizes technology upgrades for the codebase."""

    def prioritize(
        self,
        tech_stack: TechStackInfo,
        file_contents: dict[str, str],
    ) -> list[UpgradeRecommendation]:
        """Analyze and prioritize upgrade recommendations.

        Args:
            tech_stack: Detected technology stack.
            file_contents: Map of file paths to content.

        Returns:
            List of prioritized upgrade recommendations.
        """
        recommendations: list[UpgradeRecommendation] = []

        # Check version info from tech stack
        for package, version in tech_stack.versions.items():
            rec = self._analyze_package(package, version)
            if rec:
                recommendations.append(rec)

        # Parse package files for more details
        package_versions = self._parse_package_files(file_contents)
        for package, version in package_versions.items():
            if not any(r.package == package for r in recommendations):
                rec = self._analyze_package(package, version)
                if rec:
                    recommendations.append(rec)

        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 4))

        return recommendations

    def _analyze_package(
        self,
        package: str,
        version: str,
    ) -> UpgradeRecommendation | None:
        """Analyze a single package for upgrade needs."""
        package_lower = package.lower()
        version_clean = self._clean_version(version)

        # Check if package has known recommendations
        for key, info in VERSION_RECOMMENDATIONS.items():
            if key in package_lower:
                return self._create_recommendation(
                    package, version_clean, info, key
                )

        # Check security-critical packages
        if package_lower in SECURITY_CRITICAL:
            return UpgradeRecommendation(
                package=package,
                current_version=version_clean,
                category="security",
                priority="medium",
                impact_score=70,
                effort_score=30,
                reason="Security-critical package should be kept up to date",
                benefits=["Security patches", "Bug fixes"],
            )

        return None

    def _create_recommendation(
        self,
        package: str,
        current: str,
        info: dict[str, Any],
        key: str,
    ) -> UpgradeRecommendation | None:
        """Create recommendation based on known version info."""
        major = self._get_major_version(current)
        recommended = info.get("recommended", "")
        eol = info.get("eol_versions", [])
        benefits = info.get("benefits", [])

        # Check if EOL
        if major in eol:
            return UpgradeRecommendation(
                package=package,
                current_version=current,
                recommended_version=recommended,
                category="runtime",
                priority="critical",
                impact_score=90,
                effort_score=60,
                reason=f"Version {major} is End-of-Life",
                benefits=["Security updates", "Continued support"] + benefits,
                breaking_changes=["Review changelog for breaking changes"],
            )

        # Check if major upgrade available
        major_versions = info.get("major_versions", {})
        if major in major_versions:
            target = major_versions[major]
            return UpgradeRecommendation(
                package=package,
                current_version=current,
                recommended_version=target,
                category="framework",
                priority="high",
                impact_score=75,
                effort_score=50,
                reason=f"Major version {target} available with significant improvements",
                benefits=benefits,
            )

        return None

    def _parse_package_files(
        self,
        file_contents: dict[str, str],
    ) -> dict[str, str]:
        """Extract package versions from manifest files."""
        versions: dict[str, str] = {}

        for path, content in file_contents.items():
            if "package.json" in path:
                versions.update(self._parse_package_json(content))
            elif "pyproject.toml" in path or "requirements.txt" in path:
                versions.update(self._parse_python_deps(content))

        return versions

    def _parse_package_json(self, content: str) -> dict[str, str]:
        """Parse package.json for versions."""
        import json
        try:
            data = json.loads(content)
            versions = {}
            for key in ["dependencies", "devDependencies"]:
                deps = data.get(key, {})
                for pkg, ver in deps.items():
                    versions[pkg] = self._clean_version(ver)
            return versions
        except json.JSONDecodeError:
            return {}

    def _parse_python_deps(self, content: str) -> dict[str, str]:
        """Parse Python dependency files for versions."""
        versions = {}
        # Match patterns like: package==1.2.3 or package>=1.2.3
        pattern = r'([a-zA-Z\-_]+)\s*[=<>!~]+\s*([\d.]+)'
        for match in re.finditer(pattern, content):
            versions[match.group(1)] = match.group(2)
        return versions

    def _clean_version(self, version: str) -> str:
        """Clean version string."""
        return version.lstrip("^~>=<!")

    def _get_major_version(self, version: str) -> str:
        """Extract major version number."""
        parts = version.split(".")
        return parts[0] if parts else version
