"""Business logic analyzer using Generative AI.

Analyzes HOW an app makes money and grows by using LLM semantic analysis to detect:
- Authentication patterns (JWT, OAuth, session)
- Payment/subscription logic
- Monetization models (freemium, usage-based, subscription)
- Growth mechanisms (referrals, invites)
"""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from advisor.analysis.detectors.feature_extractor import Feature


logger = logging.getLogger(__name__)


class BusinessModel(BaseModel):
    """Business model analysis results."""

    auth_type: str = ""
    auth_providers: list[str] = Field(default_factory=list)
    payment_integrations: list[str] = Field(default_factory=list)
    monetization_type: str = ""  # freemium, subscription, usage-based, one-time
    monetization_signals: list[str] = Field(default_factory=list)
    growth_mechanisms: list[str] = Field(default_factory=list)
    revenue_drivers: list[str] = Field(default_factory=list)
    user_tiers: list[str] = Field(default_factory=list)


# High-value file patterns for context extraction
MANIFEST_FILES = [
    "package.json",
    "requirements.txt",
    "go.mod",
    "pom.xml",
    "gemfile",
    "cargo.toml",
    "pyproject.toml",
]

CONFIG_KEYWORDS = ["config", "settings", "env", ".env"]

LOGIC_KEYWORDS = [
    "auth",
    "payment",
    "stripe",
    "billing",
    "user",
    "subscription",
    "pricing",
    "plan",
    "checkout",
    "cart",
    "order",
    "invoice",
]


