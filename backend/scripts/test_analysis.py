#!/usr/bin/env python
"""Test script to verify end-to-end analysis flow.

Usage: uv run python scripts/test_analysis.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from advisor.analysis.orchestrator import AnalysisOrchestrator
from advisor.config import get_settings
from advisor.database.client import get_supabase_client


async def test_analysis():
    """Test the analysis flow with a sample repository."""
    print("=" * 60)
    print("AI Development Advisor - Test Script")
    print("=" * 60)

    # Check settings
    try:
        settings = get_settings()
        print(f"✓ Settings loaded: {settings.app_name}")
    except Exception as e:
        print(f"✗ Settings error: {e}")
        return

    # Check database connection
    try:
        client = get_supabase_client()
        print("✓ Supabase client created")
    except Exception as e:
        print(f"✗ Supabase error: {e}")
        print("  Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
        return

    # Test with a simple public repository
    repo_url = "https://github.com/expressjs/express"
    print(f"\n📦 Testing with: {repo_url}")

    try:
        orchestrator = AnalysisOrchestrator()
        print("  → Fetching repository...")
        result = await orchestrator.analyze(repo_url)

        print("\n✓ Analysis completed!")
        print(f"  Duration: {result.analysis_duration_ms}ms")
        print(f"  Files analyzed: {result.file_count}")
        print(f"  Model used: {result.model_used}")
        print(f"\n  Languages: {', '.join(result.tech_stack.languages)}")
        print(f"  Frameworks: {', '.join(result.tech_stack.frameworks)}")
        print(f"  Risks found: {len(result.risks_and_gaps)}")
        print(f"  Recommendations: {len(result.recommendations)}")

        print("\n" + "=" * 60)
        print("TECHNICAL SUMMARY (first 500 chars)")
        print("=" * 60)
        print(result.technical_summary[:500] + "...")

        print("\n" + "=" * 60)
        print("EXECUTIVE SUMMARY (first 500 chars)")
        print("=" * 60)
        print(result.executive_summary[:500] + "...")

    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_analysis())
