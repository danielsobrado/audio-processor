"""
Authentication dependencies for Keycloak OAuth2 JWT token validation.
Compatible with Omi's authentication patterns.
"""

import logging
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional

import jwt
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt.algorithms as algorithms
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from app.config.settings import get_settings
from app.services.cache import CacheService
from app.core.job_queue import JobQueue

logger = logging.getLogger(__name__)
settings = get_settings()

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

def get_cache_service() -> CacheService:
    """
    Dependency to get a CacheService instance.
    """
    return CacheService()

def get_job_queue() -> JobQueue:
    """
    Dependency to get a JobQueue instance.
    """
    return JobQueue()

# Cache for JWKS keys
_jwks_cache: Dict[str, Any] = {}
_jwks_cache_expiry: Optional[datetime] = None


class AuthenticationError(HTTPException):
    """Authentication-specific HTTP exception."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Authorization-specific HTTP exception."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_jwks_keys() -> Dict[str, Any]:
    """
    Fetch and cache JWKS keys from Keycloak.
    TODO: Implement proper caching with TTL.
    """
    global _jwks_cache, _jwks_cache_expiry

    # Check cache validity (5 minutes TTL)
    now = datetime.now(timezone.utc)
    if _jwks_cache and _jwks_cache_expiry and now < _jwks_cache_expiry:
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.auth.jwks_url,
                timeout=10.0,
            )
            response.raise_for_status()

            jwks_data = response.json()

            # Convert to key dictionary for easier lookup
            keys = {}
            for key in jwks_data.get("keys", []):
                if key.get("kid"):
                    keys[key["kid"]] = key

            # Update cache
            _jwks_cache = keys
            _jwks_cache_expiry = now.replace(minute=now.minute + 5)

            logger.debug(f"JWKS keys cached: {len(keys)} keys")
            return keys

    except httpx.RequestError as e:
        logger.error(f"Failed to fetch JWKS keys: {e}")
        raise AuthenticationError("Unable to verify token signature")
    except Exception as e:
        logger.error(f"Unexpected error fetching JWKS: {e}")
        raise AuthenticationError("Authentication service unavailable")


def get_public_key_from_jwks(token_header: dict, jwks_keys: dict) -> Any:
    """Extract public key from JWKS for token verification."""
    kid = token_header.get("kid")
    if not kid:
        raise AuthenticationError("Token missing key ID")

    key_data = jwks_keys.get(kid)
    if not key_data:
        raise AuthenticationError("Unknown key ID")

    try:
        public_key = algorithms.RSAAlgorithm.from_jwk(key_data)
        return public_key
    except Exception as e:
        logger.error(f"Failed to construct public key: {e}")
        raise AuthenticationError("Invalid key format")


async def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token against Keycloak and return claims.
    """
    try:
        # Decode header without verification to get key ID
        unverified_header = jwt.get_unverified_header(token)

        # Get JWKS keys
        jwks_keys = await get_jwks_keys()

        # Get public key for verification
        public_key = get_public_key_from_jwks(unverified_header, jwks_keys)

        # Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.auth.algorithm],
            issuer=settings.auth.issuer_url if settings.auth.verify_signature else None,
            audience=settings.auth.client_id if settings.auth.verify_audience else None,
            options={
                "verify_signature": settings.auth.verify_signature,
                "verify_aud": settings.auth.verify_audience,
                "verify_iss": settings.auth.verify_signature,
                "verify_exp": True,
            }
        )

        return payload

    except ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except DecodeError:
        raise AuthenticationError("Invalid token format")
    except InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AuthenticationError("Token verification failed")


