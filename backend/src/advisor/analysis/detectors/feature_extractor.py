"""Feature extractor for user-facing functionality detection.

Extracts what users can DO in the app by analyzing:
- API endpoints (REST routes, decorators)
- Third-party integrations
- User journey stages
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from advisor.database.models import TechStackInfo


class Feature(BaseModel):
    """User-facing feature detected in codebase."""

    name: str
    description: str
    endpoints: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    user_journey_stage: str = ""  # signup, onboarding, core, monetization


# Endpoint patterns for different frameworks
FASTAPI_ROUTE_PATTERN = re.compile(
    r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

EXPRESS_ROUTE_PATTERN = re.compile(
    r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

DJANGO_URL_PATTERN = re.compile(
    r'path\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

NEXTJS_API_PATTERN = re.compile(
    r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)',
    re.IGNORECASE,
)

# Feature detection patterns
FEATURE_PATTERNS = {
    "authentication": {
        "keywords": ["login", "signup", "register", "auth", "session", "logout"],
        "stage": "signup",
        "description": "User authentication and session management",
    },
    "user_profile": {
        "keywords": ["profile", "account", "settings", "preferences"],
        "stage": "onboarding",
        "description": "User profile and account management",
    },
    "payments": {
        "keywords": ["payment", "checkout", "stripe", "billing", "subscription"],
        "stage": "monetization",
        "description": "Payment processing and billing",
    },
    "notifications": {
        "keywords": ["notification", "email", "sms", "push", "alert"],
        "stage": "core",
        "description": "User notification system",
    },
    "file_upload": {
        "keywords": ["upload", "file", "image", "media", "attachment"],
        "stage": "core",
        "description": "File and media upload handling",
    },
    "search": {
        "keywords": ["search", "query", "filter", "find"],
        "stage": "core",
        "description": "Search and filtering functionality",
    },
    "analytics": {
        "keywords": ["analytics", "tracking", "metrics", "stats", "dashboard"],
        "stage": "core",
        "description": "Analytics and reporting dashboard",
    },
    "social": {
        "keywords": ["share", "invite", "referral", "social", "friend"],
        "stage": "core",
        "description": "Social features and sharing",
    },
    "admin": {
        "keywords": ["admin", "manage", "moderate", "permission", "role"],
        "stage": "core",
        "description": "Admin panel and management tools",
    },
}

# Integration patterns for third-party services
INTEGRATION_PATTERNS = {
    "stripe": ("Stripe", "Payment processing"),
    "paypal": ("PayPal", "Payment processing"),
    "sendgrid": ("SendGrid", "Email service"),
    "twilio": ("Twilio", "SMS and messaging"),
    "firebase": ("Firebase", "Backend services"),
    "supabase": ("Supabase", "Backend services"),
    "aws-sdk": ("AWS", "Cloud services"),
    "s3": ("AWS S3", "File storage"),
    "cloudinary": ("Cloudinary", "Media management"),
    "algolia": ("Algolia", "Search service"),
    "sentry": ("Sentry", "Error monitoring"),
    "segment": ("Segment", "Analytics"),
    "mixpanel": ("Mixpanel", "Product analytics"),
    "intercom": ("Intercom", "Customer messaging"),
    "auth0": ("Auth0", "Authentication"),
    "clerk": ("Clerk", "Authentication"),
}


class FeatureExtractor:
    """Extracts user-facing features from codebase."""

    def extract(
        self,
        file_contents: dict[str, str],
        tech_stack: TechStackInfo,
    ) -> list[Feature]:
        """Extract features from file contents.

        Args:
            file_contents: Map of file paths to content.
            tech_stack: Detected technology stack.

        Returns:
            List of detected features.
        """
        endpoints = self._extract_endpoints(file_contents, tech_stack)
        integrations = self._detect_integrations(file_contents)
        features = self._map_to_features(endpoints, integrations, file_contents)

        return features

    def _extract_endpoints(
        self,
        file_contents: dict[str, str],
        tech_stack: TechStackInfo,
    ) -> list[dict[str, Any]]:
        """Extract API endpoints from source files."""
        endpoints: list[dict[str, Any]] = []

        for path, content in file_contents.items():
            # FastAPI/Flask decorators
            for match in FASTAPI_ROUTE_PATTERN.finditer(content):
                endpoints.append({
                    "method": match.group(1).upper(),
                    "path": match.group(2),
                    "source": path,
                })

            # Express.js routes
            for match in EXPRESS_ROUTE_PATTERN.finditer(content):
                endpoints.append({
                    "method": match.group(1).upper(),
                    "path": match.group(2),
                    "source": path,
                })

            # Django URL patterns
            for match in DJANGO_URL_PATTERN.finditer(content):
                endpoints.append({
                    "method": "ANY",
                    "path": match.group(1),
                    "source": path,
                })

            # Next.js API routes
            for match in NEXTJS_API_PATTERN.finditer(content):
                # Derive path from file location
                api_path = self._derive_nextjs_path(path)
                endpoints.append({
                    "method": match.group(1).upper(),
                    "path": api_path,
                    "source": path,
                })

        return endpoints

    def _derive_nextjs_path(self, file_path: str) -> str:
        """Derive API path from Next.js file structure."""
        # pages/api/users/[id].ts -> /api/users/:id
        # app/api/users/route.ts -> /api/users
        path = file_path.replace("\\", "/")

        if "pages/api" in path:
            api_part = path.split("pages/api")[1]
            api_part = re.sub(r"\[(\w+)\]", r":\1", api_part)
            api_part = re.sub(r"\.(ts|js|tsx|jsx)$", "", api_part)
            return f"/api{api_part}"

        if "app/api" in path:
            api_part = path.split("app/api")[1]
            api_part = re.sub(r"/route\.(ts|js)$", "", api_part)
            api_part = re.sub(r"\[(\w+)\]", r":\1", api_part)
            return f"/api{api_part}"

        return file_path

    def _detect_integrations(
        self,
        file_contents: dict[str, str],
    ) -> list[dict[str, str]]:
        """Detect third-party integrations."""
        integrations: list[dict[str, str]] = []
        all_content = " ".join(file_contents.values()).lower()

        for pattern, (name, category) in INTEGRATION_PATTERNS.items():
            if pattern in all_content:
                integrations.append({
                    "name": name,
                    "category": category,
                    "pattern": pattern,
                })

        return integrations

    def _map_to_features(
        self,
        endpoints: list[dict[str, Any]],
        integrations: list[dict[str, str]],
        file_contents: dict[str, str],
    ) -> list[Feature]:
        """Map endpoints and integrations to user features."""
        features: list[Feature] = []
        all_content = " ".join(file_contents.values()).lower()

        for feature_id, config in FEATURE_PATTERNS.items():
            # Check if feature keywords appear in codebase
            matches = [kw for kw in config["keywords"] if kw in all_content]

            if matches:
                # Find related endpoints
                related_endpoints = [
                    f"{e['method']} {e['path']}"
                    for e in endpoints
                    if any(kw in e["path"].lower() for kw in config["keywords"])
                ]

                # Find related integrations
                related_integrations = [
                    i["name"]
                    for i in integrations
                    if any(kw in i["pattern"] for kw in config["keywords"])
                ]

                features.append(Feature(
                    name=feature_id.replace("_", " ").title(),
                    description=config["description"],
                    endpoints=related_endpoints[:5],
                    integrations=related_integrations,
                    user_journey_stage=config["stage"],
                ))

        return features
