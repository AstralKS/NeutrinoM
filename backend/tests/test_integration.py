"""Integration tests using a real GitHub repository.

Tests each feature step-by-step, then the full flow.
Run: uv run pytest tests/test_integration.py -v -s
"""

import pytest

# Test repository
TEST_REPO_URL = "https://github.com/AstralKS/LSTM_FROM_SCRATCH"
TEST_OWNER = "AstralKS"
TEST_REPO = "LSTM_FROM_SCRATCH"


class TestGitHubClientIntegration:
    """Step 1: Test GitHub client can fetch real repository data."""

    @pytest.mark.asyncio
    async def test_parse_repo_url(self):
        """Test URL parsing."""
        from advisor.github.client import GitHubClient

        owner, repo = GitHubClient.parse_repo_url(TEST_REPO_URL)

        assert owner == TEST_OWNER
        assert repo == TEST_REPO
        print(f"[OK] Parsed URL: {owner}/{repo}")

    @pytest.mark.asyncio
    async def test_fetch_repo_metadata(self):
        """Test fetching repository metadata."""
        from advisor.github.client import GitHubClient

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)

        assert metadata is not None
        assert "default_branch" in metadata
        print(f"[OK] Repo metadata: {metadata.get('name')}")
        print(f"     Default branch: {metadata.get('default_branch')}")
        print(f"     Size: {metadata.get('size')} KB")

    @pytest.mark.asyncio
    async def test_fetch_file_tree(self):
        """Test fetching file tree."""
        from advisor.github.client import GitHubClient

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")

        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        assert len(file_tree) > 0
        print(f"[OK] File tree: {len(file_tree)} files/folders")

        # Show sample files
        for item in file_tree[:5]:
            print(f"     - {item['path']} ({item['type']})")

    @pytest.mark.asyncio
    async def test_fetch_file_content(self):
        """Test fetching file content."""
        from advisor.github.client import GitHubClient

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")

        # Try to fetch README
        content = await client.get_file_content(
            TEST_OWNER, TEST_REPO, "README.md", branch
        )

        assert content is not None
        assert len(content) > 0
        print(f"[OK] README.md: {len(content)} chars")
        print(f"     Preview: {content[:100]}...")


class TestParserIntegration:
    """Step 2: Test file parser with real file tree."""

    @pytest.mark.asyncio
    async def test_parse_real_file_tree(self):
        """Test parsing real file tree."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        # Convert to expected format
        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)

        assert structure.total_files > 0
        print(f"[OK] Parsed structure:")
        print(f"     Total files: {structure.total_files}")
        print(f"     Code files: {len(structure.code_files)}")
        print(f"     Config files: {len(structure.config_files)}")
        print(f"     Doc files: {len(structure.doc_files)}")

    @pytest.mark.asyncio
    async def test_get_priority_files(self):
        """Test priority file selection."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)
        priority_files = RepositoryParser.get_files_to_analyze(structure)

        assert len(priority_files) > 0
        print(f"[OK] Priority files to analyze: {len(priority_files)}")
        for f in priority_files[:10]:
            print(f"     - {f}")


class TestStackDetectorIntegration:
    """Step 3: Test stack detection with real repository."""

    @pytest.mark.asyncio
    async def test_detect_tech_stack(self):
        """Test technology stack detection."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser
        from advisor.analysis.stack_detector import StackDetector

        # Fetch repository data
        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        # Parse structure
        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)
        priority_files = RepositoryParser.get_files_to_analyze(structure)

        # Fetch some content
        file_contents = {}
        for path in priority_files[:5]:
            try:
                content = await client.get_file_content(
                    TEST_OWNER, TEST_REPO, path, branch
                )
                if content:
                    file_contents[path] = content
            except Exception:
                pass

        # Convert FileInfo to dicts
        all_files = structure.code_files + structure.config_files
        file_dicts = [
            {"path": f.path, "type": f.type, "size": f.size}
            for f in all_files
        ]

        # Detect stack
        detector = StackDetector()
        tech_stack = detector.detect(file_dicts, file_contents)

        print(f"[OK] Tech stack detected:")
        print(f"     Languages: {tech_stack.languages}")
        print(f"     Frameworks: {tech_stack.frameworks}")
        print(f"     Tools: {tech_stack.tools}")

        # LSTM repo should have Python
        assert "Python" in tech_stack.languages


class TestArchitectureAnalyzerIntegration:
    """Step 4: Test architecture detection with real repository."""

    @pytest.mark.asyncio
    async def test_detect_architecture(self):
        """Test architecture pattern detection."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser
        from advisor.analysis.architecture import ArchitectureAnalyzer

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)

        # Convert FileInfo to dicts
        all_files = structure.code_files + structure.config_files
        file_dicts = [
            {"path": f.path, "type": f.type, "size": f.size}
            for f in all_files
        ]

        analyzer = ArchitectureAnalyzer()
        patterns = analyzer.analyze(file_dicts, {})

        print(f"[OK] Architecture patterns detected: {len(patterns)}")
        for pattern in patterns:
            print(f"     - {pattern.pattern_name} ({pattern.confidence:.0%})")


