"""Risk and gap analysis.

Identifies technical debt, security concerns, and improvement opportunities.
"""

from typing import Any

from advisor.database.models import RiskItem, TechStackInfo

# Risk detection patterns
RISK_PATTERNS = {
    "outdated_dependencies": {
        "patterns": ["lodash@3", "react@16", "python 2", "node 12"],
        "category": "maintainability",
        "severity": "medium",
        "title": "Potentially Outdated Dependencies",
        "impact": "Missing security patches and modern features",
        "recommendation": "Audit and update dependencies to latest stable versions",
    },
    "no_testing": {
        "patterns": ["test", "spec", "__tests__", "pytest", "jest", "mocha"],
        "category": "maintainability",
        "severity": "high",
        "title": "Missing Test Coverage",
        "impact": "High risk of regressions and bugs in production",
        "recommendation": "Implement unit and integration tests for critical paths",
        "invert": True,  # Risk if NOT found
    },
    "hardcoded_secrets": {
        "patterns": [
            "password=",
            "api_key=",
            "secret=",
            "AWS_SECRET",
            "PRIVATE_KEY",
        ],
        "category": "security",
        "severity": "critical",
        "title": "Potential Hardcoded Secrets",
        "impact": "Credential exposure and security breach risk",
        "recommendation": "Use environment variables and secret management",
    },
    "no_ci_cd": {
        "patterns": [".github/workflows", "Jenkinsfile", ".gitlab-ci", ".circleci"],
        "category": "practices",
        "severity": "medium",
        "title": "No CI/CD Configuration",
        "impact": "Manual deployments increase error risk",
        "recommendation": "Set up automated testing and deployment pipelines",
        "invert": True,
    },
    "no_docker": {
        "patterns": ["Dockerfile", "docker-compose"],
        "category": "practices",
        "severity": "low",
        "title": "No Containerization",
        "impact": "Environment inconsistency across deployments",
        "recommendation": "Consider Docker for consistent environments",
        "invert": True,
    },
    "no_type_safety": {
        "patterns": ["tsconfig", "mypy", "pyright", "type hints"],
        "category": "maintainability",
        "severity": "medium",
        "title": "Limited Type Safety",
        "impact": "Runtime errors and reduced IDE support",
        "recommendation": "Adopt TypeScript or type hints for better reliability",
        "invert": True,
    },
    "no_documentation": {
        "patterns": ["README.md", "docs/", "CONTRIBUTING.md"],
        "category": "practices",
        "severity": "medium",
        "title": "Limited Documentation",
        "impact": "Difficult onboarding and knowledge transfer",
        "recommendation": "Add README, API docs, and architecture documentation",
        "invert": True,
    },
}


class RiskAnalyzer:
    """Analyzes repository for risks and gaps."""

    def analyze(
        self,
        file_tree: list[dict[str, Any]],
        file_contents: dict[str, str],
        tech_stack: TechStackInfo,
    ) -> list[RiskItem]:
        """Analyze repository for risks and technical debt.

        Args:
            file_tree: List of files in repository.
            file_contents: Map of file path to content.
            tech_stack: Detected technology stack.

        Returns:
            List of identified risks.
        """
        risks = []
        all_paths = " ".join([item["path"].lower() for item in file_tree])
        all_content = " ".join(file_contents.values()).lower()

        for risk_key, risk_info in RISK_PATTERNS.items():
            found = self._check_patterns(
                risk_info["patterns"],
                all_paths,
                all_content,
            )

            # Invert for "missing" patterns
            is_risk = not found if risk_info.get("invert") else found

            if is_risk:
                risks.append(
                    RiskItem(
                        category=risk_info["category"],
                        severity=risk_info["severity"],
                        title=risk_info["title"],
                        description=self._build_description(risk_key, risk_info),
                        impact=risk_info["impact"],
                        recommendation=risk_info["recommendation"],
                    )
                )

        # Add stack-specific risks
        risks.extend(self._check_stack_risks(tech_stack))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        risks.sort(key=lambda r: severity_order.get(r.severity, 99))

        return risks

    def _check_patterns(
        self,
        patterns: list[str],
        paths: str,
        content: str,
    ) -> bool:
        """Check if any pattern is found in paths or content."""
        combined = f"{paths} {content}"
        return any(pattern.lower() in combined for pattern in patterns)

    def _build_description(self, risk_key: str, risk_info: dict) -> str:
        """Build detailed description for a risk."""
        if risk_info.get("invert"):
            return (
                f"The repository appears to be missing: "
                f"{', '.join(risk_info['patterns'][:3])}"
            )
        return (
            f"Detected potential issue related to: "
            f"{', '.join(risk_info['patterns'][:3])}"
        )

    def _check_stack_risks(self, tech_stack: TechStackInfo) -> list[RiskItem]:
        """Check for stack-specific risks."""
        risks = []

        # Large number of languages might indicate complexity
        if len(tech_stack.languages) > 4:
            risks.append(
                RiskItem(
                    category="maintainability",
                    severity="medium",
                    title="Multi-Language Complexity",
                    description=f"Project uses {len(tech_stack.languages)} languages",
                    impact="Higher maintenance burden and skill requirements",
                    recommendation="Consider consolidating to fewer languages",
                )
            )

        # No framework detected
        if not tech_stack.frameworks:
            risks.append(
                RiskItem(
                    category="practices",
                    severity="low",
                    title="No Recognized Framework",
                    description="No standard web framework detected",
                    impact="May lack common patterns and conventions",
                    recommendation="Consider adopting a standard framework",
                )
            )

        return risks
