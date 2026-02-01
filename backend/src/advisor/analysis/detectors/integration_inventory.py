"""Integration inventory for cataloging external dependencies.

Scans codebase to detect:
- Cloud services (AWS, GCP, Azure)
- SaaS integrations (Stripe, SendGrid, etc.)
- Authentication providers
- Monitoring and analytics tools
"""

import re

from pydantic import BaseModel, Field

from advisor.database.models import TechStackInfo


class Integration(BaseModel):
    """External integration detected in codebase."""

    name: str
    category: str  # cloud, payment, auth, monitoring, analytics, communication
    detected_from: str  # package.json, import, SDK usage
    description: str = ""
    cost_tier: str = ""  # free, low, medium, high, enterprise


# Integration detection patterns
INTEGRATIONS = {
    # Cloud Services
    "aws_s3": {
        "patterns": ["@aws-sdk/client-s3", "boto3", "s3client", "aws-sdk/client-s3"],
        "name": "AWS S3",
        "category": "cloud",
        "description": "Cloud object storage",
        "cost_tier": "usage-based",
    },
    "aws_lambda": {
        "patterns": ["@aws-sdk/client-lambda", "serverless", "aws-lambda"],
        "name": "AWS Lambda",
        "category": "cloud",
        "description": "Serverless functions",
        "cost_tier": "usage-based",
    },
    "aws_sqs": {
        "patterns": ["@aws-sdk/client-sqs", "sqs", "amazon-sqs"],
        "name": "AWS SQS",
        "category": "cloud",
        "description": "Message queue service",
        "cost_tier": "low",
    },
    "aws_dynamodb": {
        "patterns": ["@aws-sdk/client-dynamodb", "dynamodb"],
        "name": "AWS DynamoDB",
        "category": "cloud",
        "description": "NoSQL database",
        "cost_tier": "usage-based",
    },
    "gcp_storage": {
        "patterns": ["@google-cloud/storage", "google.cloud.storage"],
        "name": "Google Cloud Storage",
        "category": "cloud",
        "description": "Cloud object storage",
        "cost_tier": "usage-based",
    },
    "azure_storage": {
        "patterns": ["@azure/storage-blob", "azure.storage"],
        "name": "Azure Blob Storage",
        "category": "cloud",
        "description": "Cloud object storage",
        "cost_tier": "usage-based",
    },
    "vercel": {
        "patterns": ["@vercel", "vercel.json", "vercel/"],
        "name": "Vercel",
        "category": "cloud",
        "description": "Frontend hosting & serverless",
        "cost_tier": "freemium",
    },
    "cloudflare": {
        "patterns": ["cloudflare", "wrangler", "workers"],
        "name": "Cloudflare",
        "category": "cloud",
        "description": "CDN & edge computing",
        "cost_tier": "freemium",
    },

    # Payment Providers
    "stripe": {
        "patterns": ["stripe", "@stripe/stripe-js"],
        "name": "Stripe",
        "category": "payment",
        "description": "Payment processing",
        "cost_tier": "transaction-based",
    },
    "paypal": {
        "patterns": ["paypal", "@paypal/react-paypal-js"],
        "name": "PayPal",
        "category": "payment",
        "description": "Payment processing",
        "cost_tier": "transaction-based",
    },

    # Authentication
    "auth0": {
        "patterns": ["@auth0", "auth0"],
        "name": "Auth0",
        "category": "auth",
        "description": "Identity management",
        "cost_tier": "freemium",
    },
    "clerk": {
        "patterns": ["@clerk/nextjs", "@clerk"],
        "name": "Clerk",
        "category": "auth",
        "description": "Authentication & user management",
        "cost_tier": "freemium",
    },
    "firebase_auth": {
        "patterns": ["firebase/auth", "@firebase/auth"],
        "name": "Firebase Auth",
        "category": "auth",
        "description": "Authentication service",
        "cost_tier": "freemium",
    },
    "supabase_auth": {
        "patterns": ["@supabase/auth-helpers", "supabase.auth"],
        "name": "Supabase Auth",
        "category": "auth",
        "description": "Authentication service",
        "cost_tier": "free",
    },

    # Monitoring & Error Tracking
    "sentry": {
        "patterns": ["@sentry", "sentry-sdk", "sentry_sdk"],
        "name": "Sentry",
        "category": "monitoring",
        "description": "Error tracking & monitoring",
        "cost_tier": "freemium",
    },
    "datadog": {
        "patterns": ["dd-trace", "datadog", "ddtrace"],
        "name": "Datadog",
        "category": "monitoring",
        "description": "APM & infrastructure monitoring",
        "cost_tier": "high",
    },
    "logrocket": {
        "patterns": ["logrocket"],
        "name": "LogRocket",
        "category": "monitoring",
        "description": "Session replay & monitoring",
        "cost_tier": "medium",
    },

    # Analytics
    "google_analytics": {
        "patterns": ["gtag", "google-analytics", "ua-"],
        "name": "Google Analytics",
        "category": "analytics",
        "description": "Web analytics",
        "cost_tier": "free",
    },
    "mixpanel": {
        "patterns": ["mixpanel"],
        "name": "Mixpanel",
        "category": "analytics",
        "description": "Product analytics",
        "cost_tier": "freemium",
    },
    "amplitude": {
        "patterns": ["amplitude", "@amplitude"],
        "name": "Amplitude",
        "category": "analytics",
        "description": "Product analytics",
        "cost_tier": "freemium",
    },
    "segment": {
        "patterns": ["analytics.js", "@segment", "segment.com"],
        "name": "Segment",
        "category": "analytics",
        "description": "Customer data platform",
        "cost_tier": "medium",
    },
    "posthog": {
        "patterns": ["posthog"],
        "name": "PostHog",
        "category": "analytics",
        "description": "Product analytics",
        "cost_tier": "freemium",
    },

    # Communication
    "sendgrid": {
        "patterns": ["@sendgrid", "sendgrid"],
        "name": "SendGrid",
        "category": "communication",
        "description": "Email delivery",
        "cost_tier": "freemium",
    },
    "twilio": {
        "patterns": ["twilio"],
        "name": "Twilio",
        "category": "communication",
        "description": "SMS & voice",
        "cost_tier": "usage-based",
    },
    "resend": {
        "patterns": ["resend"],
        "name": "Resend",
        "category": "communication",
        "description": "Email API",
        "cost_tier": "freemium",
    },
    "intercom": {
        "patterns": ["intercom"],
        "name": "Intercom",
        "category": "communication",
        "description": "Customer messaging",
        "cost_tier": "high",
    },

    # Databases
    "mongodb": {
        "patterns": ["mongodb", "mongoose"],
        "name": "MongoDB",
        "category": "database",
        "description": "Document database",
        "cost_tier": "freemium",
    },
    "redis": {
        "patterns": ["redis", "ioredis", "redis-py"],
        "name": "Redis",
        "category": "database",
        "description": "In-memory data store",
        "cost_tier": "freemium",
    },
    "planetscale": {
        "patterns": ["planetscale"],
        "name": "PlanetScale",
        "category": "database",
        "description": "Serverless MySQL",
        "cost_tier": "freemium",
    },
    "supabase": {
        "patterns": ["@supabase/supabase-js", "supabase"],
        "name": "Supabase",
        "category": "database",
        "description": "PostgreSQL + BaaS",
        "cost_tier": "freemium",
    },
}


