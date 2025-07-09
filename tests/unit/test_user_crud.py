"""
Unit tests for User CRUD operations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.db.crud.user import CRUDUser
from app.schemas.database import User


class TestUserCRUD:
    """Test suite for User CRUD operations."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock(spec=AsyncSession)

    @pytest.fixture
    def user_crud(self):
        """User CRUD instance."""
        return CRUDUser(User)

    @pytest.fixture
    def token_user_data(self):
        """Mock user data from JWT token."""
        return CurrentUser(
            user_id="auth0|507f1f77bcf86cd799439011",
            username="John Doe",
            email="john.doe@example.com",
            roles=["user"],
            claims={},
        )

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, user_crud, db_session):
        """Test getting a user by email when user exists."""

        # Mock user object
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.hashed_password = None

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db_session.execute = AsyncMock(return_value=mock_result)

        result = await user_crud.get_by_email(db_session, email="test@example.com")

        assert result == mock_user
        db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_crud, db_session):
        """Test getting a user by email when user doesn't exist."""

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute = AsyncMock(return_value=mock_result)

        result = await user_crud.get_by_email(
            db_session, email="nonexistent@example.com"
        )

        assert result is None
        db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_from_token_success(
        self, user_crud, db_session, token_user_data
    ):
        """Test creating a user from JWT token data."""

        # Mock database operations
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        # Mock the created user object
        mock_user = Mock()
        mock_user.email = token_user_data.email
        mock_user.full_name = token_user_data.username
        mock_user.is_active = True
        mock_user.hashed_password = None

        # Patch User constructor to return our mock
        with patch.object(User, "__new__", return_value=mock_user):
            result = await user_crud.create_from_token(
                db_session, token_data=token_user_data
            )

        # Verify the user was created with correct data
        assert result.email == token_user_data.email
        assert result.full_name == token_user_data.username
        assert result.is_active is True
        assert result.hashed_password is None

        # Verify database operations were called
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_from_token_with_minimal_data(self, user_crud, db_session):
        """Test creating a user from JWT token with minimal data."""

        minimal_token_data = CurrentUser(
            user_id="auth0|minimal",
            username="Minimal User",
            email="minimal@example.com",
            roles=[],
            claims={},
        )

        # Mock database operations
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        # Mock the created user object
        mock_user = Mock()
        mock_user.email = minimal_token_data.email
        mock_user.full_name = minimal_token_data.username
        mock_user.is_active = True
        mock_user.hashed_password = None

        # Patch User constructor to return our mock
        with patch.object(User, "__new__", return_value=mock_user):
            result = await user_crud.create_from_token(
                db_session, token_data=minimal_token_data
            )

        # Verify the user was created with minimal data
        assert result.email == minimal_token_data.email
        assert result.full_name == minimal_token_data.username
        assert result.is_active is True

        # Verify database operations were called
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_crud, db_session):
        """Test updating an existing user."""

        # Mock existing user
        existing_user = Mock()
        existing_user.id = 1
        existing_user.email = "existing@example.com"
        existing_user.full_name = "Old Name"
        existing_user.is_active = True
        existing_user.hashed_password = None

        # Mock update data
        update_data = {"full_name": "New Name", "is_active": False}

        # Mock database operations
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        result = await user_crud.update(
            db_session, db_obj=existing_user, obj_in=update_data
        )

        # Verify the user data was updated
        assert existing_user.full_name == "New Name"
        assert existing_user.is_active is False
        assert existing_user.email == "existing@example.com"  # Should remain unchanged

        # Verify database operations were called
        db_session.add.assert_called_once_with(existing_user)
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(existing_user)

    @pytest.mark.asyncio
    async def test_update_user_with_schema_object(self, user_crud, db_session):
        """Test updating a user with a Pydantic schema object."""

        from app.schemas.api import UserUpdateRequest

        # Mock existing user
        existing_user = Mock()
        existing_user.id = 1
        existing_user.email = "existing@example.com"
        existing_user.full_name = "Old Name"
        existing_user.is_active = True
        existing_user.hashed_password = None

        # Create update schema object
        update_schema = UserUpdateRequest(
            full_name="Schema Updated Name", is_active=False
        )

        # Mock database operations
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        result = await user_crud.update(
            db_session, db_obj=existing_user, obj_in=update_schema
        )

        # Verify the user data was updated
        assert existing_user.full_name == "Schema Updated Name"
        assert existing_user.is_active is False

        # Verify database operations were called
        db_session.add.assert_called_once_with(existing_user)
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(existing_user)

    @pytest.mark.asyncio
    async def test_create_regular_user_with_password(self, user_crud, db_session):
        """Test creating a regular user with password (existing functionality)."""

        from app.schemas.api import UserCreateRequest

        user_request = UserCreateRequest(
            email="regular@example.com",
            password="securepassword123",
            full_name="Regular User",
        )

        hashed_password = "hashed_secure_password"

        # Mock database operations
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        # Mock the created user object
        mock_user = Mock()
        mock_user.email = user_request.email
        mock_user.full_name = user_request.full_name
        mock_user.is_active = True
        mock_user.hashed_password = hashed_password

        # Patch User constructor to return our mock
        with patch.object(User, "__new__", return_value=mock_user):
            result = await user_crud.create(
                db_session, obj_in=user_request, hashed_password=hashed_password
            )

        # Verify the user was created with correct data
        assert result.email == user_request.email
        assert result.full_name == user_request.full_name
        assert result.hashed_password == hashed_password
        assert result.is_active is True

        # Verify database operations were called
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
