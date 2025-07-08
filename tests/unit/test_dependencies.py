"""
Unit tests for API dependencies, including authentication and caching logic.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

# Import the function and globals we need to test/manipulate
from app.api.dependencies import get_jwks_keys
from app.config.settings import Settings


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Fixture to reset the JWKS cache before each test."""
    import app.api.dependencies as deps
    deps._jwks_cache = {}
    deps._jwks_cache_expiry = None
    yield
    deps._jwks_cache = {}
    deps._jwks_cache_expiry = None


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_uses_default_ttl(mock_http_client):
    """Verify that the default cache TTL of 300 seconds is used."""
    # ARRANGE
    # Mock the settings to ensure we're using defaults
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300  # Default value
    
    with patch("app.api.dependencies.settings", mock_settings):
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": [{"kid": "key1", "kty": "RSA"}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # Mock datetime.now to control time
        start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch("app.api.dependencies.datetime") as mock_datetime:
            mock_datetime.now.return_value = start_time
            mock_datetime.timedelta = timedelta  # Ensure we use the real timedelta

            # ACT
            await get_jwks_keys()

            # ASSERT
            import app.api.dependencies as deps
            expected_expiry = start_time + timedelta(seconds=300)
            assert deps._jwks_cache_expiry == expected_expiry
            mock_context_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_uses_custom_ttl(mock_http_client):
    """Verify that a custom cache TTL from settings is correctly applied."""
    # ARRANGE
    # Mock settings with a custom TTL
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 60  # Custom 1-minute TTL
    
    with patch("app.api.dependencies.settings", mock_settings):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": [{"kid": "key1", "kty": "RSA"}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch("app.api.dependencies.datetime") as mock_datetime:
            mock_datetime.now.return_value = start_time
            mock_datetime.timedelta = timedelta

            # ACT
            await get_jwks_keys()

            # ASSERT
            import app.api.dependencies as deps
            expected_expiry = start_time + timedelta(seconds=60)
            assert deps._jwks_cache_expiry == expected_expiry
            mock_context_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_cache_hit(mock_http_client):
    """Verify that a valid cache prevents an HTTP call."""
    # ARRANGE
    import app.api.dependencies as deps
    deps._jwks_cache = {"key1": {"kid": "key1", "kty": "RSA"}}
    deps._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    # ACT
    keys = await get_jwks_keys()

    # ASSERT
    assert keys == {"key1": {"kid": "key1", "kty": "RSA"}}
    mock_http_client.assert_not_called()  # The HTTP client should not have been used


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_cache_miss_due_to_expiry(mock_http_client):
    """Verify that an expired cache triggers a new HTTP call."""
    # ARRANGE
    import app.api.dependencies as deps
    deps._jwks_cache = {"key1": {"kid": "key1", "kty": "RSA"}}
    deps._jwks_cache_expiry = datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired 1 minute ago

    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300
    
    with patch("app.api.dependencies.settings", mock_settings):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": [{"kid": "new_key", "kty": "RSA"}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # ACT
        keys = await get_jwks_keys()

        # ASSERT
        assert keys == {"new_key": {"kid": "new_key", "kty": "RSA"}}  # Should contain the new data
        mock_context_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_cache_miss_no_existing_cache(mock_http_client):
    """Verify that no existing cache triggers an HTTP call."""
    # ARRANGE
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300
    
    with patch("app.api.dependencies.settings", mock_settings):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": [{"kid": "fresh_key", "kty": "RSA"}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # ACT
        keys = await get_jwks_keys()

        # ASSERT
        assert keys == {"fresh_key": {"kid": "fresh_key", "kty": "RSA"}}
        mock_context_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_handles_multiple_keys(mock_http_client):
    """Verify that multiple keys are properly processed and cached."""
    # ARRANGE
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300
    
    with patch("app.api.dependencies.settings", mock_settings):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "keys": [
                {"kid": "key1", "kty": "RSA", "use": "sig"},
                {"kid": "key2", "kty": "RSA", "use": "enc"},
                {"kty": "RSA", "use": "sig"}  # Key without kid should be ignored
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # ACT
        keys = await get_jwks_keys()

        # ASSERT
        expected_keys = {
            "key1": {"kid": "key1", "kty": "RSA", "use": "sig"},
            "key2": {"kid": "key2", "kty": "RSA", "use": "enc"}
        }
        assert keys == expected_keys
        assert len(keys) == 2  # Only keys with kid should be included


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_handles_empty_keys_response(mock_http_client):
    """Verify that an empty keys response is handled gracefully."""
    # ARRANGE
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300
    
    with patch("app.api.dependencies.settings", mock_settings):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": []}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # ACT
        keys = await get_jwks_keys()

        # ASSERT
        assert keys == {}
        mock_context_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.dependencies.httpx.AsyncClient")
async def test_get_jwks_preserves_cache_structure(mock_http_client):
    """Verify that the cache structure preserves all key data."""
    # ARRANGE
    mock_settings = MagicMock()
    mock_settings.auth.jwks_url = "http://localhost:8080/auth/realms/test/protocol/openid-connect/certs"
    mock_settings.auth.jwks_cache_ttl_seconds = 300
    
    with patch("app.api.dependencies.settings", mock_settings):
        original_key_data = {
            "kid": "test_key_id",
            "kty": "RSA",
            "use": "sig",
            "n": "sample_modulus",
            "e": "AQAB",
            "alg": "RS256"
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {"keys": [original_key_data]}
        mock_response.raise_for_status = MagicMock()
        
        mock_context_manager = AsyncMock()
        mock_context_manager.get.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_context_manager

        # ACT
        keys = await get_jwks_keys()

        # ASSERT
        assert keys["test_key_id"] == original_key_data
        assert all(key in keys["test_key_id"] for key in ["kid", "kty", "use", "n", "e", "alg"])