class IntegrationInventory:
    """Catalogs all external integrations in a codebase."""

    def scan(
        self,
        file_contents: dict[str, str],
        tech_stack: TechStackInfo,
    ) -> list[Integration]:
        """Scan codebase for external integrations.

        Args:
            file_contents: Map of file paths to content.
            tech_stack: Detected technology stack.

        Returns:
            List of detected integrations.
        """
        integrations: list[Integration] = []
        all_content = " ".join(file_contents.values()).lower()

        for integration_id, config in INTEGRATIONS.items():
            for pattern in config["patterns"]:
                if pattern.lower() in all_content:
                    # Find which file contains this integration
                    source = self._find_source(pattern, file_contents)

                    integrations.append(Integration(
                        name=config["name"],
                        category=config["category"],
                        detected_from=source,
                        description=config["description"],
                        cost_tier=config["cost_tier"],
                    ))
                    break  # Only add once per integration

        # Deduplicate by name
        seen = set()
        unique: list[Integration] = []
        for i in integrations:
            if i.name not in seen:
                seen.add(i.name)
                unique.append(i)

        return unique

    def _find_source(
        self,
        pattern: str,
        file_contents: dict[str, str],
    ) -> str:
        """Find which file contains an integration pattern."""
        pattern_lower = pattern.lower()

        for path, content in file_contents.items():
            if pattern_lower in content.lower():
                return path

        return "Unknown"

    def get_by_category(
        self,
        integrations: list[Integration],
        category: str,
    ) -> list[Integration]:
        """Filter integrations by category."""
        return [i for i in integrations if i.category == category]

    def estimate_monthly_cost(
        self,
        integrations: list[Integration],
    ) -> dict[str, str]:
        """Estimate monthly costs by category.

        Returns rough cost estimates for planning.
        """
        cost_map = {
            "free": "$0",
            "freemium": "$0-50/mo",
            "low": "$20-100/mo",
            "usage-based": "Varies with usage",
            "transaction-based": "2-3% per transaction",
            "medium": "$100-500/mo",
            "high": "$500-2000/mo",
            "enterprise": "$2000+/mo",
        }

        category_costs: dict[str, list[str]] = {}

        for i in integrations:
            if i.category not in category_costs:
                category_costs[i.category] = []
            if i.cost_tier in cost_map:
                category_costs[i.category].append(
                    f"{i.name}: {cost_map[i.cost_tier]}"
                )

        return {k: ", ".join(v) for k, v in category_costs.items()}
