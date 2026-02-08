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
            debt_items.extend(self._run_bandit(temp_path))
            debt_items.extend(self._run_pylint(temp_path))
            debt_items.extend(self._run_eslint(temp_path))

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

    def _run_bandit(self, temp_path: Path) -> list[DebtItem]:
        """Run Bandit security scanner on Python files.

        Returns:
            List of security-related DebtItems from Bandit findings.
        """
        items: list[DebtItem] = []

        # Check if bandit is installed
        if not shutil.which("bandit"):
            logger.warning("Bandit not installed, skipping security scan")
            return items

        try:
            result = subprocess.run(
                ["bandit", "-r", str(temp_path), "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Bandit returns non-zero even with findings, so check stdout
            if result.stdout:
                data = json.loads(result.stdout)
                results = data.get("results", [])

                for issue in results:
                    # Map Bandit severity to our severity
                    bandit_severity = issue.get("issue_severity", "MEDIUM").upper()
                    if bandit_severity == "HIGH":
                        severity = "critical"
                    elif bandit_severity == "MEDIUM":
                        severity = "high"
                    else:
                        severity = "medium"

                    scores = SEVERITY_SCORES.get(severity, SEVERITY_SCORES["medium"])

                    items.append(DebtItem(
                        category="security",
                        title=issue.get("issue_text", "Security Issue"),
                        description=(
                            f"{issue.get('test_name', 'Unknown')}: "
                            f"{issue.get('issue_text', 'Security vulnerability detected')}"
                        ),
                        severity=severity,
                        impact_score=scores["impact"],
                        likelihood_score=scores["likelihood"],
                        time_to_failure="immediate" if severity == "critical" else "1-3 months",
                        effort_to_fix="days",
                        fix_suggestion=issue.get("more_info", "Review and fix security issue"),
                        evidence=[
                            f"{issue.get('filename', 'unknown')}:{issue.get('line_number', 0)}"
                        ],
                    ))

        except subprocess.TimeoutExpired:
            logger.warning("Bandit scan timed out")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Bandit output: {e}")
        except Exception as e:
            logger.warning(f"Bandit scan failed: {e}")

        return items

    def _run_pylint(self, temp_path: Path) -> list[DebtItem]:
        """Run Pylint on Python files for code quality analysis.

        Returns:
            List of maintainability DebtItems from Pylint findings.
        """
        items: list[DebtItem] = []

        # Check if pylint is installed
        if not shutil.which("pylint"):
            logger.warning("Pylint not installed, skipping Python quality scan")
            return items

        # Find Python files
        py_files = list(temp_path.rglob("*.py"))
        if not py_files:
            return items

        try:
            result = subprocess.run(
                [
                    "pylint",
                    "--output-format=json",
                    "--disable=C0114,C0115,C0116",  # Skip missing docstrings (too noisy)
                    str(temp_path),
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.stdout:
                findings = json.loads(result.stdout)

                # Group by message to avoid duplicates
                seen_messages: set[str] = set()

                for finding in findings:
                    msg_id = finding.get("message-id", "")
                    msg = finding.get("message", "")
                    msg_key = f"{msg_id}:{msg}"

                    if msg_key in seen_messages:
                        continue
                    seen_messages.add(msg_key)

                    # Map Pylint type to severity
                    pylint_type = finding.get("type", "convention")
                    if pylint_type == "error":
                        severity = "high"
                    elif pylint_type == "warning":
                        severity = "medium"
                    else:  # convention, refactor
                        severity = "low"

                    scores = SEVERITY_SCORES.get(severity, SEVERITY_SCORES["medium"])

                    items.append(DebtItem(
                        category="maintainability",
                        title=finding.get("symbol", msg_id) or "Code Quality Issue",
                        description=msg,
                        severity=severity,
                        impact_score=scores["impact"],
                        likelihood_score=scores["likelihood"],
                        time_to_failure="3-6 months" if severity == "high" else "6+ months",
                        effort_to_fix="hours",
                        fix_suggestion=f"Fix {finding.get('symbol', 'issue')} in code",
                        evidence=[
                            f"{finding.get('path', 'unknown')}:{finding.get('line', 0)}"
                        ],
                    ))

        except subprocess.TimeoutExpired:
            logger.warning("Pylint scan timed out")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Pylint output: {e}")
        except Exception as e:
            logger.warning(f"Pylint scan failed: {e}")

        return items

    def _run_eslint(self, temp_path: Path) -> list[DebtItem]:
        """Run ESLint on JavaScript/TypeScript files.

        Returns:
            List of maintainability DebtItems from ESLint findings.
        """
        items: list[DebtItem] = []

        # Check if eslint is installed
        if not shutil.which("eslint"):
            logger.warning("ESLint not installed, skipping JS/TS quality scan")
            return items

        # Find JS/TS files
        js_files = list(temp_path.rglob("*.js")) + list(temp_path.rglob("*.ts"))
        js_files += list(temp_path.rglob("*.jsx")) + list(temp_path.rglob("*.tsx"))
        if not js_files:
            return items

        try:
            result = subprocess.run(
                [
                    "eslint",
                    str(temp_path),
                    "--format", "json",
                    "--no-error-on-unmatched-pattern",
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.stdout:
                findings = json.loads(result.stdout)

                # Group by rule to avoid too many duplicates
                seen_rules: set[str] = set()

                for file_result in findings:
                    for message in file_result.get("messages", []):
                        rule_id = message.get("ruleId", "unknown")

                        if rule_id in seen_rules:
                            continue
                        seen_rules.add(rule_id)

                        # Map ESLint severity (2 = error, 1 = warning)
                        eslint_severity = message.get("severity", 1)
                        if eslint_severity == 2:
                            severity = "high"
                        else:
                            severity = "medium"

                        scores = SEVERITY_SCORES.get(severity, SEVERITY_SCORES["medium"])

                        items.append(DebtItem(
                            category="maintainability",
                            title=rule_id or "ESLint Issue",
                            description=message.get("message", "Code quality issue"),
                            severity=severity,
                            impact_score=scores["impact"],
                            likelihood_score=scores["likelihood"],
                            time_to_failure="3-6 months" if severity == "high" else "6+ months",
                            effort_to_fix="hours",
                            fix_suggestion=f"Fix ESLint rule: {rule_id}",
                            evidence=[
                                f"{file_result.get('filePath', 'unknown')}:{message.get('line', 0)}"
                            ],
                        ))

        except subprocess.TimeoutExpired:
            logger.warning("ESLint scan timed out")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse ESLint output: {e}")
        except Exception as e:
            logger.warning(f"ESLint scan failed: {e}")

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