class CurrentUser:
    """User information extracted from JWT token."""

    def __init__(self, user_id: str, username: str, email: str, roles: list, claims: dict):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles = roles
        self.claims = claims

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    Extract and validate current user from JWT token.
    Compatible with Omi's user authentication pattern.
    """
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    token = credentials.credentials
    if not token:
        raise AuthenticationError("Empty authentication token")
    
    # Verify token and get claims
    claims = await verify_jwt_token(token)
    
    # Extract user information
    user_id = claims.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user ID")
    
    username = claims.get("preferred_username", "")
    email = claims.get("email", "")
    
    # Extract roles from token
    roles = []
    
    # Check realm roles
    realm_access = claims.get("realm_access", {})
    if isinstance(realm_access, dict):
        roles.extend(realm_access.get("roles", []))
    
    # Check client roles
    resource_access = claims.get("resource_access", {})
    if isinstance(resource_access, dict):
        client_access = resource_access.get(settings.auth.client_id, {})
        if isinstance(client_access, dict):
            roles.extend(client_access.get("roles", []))
    
    logger.debug(f"User authenticated: {user_id} ({username}) with roles: {roles}")
    
    return CurrentUser(
        user_id=user_id,
        username=username,
        email=email,
        roles=roles,
        claims=claims,
    )


async def get_current_user_id(current_user: CurrentUser = Depends(get_current_user)) -> str:
    """
    Get current user ID (compatible with Omi's get_current_user_uid pattern).
    """
    return current_user.user_id


def require_roles(required_roles: List[str]):
    """
    Dependency factory for role-based authorization.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: CurrentUser = Depends(require_roles(["admin"]))):
            pass
    """
    async def check_roles(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_any_role(required_roles):
            logger.warning(
                f"Access denied for user {current_user.user_id}: "
                f"requires {required_roles}, has {current_user.roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    
    return check_roles


def require_scope(required_scope: str):
    """
    Dependency factory for scope-based authorization.
    
    Usage:
        @router.get("/transcribe")
        async def transcribe(user: CurrentUser = Depends(require_scope("audio:transcribe"))):
            pass
    """
    async def check_scope(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        scopes = current_user.claims.get("scope", "").split()
        if required_scope not in scopes:
            logger.warning(
                f"Insufficient scope for user {current_user.user_id}: "
                f"requires {required_scope}, has {scopes}"
            )
            raise AuthorizationError(f"Access denied. Required scope: {required_scope}")
        return current_user
    
    return check_scope


# Optional authentication for public endpoints
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Optional authentication - returns None if no valid token provided.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except AuthenticationError:
        # Log the attempt but don't raise exception
        logger.debug("Optional authentication failed")
        return None


# Rate limiting dependency
class RateLimiter:
    """Redis-based distributed rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis_client = None
        self._fallback_requests = {}  # Fallback for when Redis is unavailable
    
    async def _get_redis_client(self):
        """Get Redis client, creating it if needed."""
        if self._redis_client is None:
            try:
                import redis.asyncio as redis
                from app.config.settings import get_settings
                settings = get_settings()
                
                # Use Redis URL from settings or fallback to localhost
                redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
                self._redis_client = redis.from_url(redis_url)
                
                # Test connection
                await self._redis_client.ping()
                
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to in-memory: {e}")
                self._redis_client = False  # Mark as failed
        
        return self._redis_client if self._redis_client is not False else None
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit using Redis or in-memory fallback."""
        redis_client = await self._get_redis_client()
        
        if redis_client:
            return await self._check_rate_limit_redis(user_id, redis_client)
        else:
            return await self._check_rate_limit_memory(user_id)
    
    async def _check_rate_limit_redis(self, user_id: str, redis_client) -> bool:
        """Redis-based rate limiting with sliding window."""
        try:
            key = f"rate_limit:{user_id}"
            now = datetime.now(timezone.utc).timestamp()
            window_start = now - self.window_seconds
            
            # Remove old entries and count current requests
            await redis_client.zremrangebyscore(key, 0, window_start)
            current_requests = await redis_client.zcard(key)
            
            if current_requests >= self.max_requests:
                return False
            
            # Add current request
            await redis_client.zadd(key, {str(now): now})
            await redis_client.expire(key, self.window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis rate limiting failed: {e}")
            # Fallback to in-memory
            return await self._check_rate_limit_memory(user_id)
    
    async def _check_rate_limit_memory(self, user_id: str) -> bool:
        """In-memory rate limiting fallback (not distributed)."""
        now = datetime.now(timezone.utc)
        window_start = now.timestamp() - self.window_seconds
        
        # Clean old entries
        user_requests = self._fallback_requests.get(user_id, [])
        user_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        # Check limit
        if len(user_requests) >= self.max_requests:
            return False
        
        # Add current request
        user_requests.append(now.timestamp())
        self._fallback_requests[user_id] = user_requests
        
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window,
)


async def check_rate_limit(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Rate limiting dependency."""
    if not await rate_limiter.check_rate_limit(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
    return current_user
