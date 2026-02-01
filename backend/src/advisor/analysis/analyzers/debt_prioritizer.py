"""Technical debt prioritizer for identifying and ranking debt items.

Analyzes codebase for technical debt indicators:
- Security vulnerabilities
- EOL technology usage
- Performance bottlenecks
- Missing best practices
- Scalability issues
"""

import re

from pydantic import BaseModel, Field

from advisor.database.models import RiskItem, TechStackInfo


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


# Technical debt detection patterns
DEBT_PATTERNS = {
    "no_tests": {
        "indicators": [],  # Checked by file structure
        "category": "maintainability",
        "title": "Missing Test Coverage",
        "description": "No automated tests detected in the codebase",
        "severity": "high",
        "impact": 80,
        "likelihood": 70,
        "time_to_failure": "3-6 months",
        "effort": "weeks",
        "fix": "Add unit and integration tests for critical paths",
    },
    "no_ci": {
        "indicators": [],  # Checked by .github/workflows presence
        "category": "maintainability",
        "title": "No CI/CD Pipeline",
        "description": "No continuous integration configuration detected",
        "severity": "medium",
        "impact": 60,
        "likelihood": 50,
        "time_to_failure": "6+ months",
        "effort": "days",
        "fix": "Set up GitHub Actions or similar CI/CD pipeline",
    },
    "hardcoded_secrets": {
        "indicators": [
            r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\']+["\']',
            r'sk[-_]live[-_][a-zA-Z0-9]+',  # Stripe keys
            r'ghp_[a-zA-Z0-9]+',  # GitHub tokens
        ],
        "category": "security",
        "title": "Hardcoded Secrets",
        "description": "Potential API keys or secrets found in source code",
        "severity": "critical",
        "impact": 95,
        "likelihood": 90,
        "time_to_failure": "immediate",
        "effort": "hours",
        "fix": "Move secrets to environment variables or a secrets manager",
    },
    "sql_injection": {
        "indicators": [
            r'execute\s*\(\s*["\'].*\%.*["\']',
            r'execute\s*\(\s*f["\']',
            r'query\s*\(\s*["\'].*\+',
        ],
        "category": "security",
        "title": "Potential SQL Injection",
        "description": "Dynamic SQL queries without parameterization detected",
        "severity": "critical",
        "impact": 95,
        "likelihood": 60,
        "time_to_failure": "immediate",
        "effort": "days",
        "fix": "Use parameterized queries or ORM",
    },
    "missing_error_handling": {
        "indicators": [
            r'except\s*:\s*\n\s*pass',
            r'catch\s*\(\s*\w*\s*\)\s*{\s*}',
        ],
        "category": "maintainability",
        "title": "Silent Error Handling",
        "description": "Empty catch/except blocks suppress errors",
        "severity": "medium",
        "impact": 50,
        "likelihood": 80,
        "time_to_failure": "3-6 months",
        "effort": "hours",
        "fix": "Add proper error logging and handling",
    },
    "console_logs": {
        "indicators": [
            r'console\.log\(',
            r'print\(',
        ],
        "category": "maintainability",
        "title": "Debug Statements in Code",
        "description": "Console.log or print statements found in production code",
        "severity": "low",
        "impact": 20,
        "likelihood": 90,
        "time_to_failure": "6+ months",
        "effort": "hours",
        "fix": "Replace with proper logging framework",
    },
    "large_files": {
        "indicators": [],  # Checked by file size
        "category": "maintainability",
        "title": "Large Source Files",
        "description": "Source files exceeding 500 lines detected",
        "severity": "medium",
        "impact": 40,
        "likelihood": 60,
        "time_to_failure": "6+ months",
        "effort": "days",
        "fix": "Refactor into smaller, focused modules",
    },
    "todo_fixme": {
        "indicators": [
            r'#\s*TODO\s*:',
            r'//\s*TODO\s*:',
            r'#\s*FIXME',
            r'//\s*FIXME',
            r'#\s*HACK',
        ],
        "category": "maintainability",
        "title": "Unresolved TODOs/FIXMEs",
        "description": "Multiple TODO or FIXME comments found in codebase",
        "severity": "low",
        "impact": 30,
        "likelihood": 80,
        "time_to_failure": "6+ months",
        "effort": "varies",
        "fix": "Review and resolve or schedule outstanding TODOs",
    },
    "no_type_hints": {
        "indicators": [
            r'def\s+\w+\s*\([^:)]+\)\s*:',  # Python function without type hints
        ],
        "category": "maintainability",
        "title": "Missing Type Annotations",
        "description": "Functions without type hints reduce code clarity",
        "severity": "low",
        "impact": 35,
        "likelihood": 70,
        "time_to_failure": "6+ months",
        "effort": "days",
        "fix": "Add type annotations incrementally, use pyright/mypy",
    },
}


