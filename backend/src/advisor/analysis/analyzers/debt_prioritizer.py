"""Technical debt prioritizer using industry-standard linters.

Orchestrates Bandit (security), Pylint (Python quality), and ESLint (JS/TS quality)
to identify and prioritize technical debt items.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from advisor.database.models import RiskItem, TechStackInfo


logger = logging.getLogger(__name__)


class DebtItem(BaseModel):
    """Technical debt item with priority scoring."""

    category: str  # security, performance, maintainability, scalability
    title: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    impact_score: int = Field(default=50, ge=0, le=100)
    likelihood_score: int = Field(default=50, ge=0, le=100)
    time_to_failure: str = ""  # immediate, 1-3 months, 3-6 months, 6+ months
    effort_to_fix: str = ""  # hours, days, weeks
    fix_suggestion: str = ""
    evidence: list[str] = Field(default_factory=list)

    @property
    def priority_score(self) -> int:
        """Calculate priority score (0-100)."""
        return (self.impact_score + self.likelihood_score) // 2


# Severity to score mapping
SEVERITY_SCORES = {
    "critical": {"impact": 95, "likelihood": 90},
    "high": {"impact": 80, "likelihood": 70},
    "medium": {"impact": 50, "likelihood": 50},
    "low": {"impact": 30, "likelihood": 40},
}


class DebtPrioritizer:
    """Identifies and prioritizes technical debt using external linters."""

    def prioritize(
        self,
        file_contents: dict[str, str],
        risks: list[RiskItem],
        tech_stack: TechStackInfo,
    ) -> list[DebtItem]:
        """Analyze codebase for technical debt using linters.

        Args:
            file_contents: Map of file paths to content.
            risks: Previously identified risks.
            tech_stack: Detected technology stack.

        Returns:
            List of prioritized debt items (top 15).
        """
        debt_items: list[DebtItem] = []

        # Create temporary directory with file contents for linter analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_files_to_temp(file_contents, temp_path)

            # Run linters and collect findings
            debt_items.extend(self._run_linter(
                temp_path, "bandit",
                ["-r", str(temp_path), "-f", "json", "-q"],
                "bandit",
            ))
            debt_items.extend(self._run_linter(
                temp_path, "pylint",
                ["--output-format=json", "--disable=C0114,C0115,C0116", str(temp_path)],
                "pylint", [".py"],
            ))
            debt_items.extend(self._run_linter(
                temp_path, "eslint",
                [str(temp_path), "--format", "json", "--no-error-on-unmatched-pattern"],
                "eslint", [".js", ".ts", ".jsx", ".tsx"],
            ))

        # Structure-based checks (tests, CI, large files)
        debt_items.extend(self._check_structure(file_contents))

        # Convert relevant risks to debt items
        debt_items.extend(self._convert_risks_to_debt(risks))

        # Sort by priority score (highest first)
        debt_items.sort(key=lambda d: d.priority_score, reverse=True)

        return debt_items[:15]  # Top 15 items

    def _write_files_to_temp(
        self,
        file_contents: dict[str, str],
        temp_path: Path,
    ) -> None:
        """Write file contents to temporary directory for linter analysis."""
        for file_path, content in file_contents.items():
            # Create subdirectories as needed
            target = temp_path / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                target.write_text(content, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to write {file_path}: {e}")

    def _run_linter(
        self,
        temp_path: Path,
        tool: str,
        args: list[str],
        parser: str,
        file_ext: list[str] | None = None,
    ) -> list[DebtItem]:
        """Run a linter and parse results.

        Args:
            temp_path: Temp directory with files.
            tool: Linter executable name.
            args: Command line arguments.
            parser: Parser type ('bandit', 'pylint', 'eslint').
            file_ext: Optional file extensions to check for.
        """
        items: list[DebtItem] = []

        if not shutil.which(tool):
            logger.warning(f"{tool} not installed, skipping scan")
            return items

        if file_ext:
            files = []
            for ext in file_ext:
                files.extend(temp_path.rglob(f"*{ext}"))
            if not files:
                return items

        try:
            result = subprocess.run(
                [tool] + args,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if not result.stdout:
                return items

            data = json.loads(result.stdout)
            items = getattr(self, f"_parse_{parser}")(data)

        except subprocess.TimeoutExpired:
            logger.warning(f"{tool} scan timed out")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {tool} output: {e}")
        except Exception as e:
            logger.warning(f"{tool} scan failed: {e}")

        return items

    def _parse_bandit(self, data: dict) -> list[DebtItem]:
        """Parse Bandit JSON output."""
        items = []
        for issue in data.get("results", []):
            sev = {"HIGH": "critical", "MEDIUM": "high"}.get(
                issue.get("issue_severity", "").upper(), "medium"
            )
            scores = SEVERITY_SCORES.get(sev, SEVERITY_SCORES["medium"])
            items.append(DebtItem(
                category="security",
                title=issue.get("issue_text", "Security Issue"),
                description=f"{issue.get('test_name', 'Unknown')}: {issue.get('issue_text', '')}",
                severity=sev,
                impact_score=scores["impact"],
                likelihood_score=scores["likelihood"],
                time_to_failure="immediate" if sev == "critical" else "1-3 months",
                effort_to_fix="days",
                fix_suggestion=issue.get("more_info", "Review and fix"),
                evidence=[f"{issue.get('filename', '?')}:{issue.get('line_number', 0)}"],
            ))
        return items

    def _parse_pylint(self, findings: list) -> list[DebtItem]:
        """Parse Pylint JSON output."""
        items, seen = [], set()
        for f in findings:
            key = f"{f.get('message-id', '')}:{f.get('message', '')}"
            if key in seen:
                continue
            seen.add(key)
            sev = {"error": "high", "warning": "medium"}.get(f.get("type", ""), "low")
            scores = SEVERITY_SCORES.get(sev, SEVERITY_SCORES["medium"])
            items.append(DebtItem(
                category="maintainability",
                title=f.get("symbol", f.get("message-id", "Issue")),
                description=f.get("message", ""),
                severity=sev,
                impact_score=scores["impact"],
                likelihood_score=scores["likelihood"],
                time_to_failure="3-6 months" if sev == "high" else "6+ months",
                effort_to_fix="hours",
                fix_suggestion=f"Fix {f.get('symbol', 'issue')}",
                evidence=[f"{f.get('path', '?')}:{f.get('line', 0)}"],
            ))
        return items

    def _parse_eslint(self, findings: list) -> list[DebtItem]:
        """Parse ESLint JSON output."""
        items, seen = [], set()
        for file_result in findings:
            for msg in file_result.get("messages", []):
                rule = msg.get("ruleId", "unknown")
                if rule in seen:
                    continue
                seen.add(rule)
                sev = "high" if msg.get("severity", 1) == 2 else "medium"
                scores = SEVERITY_SCORES.get(sev, SEVERITY_SCORES["medium"])
                items.append(DebtItem(
                    category="maintainability",
                    title=rule,
                    description=msg.get("message", "Code quality issue"),
                    severity=sev,
                    impact_score=scores["impact"],
                    likelihood_score=scores["likelihood"],
                    time_to_failure="3-6 months" if sev == "high" else "6+ months",
                    effort_to_fix="hours",
                    fix_suggestion=f"Fix ESLint: {rule}",
                    evidence=[f"{file_result.get('filePath', '?')}:{msg.get('line', 0)}"],
                ))
        return items

    def _check_structure(
        self,
        file_contents: dict[str, str],
    ) -> list[DebtItem]:
        """Check codebase structure for debt indicators."""
        items: list[DebtItem] = []
        paths = list(file_contents.keys())

        # Check for tests
        has_tests = any(
            "test" in p.lower() or "spec" in p.lower()
            for p in paths
        )
        if not has_tests:
            items.append(DebtItem(
                category="maintainability",
                title="Missing Test Coverage",
                description="No automated tests detected in the codebase",
                severity="high",
                impact_score=80,
                likelihood_score=70,
                time_to_failure="3-6 months",
                effort_to_fix="weeks",
                fix_suggestion="Add unit and integration tests for critical paths",
            ))

        # Check for CI
        has_ci = any(".github/workflows" in p or ".gitlab-ci" in p for p in paths)
        if not has_ci:
            items.append(DebtItem(
                category="maintainability",
                title="No CI/CD Pipeline",
                description="No continuous integration configuration detected",
                severity="medium",
                impact_score=60,
                likelihood_score=50,
                time_to_failure="6+ months",
                effort_to_fix="days",
                fix_suggestion="Set up GitHub Actions or similar CI/CD pipeline",
            ))

        # Check for large files
        large_files = [
            p for p, c in file_contents.items()
            if c.count("\n") > 500
        ]
        if large_files:
            items.append(DebtItem(
                category="maintainability",
                title="Large Source Files",
                description=f"{len(large_files)} files exceed 500 lines",
                severity="medium",
                impact_score=40,
                likelihood_score=60,
                time_to_failure="6+ months",
                effort_to_fix="days",
                fix_suggestion="Refactor into smaller, focused modules",
                evidence=large_files[:5],
            ))

        return items

    def _convert_risks_to_debt(self, risks: list[RiskItem]) -> list[DebtItem]:
        """Convert high-severity risks to debt items."""
        items = []
        for risk in risks:
            if risk.severity in ["high", "critical"]:
                items.append(DebtItem(
                    category=risk.category,
                    title=risk.title,
                    description=risk.description,
                    severity=risk.severity,
                    impact_score=90 if risk.severity == "critical" else 70,
                    likelihood_score=70,
                    fix_suggestion=risk.recommendation,
                ))
        return items