class BusinessAnalyzer:
    """Analyzes business logic and monetization patterns using LLM."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gpt-4o",
    ) -> None:
        """Initialize the analyzer.

        Args:
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model_name: Model to use (default: gpt-4o).
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model_name = model_name
        self._client = None

        # Initialize OpenAI client if available
        if self._api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def analyze(
        self,
        file_contents: dict[str, str],
        features: list[Feature],
    ) -> BusinessModel:
        """Analyze business model from codebase using LLM.

        Args:
            file_contents: Map of file paths to content.
            features: Detected features from FeatureExtractor.

        Returns:
            BusinessModel with detected patterns.
        """
        # Prepare context for LLM
        context = self._prepare_context(file_contents)

        # Try LLM analysis first
        if self._client and context:
            try:
                result = self._analyze_with_llm(context)
                if result:
                    # Infer revenue drivers from LLM results
                    result.revenue_drivers = self._infer_revenue_drivers(
                        result.payment_integrations,
                        result.monetization_type,
                        features,
                    )
                    return result
            except Exception as e:
                logger.warning(f"LLM analysis failed, using fallback: {e}")

        # Fallback: return empty model with warning
        logger.warning("No API key or LLM failed. Returning empty BusinessModel.")
        return self._fallback_analysis(file_contents, features)

    def _prepare_context(self, file_contents: dict[str, str]) -> str:
        """Prepare smart context for LLM by filtering high-value files.

        Args:
            file_contents: Map of file paths to content.

        Returns:
            Concatenated string of relevant file contents.
        """
        context_parts: list[str] = []
        total_chars = 0
        max_chars = 50000  # Limit total context size

        for path, content in file_contents.items():
            path_lower = path.lower()

            # Check if this is a high-value file
            is_manifest = any(m in path_lower for m in MANIFEST_FILES)
            is_config = any(k in path_lower for k in CONFIG_KEYWORDS)
            is_logic = any(k in path_lower for k in LOGIC_KEYWORDS)

            if is_manifest or is_config or is_logic:
                # Truncate large files to first 200 lines
                lines = content.split("\n")
                if len(lines) > 200:
                    truncated = "\n".join(lines[:200])
                    truncated += "\n... [TRUNCATED]"
                else:
                    truncated = content

                # Check total size
                if total_chars + len(truncated) > max_chars:
                    continue

                context_parts.append(f"=== FILE: {path} ===\n{truncated}")
                total_chars += len(truncated)

        return "\n\n".join(context_parts)

    def _analyze_with_llm(self, context: str) -> BusinessModel | None:
        """Analyze context using LLM.

        Args:
            context: Prepared code context.

        Returns:
            BusinessModel with detected patterns, or None if failed.
        """
        if not self._client:
            return None

        system_prompt = """You are a Venture Capital Technical Auditor specializing in SaaS business model analysis.

Your task is to analyze the provided code context and identify:
1. Authentication Provider (e.g., Auth0, Firebase, Clerk, Supabase, custom JWT)
2. Payment Integrations (e.g., Stripe, PayPal, Paddle, LemonSqueezy)
3. Monetization Model (Subscription, Freemium, Usage-based, One-time, Marketplace)
4. Growth Mechanisms (Referrals, Invites, Viral loops, Affiliate programs)
5. User Tiers (Free, Pro, Enterprise, etc.)

Be specific and cite evidence from the code. If you cannot determine something, leave the field empty.

You MUST return a valid JSON object strictly matching this schema:
{
    "auth_type": "string (e.g., 'JWT', 'OAuth', 'Session-based', 'Firebase Auth')",
    "auth_providers": ["list of auth providers detected"],
    "payment_integrations": ["list of payment processors"],
    "monetization_type": "string (e.g., 'subscription', 'freemium', 'usage-based', 'one-time')",
    "monetization_signals": ["list of signals found, e.g., 'subscription', 'trial', 'upgrade'"],
    "growth_mechanisms": ["list of growth mechanisms"],
    "user_tiers": ["list of tier names found"]
}

Return ONLY the JSON object, no explanation or markdown."""

        user_prompt = f"""Analyze the following codebase context for business model patterns:

{context}

Return the analysis as a JSON object matching the schema."""

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            if not content:
                return None

            # Parse JSON response
            data = json.loads(content)

            return BusinessModel(
                auth_type=data.get("auth_type", ""),
                auth_providers=data.get("auth_providers", []),
                payment_integrations=data.get("payment_integrations", []),
                monetization_type=data.get("monetization_type", ""),
                monetization_signals=data.get("monetization_signals", []),
                growth_mechanisms=data.get("growth_mechanisms", []),
                user_tiers=data.get("user_tiers", []),
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM API call failed: {e}")
            return None

    def _fallback_analysis(
        self,
        file_contents: dict[str, str],
        features: list[Feature],
    ) -> BusinessModel:
        """Basic fallback analysis when LLM is unavailable.

        Performs very simple keyword detection as a last resort.
        """
        all_content = " ".join(file_contents.values()).lower()

        # Simple keyword detection
        auth_providers = []
        if "stripe" in all_content:
            auth_providers.append("Stripe")
        if "auth0" in all_content:
            auth_providers.append("Auth0")
        if "firebase" in all_content:
            auth_providers.append("Firebase")
        if "supabase" in all_content:
            auth_providers.append("Supabase")

        payment_integrations = []
        if "stripe" in all_content:
            payment_integrations.append("Stripe")
        if "paypal" in all_content:
            payment_integrations.append("PayPal")
        if "paddle" in all_content:
            payment_integrations.append("Paddle")

        monetization_type = ""
        if "subscription" in all_content:
            monetization_type = "subscription"
        elif "freemium" in all_content or "free_tier" in all_content:
            monetization_type = "freemium"

        return BusinessModel(
            auth_type="Unknown (fallback)",
            auth_providers=auth_providers,
            payment_integrations=payment_integrations,
            monetization_type=monetization_type,
            monetization_signals=[],
            growth_mechanisms=[],
            revenue_drivers=self._infer_revenue_drivers(
                payment_integrations, monetization_type, features
            ),
            user_tiers=[],
        )

    def _infer_revenue_drivers(
        self,
        payment_integrations: list[str],
        monetization_type: str,
        features: list[Feature],
    ) -> list[str]:
        """Infer revenue drivers from detected patterns."""
        drivers: list[str] = []

        if payment_integrations:
            drivers.append(f"Payment processing via {', '.join(payment_integrations)}")

        if monetization_type:
            type_descriptions = {
                "subscription": "Recurring subscription revenue",
                "freemium": "Premium feature upgrades",
                "usage-based": "Usage-based billing",
                "one-time": "One-time purchase revenue",
            }
            if monetization_type in type_descriptions:
                drivers.append(type_descriptions[monetization_type])

        # Check for monetization-stage features
        monetization_features = [
            f.name for f in features if f.user_journey_stage == "monetization"
        ]
        if monetization_features:
            drivers.append(f"Monetization features: {', '.join(monetization_features)}")

        return drivers