class DebtPrioritizer:
    """Identifies and prioritizes technical debt."""

    def prioritize(
        self,
        file_contents: dict[str, str],
        risks: list[RiskItem],
        tech_stack: TechStackInfo,
    ) -> list[DebtItem]:
        """Analyze codebase for technical debt.

        Args:
            file_contents: Map of file paths to content.
            risks: Previously identified risks.
            tech_stack: Detected technology stack.

        Returns:
            List of prioritized debt items.
        """
        debt_items: list[DebtItem] = []

        # Pattern-based detection
        for debt_id, config in DEBT_PATTERNS.items():
            matches = self._find_pattern_matches(
                file_contents, config.get("indicators", [])
            )
            if matches:
                debt_items.append(self._create_debt_item(config, matches))

        # Structure-based checks
        debt_items.extend(self._check_structure(file_contents))

        # Convert relevant risks to debt items
        debt_items.extend(self._convert_risks_to_debt(risks))

        # Sort by priority score
        debt_items.sort(key=lambda d: d.priority_score, reverse=True)

        return debt_items[:15]  # Top 15 items

    def _find_pattern_matches(
        self,
        file_contents: dict[str, str],
        patterns: list[str],
    ) -> list[str]:
        """Find files matching any of the patterns."""
        matches = []
        for path, content in file_contents.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matches.append(path)
                    break
        return matches

    def _create_debt_item(
        self,
        config: dict,
        matches: list[str],
    ) -> DebtItem:
        """Create a debt item from config and matches."""
        return DebtItem(
            category=config["category"],
            title=config["title"],
            description=config["description"],
            severity=config["severity"],
            impact_score=config["impact"],
            likelihood_score=config["likelihood"],
            time_to_failure=config["time_to_failure"],
            effort_to_fix=config["effort"],
            fix_suggestion=config["fix"],
            evidence=matches[:5],  # Top 5 examples
        )

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
            config = DEBT_PATTERNS["no_tests"]
            items.append(DebtItem(
                category=config["category"],
                title=config["title"],
                description=config["description"],
                severity=config["severity"],
                impact_score=config["impact"],
                likelihood_score=config["likelihood"],
                time_to_failure=config["time_to_failure"],
                effort_to_fix=config["effort"],
                fix_suggestion=config["fix"],
            ))

        # Check for CI
        has_ci = any(".github/workflows" in p or ".gitlab-ci" in p for p in paths)
        if not has_ci:
            config = DEBT_PATTERNS["no_ci"]
            items.append(DebtItem(
                category=config["category"],
                title=config["title"],
                description=config["description"],
                severity=config["severity"],
                impact_score=config["impact"],
                likelihood_score=config["likelihood"],
                time_to_failure=config["time_to_failure"],
                effort_to_fix=config["effort"],
                fix_suggestion=config["fix"],
            ))

        # Check for large files
        large_files = [
            p for p, c in file_contents.items()
            if c.count("\n") > 500
        ]
        if large_files:
            config = DEBT_PATTERNS["large_files"]
            items.append(DebtItem(
                category=config["category"],
                title=config["title"],
                description=f"{len(large_files)} files exceed 500 lines",
                severity=config["severity"],
                impact_score=config["impact"],
                likelihood_score=config["likelihood"],
                time_to_failure=config["time_to_failure"],
                effort_to_fix=config["effort"],
                fix_suggestion=config["fix"],
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
