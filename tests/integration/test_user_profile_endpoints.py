"""
Integration tests for user profile endpoints with JIT provisioning.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch

from app.main import app
from app.api.dependencies import get_current_user, CurrentUser
from app.db.session import get_async_session
from app.db import crud
from app.schemas.database import User


class TestUserProfileEndpoints:
    """Test suite for user profile endpoints."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user from JWT token."""
        return CurrentUser(
            user_id="auth0|507f1f77bcf86cd799439011",
            username="John Doe",
            email="john.doe@example.com",
            roles=["user"],
            claims={}
        )

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user from JWT token."""
        return CurrentUser(
            user_id="auth0|507f1f77bcf86cd799439012",
            username="Jane Admin",
            email="jane.admin@example.com",
            roles=["admin"],
            claims={}
        )

    @pytest.fixture
    async def db_session(self):
        """Database session fixture."""
        # In real implementation, this would use a test database
        return Mock(spec=AsyncSession)

    async def test_get_current_user_jit_provisioning(self, client, mock_current_user, db_session):
        """Test that GET /me creates a user record if it doesn't exist (JIT provisioning)."""
        
        # Mock the database session and CRUD operations
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.api.v1.endpoints.users.get_current_user', return_value=mock_current_user), \
             patch('app.db.crud.user.get_by_email', return_value=None), \
             patch('app.db.crud.user.create_from_token') as mock_create:
            
            # Mock the created user
            mock_user = User(
                id=1,
                email=mock_current_user.email,
                full_name=mock_current_user.username,
                is_active=True,
                hashed_password=None
            )
            mock_create.return_value = mock_user
            
            response = client.get("/api/v1/users/me")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_current_user.email
            assert data["full_name"] == mock_current_user.username
            assert data["is_active"] is True
            
            # Verify that create_from_token was called
            mock_create.assert_called_once()

    async def test_get_current_user_existing_user(self, client, mock_current_user, db_session):
        """Test that GET /me returns existing user record without creating a new one."""
        
        # Mock existing user in database
        existing_user = User(
            id=1,
            email=mock_current_user.email,
            full_name="Existing Full Name",
            is_active=True,
            hashed_password=None
        )
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.api.v1.endpoints.users.get_current_user', return_value=mock_current_user), \
             patch('app.db.crud.user.get_by_email', return_value=existing_user), \
             patch('app.db.crud.user.create_from_token') as mock_create:
            
            response = client.get("/api/v1/users/me")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_current_user.email
            assert data["full_name"] == "Existing Full Name"  # Should use existing data
            assert data["is_active"] is True
            
            # Verify that create_from_token was NOT called
            mock_create.assert_not_called()

    async def test_get_current_user_unauthenticated(self, client):
        """Test that GET /me returns 403 for unauthenticated requests."""
        
        with patch('app.api.v1.endpoints.users.get_current_user', side_effect=Exception("Unauthorized")):
            response = client.get("/api/v1/users/me")
            assert response.status_code in [401, 403]

    async def test_update_current_user_jit_provisioning(self, client, mock_current_user, db_session):
        """Test that PUT /me creates a user record if it doesn't exist before updating."""
        
        update_data = {
            "full_name": "Updated Name",
            "is_active": True
        }
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.api.v1.endpoints.users.get_current_user', return_value=mock_current_user), \
             patch('app.db.crud.user.get_by_email', return_value=None), \
             patch('app.db.crud.user.create_from_token') as mock_create, \
             patch('app.db.crud.user.update') as mock_update:
            
            # Mock the created and updated user
            mock_user = User(
                id=1,
                email=mock_current_user.email,
                full_name=mock_current_user.username,
                is_active=True,
                hashed_password=None
            )
            mock_create.return_value = mock_user
            
            updated_user = User(
                id=1,
                email=mock_current_user.email,
                full_name="Updated Name",
                is_active=True,
                hashed_password=None
            )
            mock_update.return_value = updated_user
            
            response = client.put("/api/v1/users/me", json=update_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Name"
            
            # Verify that both create_from_token and update were called
            mock_create.assert_called_once()
            mock_update.assert_called_once()

    async def test_update_current_user_existing_user(self, client, mock_current_user, db_session):
        """Test that PUT /me updates existing user without creating a new one."""
        
        update_data = {
            "full_name": "Updated Name",
            "is_active": False
        }
        
        # Mock existing user in database
        existing_user = User(
            id=1,
            email=mock_current_user.email,
            full_name="Original Name",
            is_active=True,
            hashed_password=None
        )
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.api.v1.endpoints.users.get_current_user', return_value=mock_current_user), \
             patch('app.db.crud.user.get_by_email', return_value=existing_user), \
             patch('app.db.crud.user.create_from_token') as mock_create, \
             patch('app.db.crud.user.update') as mock_update:
            
            updated_user = User(
                id=1,
                email=mock_current_user.email,
                full_name="Updated Name",
                is_active=False,
                hashed_password=None
            )
            mock_update.return_value = updated_user
            
            response = client.put("/api/v1/users/me", json=update_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Name"
            assert data["is_active"] is False
            
            # Verify that create_from_token was NOT called, but update was
            mock_create.assert_not_called()
            mock_update.assert_called_once()

    async def test_list_users_admin_only(self, client, mock_admin_user, db_session):
        """Test that GET /users requires admin role."""
        
        mock_users = [
            User(id=1, email="user1@example.com", full_name="User 1", is_active=True),
            User(id=2, email="user2@example.com", full_name="User 2", is_active=True),
        ]
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.api.v1.endpoints.users.require_roles') as mock_require_roles, \
             patch('app.db.crud.user.get_multi', return_value=mock_users):
            
            # Mock the admin role requirement
            mock_require_roles.return_value = lambda: None
            
            response = client.get("/api/v1/users/")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["email"] == "user1@example.com"
            assert data[1]["email"] == "user2@example.com"

    async def test_list_users_unauthorized(self, client, mock_current_user):
        """Test that GET /users returns 403 for non-admin users."""
        
        with patch('app.api.v1.endpoints.users.require_roles', side_effect=Exception("Forbidden")):
            response = client.get("/api/v1/users/")
            assert response.status_code in [401, 403]

    async def test_crud_fallback_behavior(self, client, mock_current_user):
        """Test fallback behavior when CRUD module is not available."""
        
        with patch('app.api.v1.endpoints.users.get_current_user', return_value=mock_current_user), \
             patch('app.api.v1.endpoints.users.crud', side_effect=ImportError("CRUD not available")):
            
            response = client.get("/api/v1/users/me")
            
            # Should still return 200 with mock data
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_current_user.email
            assert data["full_name"] == mock_current_user.username

    async def test_create_user_public_endpoint(self, client, db_session):
        """Test the public user creation endpoint."""
        
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.db.crud.user.get_by_email', return_value=None), \
             patch('app.db.crud.user.create') as mock_create, \
             patch('app.core.security.get_password_hash', return_value="hashed_password"):
            
            mock_user = User(
                id=1,
                email=user_data["email"],
                full_name=user_data["full_name"],
                is_active=True,
                hashed_password="hashed_password"
            )
            mock_create.return_value = mock_user
            
            response = client.post("/api/v1/users/", json=user_data)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["full_name"] == user_data["full_name"]
            assert data["is_active"] is True
            
            # Verify that create was called
            mock_create.assert_called_once()

    async def test_create_user_duplicate_email(self, client, db_session):
        """Test that creating a user with existing email returns 400."""
        
        user_data = {
            "email": "existing@example.com",
            "password": "securepassword123",
            "full_name": "Duplicate User"
        }
        
        # Mock existing user
        existing_user = User(
            id=1,
            email=user_data["email"],
            full_name="Existing User",
            is_active=True,
            hashed_password="existing_hash"
        )
        
        with patch('app.api.v1.endpoints.users.get_async_session', return_value=db_session), \
             patch('app.db.crud.user.get_by_email', return_value=existing_user):
            
            response = client.post("/api/v1/users/", json=user_data)
            
            # Should return 400 for duplicate email
            assert response.status_code == 400
            data = response.json()
            assert "already exists" in data["detail"].lower()
