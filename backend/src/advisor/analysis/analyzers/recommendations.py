"""Forward-looking recommendations engine.

Generates actionable recommendations based on analysis results.
"""

from advisor.database.models import (
    ArchitecturePattern,
    Recommendation,
    RiskItem,
    TechStackInfo,
)

# Recommendation templates based on stack and patterns
RECOMMENDATION_TEMPLATES = {
    "add_typescript": {
        "category": "tooling",
        "priority": "medium",
        "title": "Adopt TypeScript",
        "description": "Add TypeScript for improved type safety and developer experience",
        "effort_estimate": "medium",
        "business_impact": "Reduced bugs and faster onboarding",
        "technical_steps": [
            "Install TypeScript and configure tsconfig.json",
            "Start with strict: false and gradually increase",
            "Convert files incrementally, starting with new code",
        ],
        "applies_to": {"languages": ["JavaScript"]},
    },
    "add_testing": {
        "category": "process",
        "priority": "high",
        "title": "Implement Automated Testing",
        "description": "Establish test coverage for critical functionality",
        "effort_estimate": "medium",
        "business_impact": "Higher reliability and confident deployments",
        "technical_steps": [
            "Set up testing framework (Jest/pytest)",
            "Write tests for critical business logic first",
            "Aim for 70%+ coverage on new code",
            "Integrate tests into CI pipeline",
        ],
        "requires_risk": "Missing Test Coverage",
    },
    "add_ci_cd": {
        "category": "process",
        "priority": "high",
        "title": "Set Up CI/CD Pipeline",
        "description": "Automate testing and deployment workflows",
        "effort_estimate": "small",
        "business_impact": "Faster, safer releases with less manual work",
        "technical_steps": [
            "Create GitHub Actions workflow",
            "Add automated testing on pull requests",
            "Configure staging deployment",
            "Add production deployment with approval gates",
        ],
        "requires_risk": "No CI/CD Configuration",
    },
    "add_docker": {
        "category": "tooling",
        "priority": "medium",
        "title": "Containerize Application",
        "description": "Use Docker for consistent development and deployment",
        "effort_estimate": "small",
        "business_impact": "Eliminate 'works on my machine' issues",
        "technical_steps": [
            "Create Dockerfile with multi-stage build",
            "Add docker-compose for local development",
            "Configure for production deployment",
        ],
        "requires_risk": "No Containerization",
    },
    "add_documentation": {
        "category": "process",
        "priority": "medium",
        "title": "Improve Documentation",
        "description": "Add comprehensive project documentation",
        "effort_estimate": "small",
        "business_impact": "Faster onboarding and knowledge sharing",
        "technical_steps": [
            "Write README with setup instructions",
            "Document architecture decisions (ADRs)",
            "Add API documentation",
            "Create contribution guidelines",
        ],
        "requires_risk": "Limited Documentation",
    },
    "modernize_react": {
        "category": "architecture",
        "priority": "medium",
        "title": "Modernize React Patterns",
        "description": "Adopt modern React 18+ patterns",
        "effort_estimate": "large",
        "business_impact": "Better performance and maintainability",
        "technical_steps": [
            "Migrate class components to hooks",
            "Implement concurrent features where beneficial",
            "Consider React Server Components for Next.js",
        ],
        "applies_to": {"frameworks": ["React"]},
    },
    "security_audit": {
        "category": "security",
        "priority": "high",
        "title": "Conduct Security Audit",
        "description": "Review and address security concerns",
        "effort_estimate": "medium",
        "business_impact": "Protect against breaches and compliance issues",
        "technical_steps": [
            "Run dependency vulnerability scan",
            "Review authentication and authorization",
            "Check for exposed secrets in codebase",
            "Implement security headers and CSP",
        ],
        "requires_risk": "Potential Hardcoded Secrets",
    },
}


class RecommendationEngine:
    """Generates forward-looking recommendations."""

    def generate(
        self,
        tech_stack: TechStackInfo,
        architecture: list[ArchitecturePattern],
        risks: list[RiskItem],
    ) -> list[Recommendation]:
        """Generate recommendations based on analysis.

        Args:
            tech_stack: Detected technology stack.
            architecture: Identified architecture patterns.
            risks: Identified risks and gaps.

        Returns:
            Prioritized list of recommendations.
        """
        recommendations = []
        risk_titles = {r.title for r in risks}

        for rec_info in RECOMMENDATION_TEMPLATES.values():
            # Check if recommendation applies
            if not self._should_apply(rec_info, tech_stack, risk_titles):
                continue

            recommendations.append(
                Recommendation(
                    category=rec_info["category"],
                    priority=rec_info["priority"],
                    title=rec_info["title"],
                    description=rec_info["description"],
                    effort_estimate=rec_info["effort_estimate"],
                    business_impact=rec_info["business_impact"],
                    technical_steps=rec_info["technical_steps"],
                )
            )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations[:10]  # Top 10 recommendations

    def _should_apply(
        self,
        rec_info: dict,
        tech_stack: TechStackInfo,
        risk_titles: set[str],
    ) -> bool:
        """Check if a recommendation should be applied."""
        # Check if requires a specific risk
        if "requires_risk" in rec_info and rec_info["requires_risk"] not in risk_titles:
            return False

        # Check if applies to specific stack
        if "applies_to" in rec_info:
            applies = rec_info["applies_to"]

            if "languages" in applies and not any(
                lang in tech_stack.languages for lang in applies["languages"]
            ):
                return False

            if "frameworks" in applies and not any(
                fw in tech_stack.frameworks for fw in applies["frameworks"]
            ):
                return False

        return True
