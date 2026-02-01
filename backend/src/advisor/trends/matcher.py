"""Trend-to-stack matcher - matches trends to user's technology stack.

Analyzes trends and calculates relevance scores based on:
- Direct technology matches
- Related technology matches
- Category alignment
- Business impact potential
"""

from advisor.database.models import TechStackInfo
from advisor.trends.models import (
    TECH_KEYWORDS,
    TrendCategory,
    TrendItem,
    TrendMatch,
    TrendReport,
)


# Technology relationships (what pairs well together)
TECH_RELATIONS = {
    "python": ["ai", "database", "devops"],
    "javascript": ["react", "vue", "svelte", "cloud"],
    "typescript": ["react", "javascript", "cloud"],
    "react": ["javascript", "typescript", "cloud"],
    "rust": ["devops", "database"],
    "go": ["devops", "cloud", "database"],
    "ai": ["python", "vector_db", "cloud"],
}


class TrendMatcher:
    """Matches technology trends to user's stack."""

    def match_trends(
        self,
        trends: list[TrendItem],
        tech_stack: TechStackInfo,
    ) -> TrendReport:
        """Match trends to user's tech stack and generate report.

        Args:
            trends: List of trends from aggregator.
            tech_stack: User's detected technology stack.

        Returns:
            TrendReport with matched and scored trends.
        """
        # Build user's technology set
        user_techs = self._build_tech_set(tech_stack)

        # Score and match each trend
        matches: list[TrendMatch] = []
        for trend in trends:
            match = self._score_trend(trend, user_techs)
            if match.relevance_score > 0.1:  # Minimum relevance threshold
                matches.append(match)

        # Sort by relevance
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        # Extract insights
        top_techs = self._extract_top_technologies(trends[:50])
        emerging = self._find_emerging_tools(matches)

        return TrendReport(
            total_trends_scanned=len(trends),
            relevant_trends=matches[:20],  # Top 20 relevant
            top_technologies=top_techs[:10],
            emerging_tools=emerging[:5],
            recommendations=self._generate_recommendations(matches[:10]),
        )

    def _build_tech_set(self, tech_stack: TechStackInfo) -> set[str]:
        """Build a set of normalized technology names."""
        techs: set[str] = set()

        # Add languages
        for lang in tech_stack.languages:
            techs.add(self._normalize_tech(lang))

        # Add frameworks
        for fw in tech_stack.frameworks:
            techs.add(self._normalize_tech(fw))

        # Add databases
        for db in tech_stack.databases:
            techs.add(self._normalize_tech(db))

        # Add tools
        for tool in tech_stack.tools:
            techs.add(self._normalize_tech(tool))

        return techs

    def _normalize_tech(self, tech: str) -> str:
        """Normalize technology name."""
        tech_lower = tech.lower()

        # Map common variations
        mappings = {
            "node.js": "javascript",
            "nodejs": "javascript",
            "ts": "typescript",
            "py": "python",
            "postgres": "database",
            "postgresql": "database",
            "mongodb": "database",
            "redis": "database",
            "next.js": "react",
            "nextjs": "react",
            "nuxt": "vue",
            "django": "python",
            "fastapi": "python",
            "flask": "python",
            "express": "javascript",
        }

        return mappings.get(tech_lower, tech_lower)

    def _score_trend(
        self,
        trend: TrendItem,
        user_techs: set[str],
    ) -> TrendMatch:
        """Score a trend's relevance to user's stack."""
        matching_techs: list[str] = []
        score = 0.0

        # Direct matches (highest weight)
        for tech in trend.technologies:
            normalized = self._normalize_tech(tech)
            if normalized in user_techs:
                matching_techs.append(tech)
                score += 0.3

        # Related technology matches
        for tech in trend.technologies:
            normalized = self._normalize_tech(tech)
            related = TECH_RELATIONS.get(normalized, [])
            for rel in related:
                if rel in user_techs:
                    score += 0.1

        # Category bonus
        category_relevance = self._category_relevance(trend.category, user_techs)
        score += category_relevance * 0.2

        # Popularity bonus (normalized)
        if trend.score > 100:
            score += 0.1

        # Cap at 1.0
        score = min(score, 1.0)

        # Determine opportunity type
        opportunity = self._determine_opportunity(trend, user_techs)

        return TrendMatch(
            trend=trend,
            relevance_score=round(score, 2),
            matching_technologies=matching_techs,
            opportunity_type=opportunity,
            business_impact=self._estimate_impact(score, trend),
        )

    def _category_relevance(
        self,
        category: TrendCategory,
        user_techs: set[str],
    ) -> float:
        """Calculate category relevance to user stack."""
        category_tech_map = {
            TrendCategory.AI_ML: ["python", "ai", "javascript"],
            TrendCategory.DEVOPS: ["cloud", "devops", "docker"],
            TrendCategory.DATABASE: ["database", "python", "javascript"],
            TrendCategory.FRAMEWORK: ["react", "vue", "svelte", "python"],
            TrendCategory.SECURITY: ["javascript", "python", "go"],
        }

        relevant_techs = category_tech_map.get(category, [])
        matches = sum(1 for t in relevant_techs if t in user_techs)
        return matches / max(len(relevant_techs), 1)

    def _determine_opportunity(
        self,
        trend: TrendItem,
        user_techs: set[str],
    ) -> str:
        """Determine what type of opportunity this trend represents."""
        title_lower = trend.title.lower()

        if "upgrade" in title_lower or "new version" in title_lower:
            return "upgrade"
        if "migration" in title_lower or "moving to" in title_lower:
            return "migration"
        if any(t in user_techs for t in trend.technologies):
            return "best_practice"

        return "new_feature"

    def _estimate_impact(self, score: float, trend: TrendItem) -> str:
        """Estimate business impact of adopting this trend."""
        if score > 0.7 and trend.score > 200:
            return "high"
        if score > 0.4 or trend.score > 100:
            return "medium"
        return "low"

    def _extract_top_technologies(self, trends: list[TrendItem]) -> list[str]:
        """Extract most mentioned technologies."""
        tech_counts: dict[str, int] = {}
        for trend in trends:
            for tech in trend.technologies:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1

        sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
        return [tech for tech, _ in sorted_techs]

    def _find_emerging_tools(self, matches: list[TrendMatch]) -> list[str]:
        """Find tools that are emerging and relevant."""
        emerging: list[str] = []
        for match in matches:
            if match.opportunity_type == "new_feature":
                for tech in match.trend.technologies:
                    if tech not in emerging:
                        emerging.append(tech)
        return emerging

    def _generate_recommendations(self, top_matches: list[TrendMatch]) -> list[str]:
        """Generate actionable recommendations from top matches."""
        recommendations: list[str] = []

        for match in top_matches[:5]:
            if match.opportunity_type == "upgrade":
                recommendations.append(
                    f"Consider upgrading: {match.trend.title[:50]}..."
                )
            elif match.opportunity_type == "new_feature":
                recommendations.append(
                    f"New feature opportunity: {match.trend.title[:50]}..."
                )
            elif match.opportunity_type == "best_practice":
                recommendations.append(
                    f"Best practice: {match.trend.title[:50]}..."
                )

        return recommendations
