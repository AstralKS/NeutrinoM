"""Version Checker - Fetches latest versions from package registries.

Checks npm, PyPI, and GitHub releases for the latest stable versions
of detected packages and compares them against the user's current versions.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Cache duration for version lookups
CACHE_TTL_HOURS = 24


@dataclass
class VersionInfo:
    """Version information for a package."""

    package: str
    registry: str  # npm, pypi, github
    current_version: str | None = None
    latest_stable: str | None = None
    latest_release_date: datetime | None = None
    breaking_changes: bool = False
    major_versions_behind: int = 0
    changelog_url: str | None = None
    deprecation_warning: str | None = None
    error: str | None = None


@dataclass
class PackageInfo:
    """Input package information."""

    name: str
    current_version: str | None = None
    registry: str = "auto"  # auto, npm, pypi, github


@dataclass
class VersionCache:
    """Cached version data."""

    data: dict[str, VersionInfo] = field(default_factory=dict)
    timestamps: dict[str, datetime] = field(default_factory=dict)

    def get(self, key: str) -> VersionInfo | None:
        """Get cached entry if not expired."""
        if key not in self.data:
            return None
        
        timestamp = self.timestamps.get(key)
        if timestamp and datetime.now(UTC) - timestamp > timedelta(hours=CACHE_TTL_HOURS):
            del self.data[key]
            del self.timestamps[key]
            return None
        
        return self.data[key]

    def set(self, key: str, value: VersionInfo) -> None:
        """Set cache entry."""
        self.data[key] = value
        self.timestamps[key] = datetime.now(UTC)


class VersionChecker:
    """Checks package registries for latest versions."""

    def __init__(self) -> None:
        """Initialize version checker with cache."""
        self._cache = VersionCache()
        self._timeout = 10.0

    async def get_latest_version(
        self,
        package: str,
        registry: str = "auto",
        current_version: str | None = None,
    ) -> VersionInfo:
        """Get latest version for a single package.

        Args:
            package: Package name.
            registry: Registry to check (npm, pypi, github, auto).
            current_version: Current version for comparison.

        Returns:
            VersionInfo with latest version data.
        """
        cache_key = f"{registry}:{package}"
        cached = self._cache.get(cache_key)
        if cached:
            # Update current version comparison if provided
            if current_version:
                cached.current_version = current_version
                cached.breaking_changes = self._is_major_upgrade(
                    current_version, cached.latest_stable
                )
                cached.major_versions_behind = self._get_major_diff(
                    current_version, cached.latest_stable
                )
            return cached

        # Auto-detect registry
        if registry == "auto":
            registry = self._detect_registry(package)

        # Fetch from appropriate registry
        if registry == "npm":
            result = await self._check_npm(package, current_version)
        elif registry == "pypi":
            result = await self._check_pypi(package, current_version)
        elif registry == "github":
            result = await self._check_github(package, current_version)
        else:
            result = VersionInfo(
                package=package,
                registry=registry,
                error=f"Unknown registry: {registry}",
            )

        self._cache.set(cache_key, result)
        return result

    async def get_batch_versions(
        self,
        packages: list[PackageInfo],
    ) -> dict[str, VersionInfo]:
        """Get latest versions for multiple packages.

        Args:
            packages: List of PackageInfo objects.

        Returns:
            Dict mapping package names to VersionInfo.
        """
        tasks = [
            self.get_latest_version(
                package=p.name,
                registry=p.registry,
                current_version=p.current_version,
            )
            for p in packages
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, VersionInfo] = {}
        for pkg, result in zip(packages, results):
            if isinstance(result, Exception):
                output[pkg.name] = VersionInfo(
                    package=pkg.name,
                    registry=pkg.registry,
                    error=str(result),
                )
            else:
                output[pkg.name] = result

        return output

    def format_for_analysis(
        self,
        versions: dict[str, VersionInfo],
    ) -> str:
        """Format version info for inclusion in analysis prompts.

        Args:
            versions: Dict of package names to VersionInfo.

        Returns:
            Formatted markdown string for prompt injection.
        """
        if not versions:
            return "No package version information available."

        lines = ["| Package | Current | Latest | Status | Action |",
                 "|---------|---------|--------|--------|--------|"]

        # Sort by priority: breaking changes first, then by major versions behind
        sorted_versions = sorted(
            versions.values(),
            key=lambda v: (not v.breaking_changes, -v.major_versions_behind),
        )

        outdated_count = 0
        for v in sorted_versions:
            if v.error:
                continue

            current = v.current_version or "unknown"
            latest = v.latest_stable or "unknown"

            if v.breaking_changes:
                status = f"⚠️ {v.major_versions_behind} major behind"
                action = "Major upgrade needed"
                outdated_count += 1
            elif v.major_versions_behind > 0:
                status = f"📦 {v.major_versions_behind} version(s) behind"
                action = "Update recommended"
                outdated_count += 1
            elif current != latest and current != "unknown":
                status = "🔄 Minor update"
                action = "Optional update"
            else:
                status = "✅ Up to date"
                action = "None"

            lines.append(f"| {v.package} | {current} | {latest} | {status} | {action} |")

        summary = f"\n**Summary:** {outdated_count}/{len(sorted_versions)} packages need updates."
        
        if outdated_count > 0:
            critical = [v for v in sorted_versions if v.breaking_changes]
            if critical:
                summary += f"\n**Critical:** {len(critical)} packages have breaking changes available."

        return "\n".join(lines) + summary

    async def _check_npm(
        self,
        package: str,
        current_version: str | None,
    ) -> VersionInfo:
        """Check npm registry for latest version."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"https://registry.npmjs.org/{package}/latest",
                    headers={"Accept": "application/json"},
                )

                if response.status_code == 404:
                    return VersionInfo(
                        package=package,
                        registry="npm",
                        error="Package not found on npm",
                    )

                if response.status_code != 200:
                    return VersionInfo(
                        package=package,
                        registry="npm",
                        error=f"npm API error: {response.status_code}",
                    )

                data = response.json()
                latest = data.get("version", "")

                # Get release date from dist-tags
                release_date = None
                time_data = data.get("time", {})
                if latest in time_data:
                    try:
                        release_date = datetime.fromisoformat(
                            time_data[latest].replace("Z", "+00:00")
                        )
                    except (ValueError, KeyError):
                        pass

                return VersionInfo(
                    package=package,
                    registry="npm",
                    current_version=current_version,
                    latest_stable=latest,
                    latest_release_date=release_date,
                    breaking_changes=self._is_major_upgrade(current_version, latest),
                    major_versions_behind=self._get_major_diff(current_version, latest),
                    changelog_url=f"https://www.npmjs.com/package/{package}?activeTab=versions",
                )

        except Exception as e:
            logger.warning(f"Error checking npm for {package}: {e}")
            return VersionInfo(
                package=package,
                registry="npm",
                error=str(e),
            )

    async def _check_pypi(
        self,
        package: str,
        current_version: str | None,
    ) -> VersionInfo:
        """Check PyPI registry for latest version."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"https://pypi.org/pypi/{package}/json",
                    headers={"Accept": "application/json"},
                )

                if response.status_code == 404:
                    return VersionInfo(
                        package=package,
                        registry="pypi",
                        error="Package not found on PyPI",
                    )

                if response.status_code != 200:
                    return VersionInfo(
                        package=package,
                        registry="pypi",
                        error=f"PyPI API error: {response.status_code}",
                    )

                data = response.json()
                info = data.get("info", {})
                latest = info.get("version", "")

                # Get release date from releases
                release_date = None
                releases = data.get("releases", {})
                if latest in releases and releases[latest]:
                    try:
                        upload_time = releases[latest][0].get("upload_time_iso_8601")
                        if upload_time:
                            release_date = datetime.fromisoformat(
                                upload_time.replace("Z", "+00:00")
                            )
                    except (ValueError, IndexError, KeyError):
                        pass

                return VersionInfo(
                    package=package,
                    registry="pypi",
                    current_version=current_version,
                    latest_stable=latest,
                    latest_release_date=release_date,
                    breaking_changes=self._is_major_upgrade(current_version, latest),
                    major_versions_behind=self._get_major_diff(current_version, latest),
                    changelog_url=info.get("project_url") or f"https://pypi.org/project/{package}/",
                )

        except Exception as e:
            logger.warning(f"Error checking PyPI for {package}: {e}")
            return VersionInfo(
                package=package,
                registry="pypi",
                error=str(e),
            )

    async def _check_github(
        self,
        repo: str,
        current_version: str | None,
    ) -> VersionInfo:
        """Check GitHub releases for latest version.
        
        Args:
            repo: GitHub repo in "owner/repo" format.
            current_version: Current version for comparison.
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"https://api.github.com/repos/{repo}/releases/latest",
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "VersionChecker",
                    },
                )

                if response.status_code == 404:
                    return VersionInfo(
                        package=repo,
                        registry="github",
                        error="Repository or releases not found",
                    )

                if response.status_code != 200:
                    return VersionInfo(
                        package=repo,
                        registry="github",
                        error=f"GitHub API error: {response.status_code}",
                    )

                data = response.json()
                tag = data.get("tag_name", "")
                # Remove 'v' prefix if present
                latest = tag.lstrip("v")

                release_date = None
                published = data.get("published_at")
                if published:
                    try:
                        release_date = datetime.fromisoformat(
                            published.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                return VersionInfo(
                    package=repo,
                    registry="github",
                    current_version=current_version,
                    latest_stable=latest,
                    latest_release_date=release_date,
                    breaking_changes=self._is_major_upgrade(current_version, latest),
                    major_versions_behind=self._get_major_diff(current_version, latest),
                    changelog_url=data.get("html_url"),
                )

        except Exception as e:
            logger.warning(f"Error checking GitHub for {repo}: {e}")
            return VersionInfo(
                package=repo,
                registry="github",
                error=str(e),
            )

    def _detect_registry(self, package: str) -> str:
        """Auto-detect registry based on package name patterns."""
        # GitHub format: owner/repo
        if "/" in package and not package.startswith("@"):
            return "github"
        
        # npm scoped packages: @org/package
        if package.startswith("@"):
            return "npm"
        
        # Common Python package naming
        python_indicators = [
            "django", "flask", "fastapi", "pytest", "numpy", "pandas",
            "torch", "tensorflow", "requests", "pydantic", "sqlalchemy",
        ]
        if any(ind in package.lower() for ind in python_indicators):
            return "pypi"
        
        # Default to npm for most frontend packages
        return "npm"

    def _is_major_upgrade(
        self,
        current: str | None,
        latest: str | None,
    ) -> bool:
        """Check if upgrade involves major version change."""
        if not current or not latest:
            return False
        
        return self._get_major_diff(current, latest) > 0

    def _get_major_diff(
        self,
        current: str | None,
        latest: str | None,
    ) -> int:
        """Get difference in major versions."""
        if not current or not latest:
            return 0

        current_major = self._parse_major(current)
        latest_major = self._parse_major(latest)

        if current_major is None or latest_major is None:
            return 0

        return max(0, latest_major - current_major)

    def _parse_major(self, version: str) -> int | None:
        """Parse major version number from version string."""
        # Remove 'v' prefix and any pre-release suffix
        version = version.lstrip("v").split("-")[0].split("+")[0]
        
        # Extract first number
        match = re.match(r"(\d+)", version)
        if match:
            return int(match.group(1))
        return None