class TestRiskAnalyzerIntegration:
    """Step 5: Test risk detection with real repository."""

    @pytest.mark.asyncio
    async def test_detect_risks(self):
        """Test risk detection."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser
        from advisor.analysis.stack_detector import StackDetector
        from advisor.analysis.risk_analyzer import RiskAnalyzer

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)

        all_files = structure.code_files + structure.config_files
        file_dicts = [
            {"path": f.path, "type": f.type, "size": f.size}
            for f in all_files
        ]

        detector = StackDetector()
        tech_stack = detector.detect(file_dicts, {})

        analyzer = RiskAnalyzer()
        risks = analyzer.analyze(file_dicts, {}, tech_stack)

        print(f"[OK] Risks detected: {len(risks)}")
        for risk in risks:
            print(f"     - [{risk.severity.upper()}] {risk.title}")


class TestRecommendationEngineIntegration:
    """Step 6: Test recommendation generation."""

    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """Test recommendation generation."""
        from advisor.github.client import GitHubClient
        from advisor.github.parser import RepositoryParser
        from advisor.analysis.stack_detector import StackDetector
        from advisor.analysis.architecture import ArchitectureAnalyzer
        from advisor.analysis.risk_analyzer import RiskAnalyzer
        from advisor.analysis.recommendations import RecommendationEngine

        client = GitHubClient()
        metadata = await client.get_repo_metadata(TEST_OWNER, TEST_REPO)
        branch = metadata.get("default_branch", "main")
        file_tree = await client.get_file_tree(TEST_OWNER, TEST_REPO, branch)

        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)

        all_files = structure.code_files + structure.config_files
        file_dicts = [
            {"path": f.path, "type": f.type, "size": f.size}
            for f in all_files
        ]

        detector = StackDetector()
        tech_stack = detector.detect(file_dicts, {})

        arch_analyzer = ArchitectureAnalyzer()
        architecture = arch_analyzer.analyze(file_dicts, {})

        risk_analyzer = RiskAnalyzer()
        risks = risk_analyzer.analyze(file_dicts, {}, tech_stack)

        engine = RecommendationEngine()
        recommendations = engine.generate(tech_stack, architecture, risks)

        print(f"[OK] Recommendations generated: {len(recommendations)}")
        for rec in recommendations[:5]:
            print(f"     - [{rec.priority.upper()}] {rec.title}")


class TestFullAnalysisFlow:
    """Step 7: Test the complete analysis orchestrator."""

    @pytest.mark.asyncio
    async def test_full_analysis(self):
        """Test complete analysis flow."""
        from advisor.analysis.orchestrator import AnalysisOrchestrator

        orchestrator = AnalysisOrchestrator()
        result = await orchestrator.analyze(TEST_REPO_URL)

        print(f"\n{'='*60}")
        print(f"FULL ANALYSIS RESULTS: {result.repo_name}")
        print(f"{'='*60}")

        # Verify all parts are present
        assert result.repo_url == TEST_REPO_URL
        assert result.repo_name == f"{TEST_OWNER}/{TEST_REPO}"
        assert result.tech_stack is not None
        assert result.technical_summary is not None
        assert result.executive_summary is not None

        print(f"\n[TECH STACK]")
        print(f"  Languages: {result.tech_stack.languages}")
        print(f"  Frameworks: {result.tech_stack.frameworks}")
        print(f"  Tools: {result.tech_stack.tools}")

        print(f"\n[ARCHITECTURE]")
        for pattern in result.architecture_patterns:
            print(f"  - {pattern.pattern_name} ({pattern.confidence:.0%})")

        print(f"\n[RISKS] ({len(result.risks_and_gaps)} found)")
        for risk in result.risks_and_gaps[:3]:
            print(f"  - [{risk.severity}] {risk.title}")

        print(f"\n[RECOMMENDATIONS] ({len(result.recommendations)} generated)")
        for rec in result.recommendations[:3]:
            print(f"  - [{rec.priority}] {rec.title}")

        print(f"\n[TECHNICAL SUMMARY]")
        print(f"{result.technical_summary[:500]}...")

        print(f"\n[EXECUTIVE SUMMARY]")
        print(f"{result.executive_summary[:500]}...")

        print(f"\n[STATS]")
        print(f"  Model: {result.model_used}")
        print(f"  Duration: {result.analysis_duration_ms}ms")
        print(f"  Files: {result.file_count}")

        print(f"\n{'='*60}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*60}")
