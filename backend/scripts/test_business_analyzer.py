"""Test script for BusinessAnalyzer with LLM integration."""

import sys
sys.path.insert(0, ".")

from advisor.analysis.analyzers.business_analyzer import BusinessAnalyzer, BusinessModel

# Sample file contents simulating a SaaS app
test_files = {
    "package.json": """
{
  "name": "saas-app",
  "dependencies": {
    "@stripe/stripe-js": "^2.0.0",
    "@auth0/auth0-react": "^2.0.0",
    "next-auth": "^4.0.0"
  }
}
""",
    "src/config/settings.py": """
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
SUBSCRIPTION_TRIAL_DAYS = 14
""",
    "src/auth/provider.tsx": """
import { Auth0Provider } from '@auth0/auth0-react';

export function AuthProvider({ children }) {
  return (
    <Auth0Provider
      domain={process.env.AUTH0_DOMAIN}
      clientId={process.env.AUTH0_CLIENT_ID}
    >
      {children}
    </Auth0Provider>
  );
}
""",
    "src/billing/subscription.py": """
import stripe

class SubscriptionService:
    def create_subscription(self, customer_id: str, plan: str):
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": self.get_price_id(plan)}],
            trial_period_days=14,
        )
    
    def upgrade_plan(self, subscription_id: str, new_plan: str):
        # Upgrade from free to pro or enterprise
        pass
    
    def cancel_subscription(self, subscription_id: str):
        stripe.Subscription.delete(subscription_id)
""",
    "src/pricing/plans.py": """
PLANS = {
    "free": {"price": 0, "features": ["basic"]},
    "pro": {"price": 29, "features": ["basic", "advanced", "priority_support"]},
    "enterprise": {"price": 99, "features": ["all", "custom_integrations", "sla"]},
}

def get_plan_limits(tier: str):
    limits = {
        "free": {"api_calls": 1000, "users": 1},
        "pro": {"api_calls": 50000, "users": 10},
        "enterprise": {"api_calls": -1, "users": -1},  # Unlimited
    }
    return limits.get(tier, limits["free"])
""",
    "src/growth/referral.py": """
class ReferralService:
    def generate_referral_code(self, user_id: str) -> str:
        return f"REF-{user_id[:8]}"
    
    def apply_referral_bonus(self, referrer_id: str, referee_id: str):
        # Give both users 1 month free
        pass
    
    def track_invite(self, invite_code: str, new_user_id: str):
        pass
"""
}

print("=" * 60)
print("Testing BusinessAnalyzer")
print("=" * 60)

# Test 1: Without API key (fallback mode)
print("\n[TEST 1] Fallback mode (no API key):")
print("-" * 40)

analyzer = BusinessAnalyzer(api_key=None)
result = analyzer.analyze(test_files, [])

print(f"Auth Type: {result.auth_type}")
print(f"Auth Providers: {result.auth_providers}")
print(f"Payment Integrations: {result.payment_integrations}")
print(f"Monetization Type: {result.monetization_type}")
print(f"Monetization Signals: {result.monetization_signals}")
print(f"Growth Mechanisms: {result.growth_mechanisms}")
print(f"User Tiers: {result.user_tiers}")
print(f"Revenue Drivers: {result.revenue_drivers}")

# Test 2: Context preparation
print("\n[TEST 2] Context Preparation:")
print("-" * 40)
context = analyzer._prepare_context(test_files)
print(f"Context length: {len(context)} characters")
print(f"Files included in context:")
for line in context.split("\n"):
    if line.startswith("=== FILE:"):
        print(f"  - {line.replace('=== FILE:', '').replace('===', '').strip()}")

print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
