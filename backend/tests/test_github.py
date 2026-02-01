"""Tests for GitHub client."""

import pytest

from advisor.github.client import GitHubClient


class TestParseRepoUrl:
    """Tests for repository URL parsing."""

    def test_parse_standard_url(self):
        """Test parsing standard GitHub URL."""
        owner, repo = GitHubClient.parse_repo_url(
            "https://github.com/owner/repo"
        )
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_url_with_git_suffix(self):
        """Test parsing URL with .git suffix."""
        owner, repo = GitHubClient.parse_repo_url(
            "https://github.com/owner/repo.git"
        )
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        owner, repo = GitHubClient.parse_repo_url(
            "https://github.com/owner/repo/"
        )
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_url_raises(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            GitHubClient.parse_repo_url("not-a-github-url")

    def test_parse_empty_url_raises(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError):
            GitHubClient.parse_repo_url("")
