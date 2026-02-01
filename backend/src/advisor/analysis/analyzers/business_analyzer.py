"""Business logic analyzer for monetization and growth detection.

Analyzes HOW an app makes money and grows by detecting:
- Authentication patterns (JWT, OAuth, session)
- Payment/subscription logic
- Monetization models (freemium, usage-based, subscription)
- Growth mechanisms (referrals, invites)
"""

import re

from pydantic import BaseModel, Field

from advisor.analysis.feature_extractor import Feature


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


# Authentication detection patterns
AUTH_PATTERNS = {
    "jwt": {
        "patterns": ["jwt", "jsonwebtoken", "jose", "jwt.sign", "jwt.verify"],
        "type": "JWT (Stateless)",
    },
    "session": {
        "patterns": ["express-session", "session_id", "sessionstore", "sessionmiddleware"],
        "type": "Session-based",
    },
    "oauth": {
        "patterns": ["oauth", "passport", "next-auth", "authjs", "oauth2"],
        "type": "OAuth",
    },
    "firebase_auth": {
        "patterns": ["firebase/auth", "firebaseauth", "firebase.auth"],
        "type": "Firebase Auth",
    },
    "auth0": {
        "patterns": ["@auth0", "auth0", "auth0-react"],
        "type": "Auth0",
    },
    "clerk": {
        "patterns": ["@clerk", "clerk/nextjs", "clerkauthprovider"],
        "type": "Clerk",
    },
    "supabase_auth": {
        "patterns": ["supabase.auth", "@supabase/auth-helpers"],
        "type": "Supabase Auth",
    },
}

# Payment integration patterns
PAYMENT_PATTERNS = {
    "stripe": ["stripe", "@stripe/stripe-js", "stripe-node", "stripe.customers"],
    "paypal": ["paypal", "@paypal/react-paypal-js", "paypal-rest-sdk"],
    "paddle": ["paddle", "paddle.js"],
    "lemonsqueezy": ["lemonsqueezy", "@lemonsqueezy"],
    "razorpay": ["razorpay"],
    "square": ["square", "squareup"],
}

# Monetization signal patterns
MONETIZATION_SIGNALS = {
    "subscription": {
        "patterns": [
            "subscription", "plan", "tier", "billing_cycle", "trial",
            "cancel_subscription", "upgrade", "downgrade",
        ],
        "type": "subscription",
    },
    "freemium": {
        "patterns": [
            "free_tier", "premium", "pro_plan", "limit_reached",
            "upgrade_prompt", "feature_gate", "usage_limit",
        ],
        "type": "freemium",
    },
    "usage_based": {
        "patterns": [
            "credits", "tokens", "api_calls", "usage", "metered",
            "overage", "quota", "rate_limit",
        ],
        "type": "usage-based",
    },
    "one_time": {
        "patterns": [
            "purchase", "one_time", "lifetime", "buy_now",
            "checkout", "cart",
        ],
        "type": "one-time",
    },
}

# Growth mechanism patterns
GROWTH_PATTERNS = {
    "referral": ["referral", "refer", "invite_code", "referral_code", "referee"],
    "invite": ["invite", "invitation", "invite_link", "share_link"],
    "social_sharing": ["share", "twitter", "facebook", "linkedin", "social_share"],
    "viral_loop": ["viral", "share_reward", "invite_reward", "referral_bonus"],
    "affiliate": ["affiliate", "partner_code", "commission"],
    "waitlist": ["waitlist", "early_access", "beta_signup"],
}


class BusinessAnalyzer:
    """Analyzes business logic and monetization patterns."""

    def analyze(
        self,
        file_contents: dict[str, str],
        features: list[Feature],
    ) -> BusinessModel:
        """Analyze business model from codebase.

        Args:
            file_contents: Map of file paths to content.
            features: Detected features from FeatureExtractor.

        Returns:
            BusinessModel with detected patterns.
        """
        all_content = " ".join(file_contents.values()).lower()

        auth_type, auth_providers = self._detect_auth(all_content)
        payment_integrations = self._detect_payments(all_content)
        monetization_type, signals = self._detect_monetization(all_content)
        growth_mechanisms = self._detect_growth(all_content)
        user_tiers = self._detect_user_tiers(all_content)
        revenue_drivers = self._infer_revenue_drivers(
            payment_integrations, monetization_type, features
        )

        return BusinessModel(
            auth_type=auth_type,
            auth_providers=auth_providers,
            payment_integrations=payment_integrations,
            monetization_type=monetization_type,
            monetization_signals=signals,
            growth_mechanisms=growth_mechanisms,
            revenue_drivers=revenue_drivers,
            user_tiers=user_tiers,
        )

    def _detect_auth(self, content: str) -> tuple[str, list[str]]:
        """Detect authentication type and providers."""
        providers: list[str] = []
        primary_type = ""

        for auth_id, config in AUTH_PATTERNS.items():
            if any(p in content for p in config["patterns"]):
                providers.append(auth_id.replace("_", " ").title())
                if not primary_type:
                    primary_type = config["type"]

        return primary_type or "Unknown", providers

    def _detect_payments(self, content: str) -> list[str]:
        """Detect payment integrations."""
        integrations: list[str] = []

        for provider, patterns in PAYMENT_PATTERNS.items():
            if any(p in content for p in patterns):
                integrations.append(provider.title())

        return integrations

    def _detect_monetization(self, content: str) -> tuple[str, list[str]]:
        """Detect monetization model and signals."""
        signals: list[str] = []
        detected_types: dict[str, int] = {}

        for model_id, config in MONETIZATION_SIGNALS.items():
            matches = [p for p in config["patterns"] if p in content]
            if matches:
                signals.extend(matches[:3])
                detected_types[config["type"]] = len(matches)

        # Return the type with most signals
        if detected_types:
            primary_type = max(detected_types, key=detected_types.get)
            return primary_type, signals

        return "", signals

    def _detect_growth(self, content: str) -> list[str]:
        """Detect growth mechanisms."""
        mechanisms: list[str] = []

        for mechanism, patterns in GROWTH_PATTERNS.items():
            if any(p in content for p in patterns):
                mechanisms.append(mechanism.replace("_", " ").title())

        return mechanisms

    def _detect_user_tiers(self, content: str) -> list[str]:
        """Detect user tier/plan names."""
        tiers: list[str] = []

        # Common tier patterns
        tier_patterns = [
            r"\b(free|basic|starter)\b",
            r"\b(pro|professional|plus)\b",
            r"\b(premium|advanced)\b",
            r"\b(enterprise|business|team)\b",
        ]

        for pattern in tier_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                tiers.append(matches[0].title())

        return list(set(tiers))

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
