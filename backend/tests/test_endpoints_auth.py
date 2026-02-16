import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from advisor.api.endpoints import app, get_current_user, AuthenticatedUser

client = TestClient(app)

# Mock authenticated user
MOCKED_USER = AuthenticatedUser(id="user-123", email="test@example.com", provider="github")

@pytest.fixture
def mock_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCKED_USER
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_github_repos_with_header(mock_auth):
    """Test accessing GitHub repos with X-GitHub-Token header."""
    
    # Mock httpx response from GitHub
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"id": 1, "name": "repo1", "full_name": "owner/repo1", "html_url": "http://github.com/owner/repo1", "private": True}
        ]
        mock_get.return_value = mock_resp
        
        response = client.get(
            "/user/github/repos",
            headers={"X-GitHub-Token": "gh_token_from_header"}
        )
        
        assert response.status_code == 200
        assert len(response.json()["repos"]) == 1
        assert response.json()["repos"][0]["name"] == "repo1"
        
        # Verify it used the token from header
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer gh_token_from_header"

@pytest.mark.asyncio
async def test_github_repos_missing_token(mock_auth):
    """Test accessing GitHub repos without any token (should fail 400)."""
    
    # Mock failed lookup from Supabase (fallback)
    with patch("httpx.AsyncClient.get") as mock_get:
        # Mocking the call to Supabase /user endpoint
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"identities": []} # No github identity
        mock_get.return_value = mock_resp
        
        response = client.get("/user/github/repos")
        
        assert response.status_code == 400
        assert "GitHub provider token not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_github_repos_api_error(mock_auth):
    """Test GitHub API returning error (e.g. 401)."""
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Bad credentials"
        mock_get.return_value = mock_resp
        
        response = client.get(
            "/user/github/repos",
            headers={"X-GitHub-Token": "invalid_token"}
        )
        
        assert response.status_code == 502
        assert "GitHub token expired or invalid" in response.json()["detail"]
