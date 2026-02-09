"""GitHub client for repository intake.

Fetches repository metadata, file trees, and content samples.
Credentials are ephemeral and never stored.
"""

import asyncio
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    coro_func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
):
    """Retry an async function with exponential backoff.
    
    Args:
        coro_func: A callable that returns a coroutine.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
    
    Returns:
        The result of the successful coroutine call.
    
    Raises:
        The last exception if all retries fail.
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.TimeoutException) as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed: {e}")
    raise last_exception

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
        self._access_token = access_token or os.getenv("GITHUB_TOKEN")

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with optional auth."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Development-Advisor",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

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
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}",
                headers=self._get_headers(),
            )

            if response.status_code == 404:
                raise GitHubError(
                    f"Repository not found: {owner}/{repo}",
                    status_code=404,
                )

            if response.status_code == 403:
                raise GitHubError(
                    "Access denied. Private repo requires access token.",
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
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Get the tree recursively with retry logic
            async def make_request():
                return await client.get(
                    f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{branch}",
                    params={"recursive": "1"},
                    headers=self._get_headers(),
                )

            response = await retry_with_backoff(make_request)

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
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
                headers=self._get_headers(),
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
