import asyncio
import time
from advisor.trends import query_planner, search_sources
from advisor.trends.models import SearchResult

async def test_performance():
    print("--- Starting Trend Optimization Verification ---")
    
    # 1. Test Query Planner
    print("\n1. Testing Query Planner...")
    tags = ["react", "django", "fastapi", "postgresql", "docker"]
    total_queries = 0
    for tag in tags:
        queries = query_planner.plan_queries(tag)
        total_queries += len(queries)
        print(f"  - {tag}: {len(queries)} queries")
    
    print(f"  Total queries for 5 tags: {total_queries}")
    if total_queries > 20: # Should be 5 tags * 3 queries = 15 max
         print("  [FAIL] Query count too high!")
    else:
         print("  [PASS] Query count optimized.")

    # 2. Test Search Sources (Mocked)
    print("\n2. Testing Search Sources Latency (Mocked)...")
    
    # Mock the actual API calls to test concurrency logic
    original_serper = search_sources._search_serper_single
    original_github = search_sources._search_github_repos
    original_hn = search_sources._search_hn_single
    
    async def mock_search(*args, **kwargs):
        await asyncio.sleep(1.0) # Simulate 1s latency per request
        return [SearchResult(title="Mock", url="http://mock.com", source="mock", score=1)]

    search_sources._search_serper_single = mock_search
    search_sources._search_github_repos = mock_search
    search_sources._search_hn_single = mock_search

    t0 = time.time()
    # Simulate a full batch for one tag
    # 3 Serper + 1 GitHub + 1 HN
    results = await search_sources.search_all(
        serper_queries=["q1", "q2", "q3"],
        github_queries=["g1"],
        hn_queries=["h1"]
    )
    t1 = time.time()
    duration = t1 - t0
    
    print(f"  Simulated search took: {duration:.2f}s")
    
    # Sequential would be: 3*1s (Serper) + 1s (GitHub) + 1s (HN) = 5s (plus sleeps)
    # Optimized should be: max(Serper_Batch, GitHub, HN) = ~1.3s (due to stagger)
    if duration < 2.5:
        print("  [PASS] Concurrency is working (Fast execution)")
    else:
        print(f"  [FAIL] Execution too slow ({duration}s), concurrency might be broken")

    # Restore mocks
    search_sources._search_serper_single = original_serper
    search_sources._search_github_repos = original_github
    search_sources._search_hn_single = original_hn
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_performance())
