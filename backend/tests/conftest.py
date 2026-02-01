"""Shared test fixtures and mocks."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.supabase_url = "https://test.supabase.co"
    settings.supabase_service_role_key = "test-key"
    settings.openrouter_api_keys = ["test-key-1", "test-key-2"]
    settings.openrouter_base_url = "https://openrouter.ai/api/v1"
    settings.app_name = "Test Advisor"
    settings.debug = True
    return settings


@pytest.fixture
def sample_file_tree() -> list[dict[str, Any]]:
    """Sample GitHub file tree for testing."""
    return [
        {"path": "README.md", "type": "blob", "size": 1024},
        {"path": "package.json", "type": "blob", "size": 500},
        {"path": "src", "type": "tree", "size": 0},
        {"path": "src/index.ts", "type": "blob", "size": 2048},
        {"path": "src/components", "type": "tree", "size": 0},
        {"path": "src/components/App.tsx", "type": "blob", "size": 1500},
        {"path": "src/utils/helpers.ts", "type": "blob", "size": 800},
        {"path": "tests", "type": "tree", "size": 0},
        {"path": "tests/app.test.ts", "type": "blob", "size": 600},
        {"path": ".github/workflows/ci.yml", "type": "blob", "size": 300},
        {"path": "Dockerfile", "type": "blob", "size": 200},
    ]


@pytest.fixture
def sample_file_contents() -> dict[str, str]:
    """Sample file contents for testing."""
    return {
        "package.json": '''{
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.2.0",
                "next": "^14.0.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "jest": "^29.0.0"
            }
        }''',
        "README.md": "# Test Project\n\nA sample project for testing.",
        "src/index.ts": "export const main = () => console.log('Hello');",
    }


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    client = MagicMock()
    client.get_repo_metadata = AsyncMock(
        return_value={
            "name": "test-repo",
            "owner": {"login": "test-owner"},
            "default_branch": "main",
            "size": 1024,
        }
    )
    client.get_file_tree = AsyncMock(return_value=[])
    client.get_file_content = AsyncMock(return_value="# Content")
    return client


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.complete = AsyncMock(
        return_value={
            "content": "Sample analysis summary.",
            "model": "test-model",
            "usage": {"total_tokens": 100},
        }
    )
    client.total_tokens_used = 100
    return client
