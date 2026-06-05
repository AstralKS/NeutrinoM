"""GitHub client for repository intake.

Fetches repository metadata, file trees, and content samples.
Credentials are ephemeral and never stored.
"""

import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


class GitHubError(Exception):
    """Error from GitHub API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Client for GitHub API interactions.

    Handles public and private repository access.
    Access tokens are used ephemerally and never stored.
    """

    def __init__(self, access_token: str | None = None) -> None:
        """Initialize client with optional access token.

        Args:
            access_token: GitHub personal access token for private repos.
                         Used only for this request, never stored.
        """
        # Prioritize the backend .env token if available, fallback to frontend token
        self._access_token = os.getenv("GITHUB_TOKEN") or access_token

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with optional auth."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Development-Advisor",
        }
        if self._access_token:
            # Debug: print first few characters to see which token is used
            prefix = self._access_token[:10] if len(self._access_token) > 10 else "***"
            logger.info(f"Using GitHub token starting with {prefix}...")
            headers["Authorization"] = f"Bearer {self._access_token}"
        else:
            logger.info("No GitHub token provided, using unauthenticated request.")
        return headers

    async def _make_get_request(
        self, client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make GET request with automatic token fallback on 401."""
        response = await client.get(url, params=params, headers=self._get_headers())
        if response.status_code == 401 and self._access_token:
            logger.warning("GitHub token is invalid (401 Bad Credentials). Falling back to unauthenticated request.")
            self._access_token = None  # Clear invalid token
            response = await client.get(url, params=params, headers=self._get_headers())
        return response

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL.

        Args:
            url: GitHub repository URL.

        Returns:
            Tuple of (owner, repo_name).

        Raises:
            ValueError: If URL is not a valid GitHub repository URL.
        """
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            r"github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

        raise ValueError(f"Invalid GitHub repository URL: {url}")

    async def get_repo_metadata(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """Fetch repository metadata.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            Repository metadata including default branch, size, etc.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await self._make_get_request(
                client,
                f"{GITHUB_API_URL}/repos/{owner}/{repo}"
            )

            if response.status_code == 404:
                raise GitHubError(
                    f"Repository not found: {owner}/{repo}",
                    status_code=404,
                )

            if response.status_code == 403:
                # Distinguish rate limiting from actual access denial
                remaining = response.headers.get("x-ratelimit-remaining", "")
                body_text = response.text.lower()

                if remaining == "0" or "rate limit" in body_text:
                    reset_at = response.headers.get("x-ratelimit-reset", "")
                    raise GitHubError(
                        f"GitHub API rate limit exceeded for {owner}/{repo}. "
                        f"Reset at: {reset_at}. "
                        "Tip: set GITHUB_TOKEN in .env to get 5000 req/hr instead of 60.",
                        status_code=403,
                    )
                raise GitHubError(
                    f"Access denied for {owner}/{repo}. "
                    "If this is a private repo, provide an access token.",
                    status_code=403,
                )

            if response.status_code != 200:
                raise GitHubError(
                    f"GitHub API error: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

    async def get_file_tree(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Fetch repository file tree.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch to fetch (default: main).
            max_depth: Maximum directory depth to fetch.

        Returns:
            List of file/directory entries with paths and types.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get the tree recursively
            response = await self._make_get_request(
                client,
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"}
            )

            if response.status_code != 200:
                raise GitHubError(
                    f"Failed to fetch file tree: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            tree = data.get("tree", [])

            # Filter by depth
            filtered = []
            for item in tree:
                depth = item["path"].count("/")
                if depth <= max_depth:
                    filtered.append({
                        "path": item["path"],
                        "type": item["type"],  # blob or tree
                        "size": item.get("size", 0),
                    })

            return filtered

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: str = "main",
        max_size_kb: int = 100,
    ) -> str | None:
        """Fetch file content.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: File path within repository.
            branch: Branch to fetch from.
            max_size_kb: Maximum file size to fetch (skip larger files).

        Returns:
            File content as string, or None if too large or binary.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await self._make_get_request(
                client,
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch}
            )

            if response.status_code != 200:
                return None

            data = response.json()

            # Check size
            size_kb = data.get("size", 0) / 1024
            if size_kb > max_size_kb:
                logger.debug(f"Skipping large file: {path} ({size_kb:.1f}KB)")
                return None

            # Check encoding
            if data.get("encoding") != "base64":
                return None

            # Decode content
            import base64
            try:
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            except (UnicodeDecodeError, ValueError):
                logger.debug(f"Skipping binary file: {path}")
                return None
