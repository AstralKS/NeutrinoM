import pytest
import jwt
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from advisor.api.deps import get_current_user, AuthenticatedUser
from advisor.config import Settings

# Sample test data
MOCK_SETTINGS = Settings(
    supabase_url="https://example.supabase.co",
    supabase_service_role_key="service_role",
    supabase_jwt_secret="super_secret_jwt_key_must_be_long_enough",
    openrouter_api_key_1="sk-openrouter-key",
)

@pytest.fixture
def mock_settings():
    with patch("advisor.api.deps.get_settings", return_value=MOCK_SETTINGS):
        yield MOCK_SETTINGS

@pytest.fixture
def mock_jwks_client():
    with patch("advisor.api.deps._get_jwks_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

@pytest.mark.asyncio
async def test_get_current_user_hs256_success(mock_settings):
    """Test successful HS256 token verification (typical for older Supabase projects or signed manually)."""
    # Add required claims for PyJWT validation
    import time
    token = jwt.encode(
        {
            "sub": "user-123", 
            "email": "test@example.com", 
            "app_metadata": {"provider": "email"},
            "aud": "authenticated",
            "exp": time.time() + 3600
        },
        MOCK_SETTINGS.supabase_jwt_secret,
        algorithm="HS256",
    )
    auth_header = f"Bearer {token}"
    
    user = await get_current_user(auth_header)
    
    assert user.id == "user-123"
    assert user.email == "test@example.com"
    assert user.provider == "email"

@pytest.mark.asyncio
async def test_get_current_user_es256_success(mock_settings, mock_jwks_client):
    """Test successful ES256 token verification (typical for Google/GitHub OAuth login via Supabase)."""
    token = "some_valid_looking_token_string"
    auth_header = f"Bearer {token}"
    
    # Mock jwks client to return a dummy key
    key_mock = MagicMock()
    key_mock.key = "public_key"
    mock_jwks_client.get_signing_key_from_jwt.return_value = key_mock
    
    # Mock header to return ES256 alg (avoiding actual decoding)
    with patch("jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"alg": "ES256"}
        
        # Mock jwt.decode to return payload
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {
                "sub": "user-456",
                "email": "github_user@example.com",
                "app_metadata": {"provider": "github"},
                "aud": "authenticated"
            }
            
            user = await get_current_user(auth_header)
            
            assert user.id == "user-456"
            assert user.email == "github_user@example.com"
            assert user.provider == "github"

@pytest.mark.asyncio
async def test_get_current_user_google_auth(mock_settings, mock_jwks_client):
    """Test successful Google OAuth token verification."""
    token = "some_token"
    auth_header = f"Bearer {token}"
    
    key_mock = MagicMock()
    key_mock.key = "public_key"
    mock_jwks_client.get_signing_key_from_jwt.return_value = key_mock
    
    with patch("jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"alg": "ES256"}
        
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {
                "sub": "user-789",
                "email": "google_user@gmail.com",
                "app_metadata": {"provider": "google"},
                "aud": "authenticated"
            }
            
            user = await get_current_user(auth_header)
            assert user.provider == "google"

@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None)
    assert exc.value.status_code == 401
    assert "Missing or invalid authorization header" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_settings):
    # Pass a token that fails get_unverified_header real decoding (unmocked)
    with pytest.raises(HTTPException) as exc:
        await get_current_user("Bearer invalid")
    assert exc.value.status_code == 401
    assert "Invalid authentication token" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_expired_token(mock_settings):
    # Use a real token structure encoded properly so get_unverified_header passes
    token = jwt.encode({"test": "data"}, "secret", algorithm="HS256")
    auth_header = f"Bearer {token}"
    
    # Patch decode to raise ExpiredSignatureError
    # We don't patch get_unverified_header, so it uses real logic (HS256 default)
    with patch("jwt.decode", side_effect=jwt.ExpiredSignatureError):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(auth_header)
        assert exc.value.status_code == 401
        assert "Token has expired" in exc.value.detail
