# Just-In-Time (JIT) User Provisioning Guide

## Overview

This document describes the Just-In-Time (JIT) user provisioning implementation for the audio processor application. JIT provisioning automatically creates local user records when authenticated users access the API for the first time, eliminating the need for manual user management while maintaining data integrity.

## Architecture

### Components

1. **External Identity Provider (Keycloak)**: Handles authentication and issues JWT tokens
2. **JWT Token Validation**: Extracts user information from tokens
3. **Local User Database**: Stores user records for data relationships
4. **JIT Provisioning Logic**: Automatically creates users as needed

### Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │    │   Keycloak      │    │  Audio Processor│
│                 │    │   (AuthN)       │    │      API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │  1. Login Request     │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │  2. JWT Token         │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │  3. API Request + JWT │                       │
         ├───────────────────────┼──────────────────────►│
         │                       │                       │
         │                       │  4. Validate Token   │
         │                       │◄──────────────────────┤
         │                       │                       │
         │                       │  5. User Info         │
         │                       ├──────────────────────►│
         │                       │                       │
         │                       │    ┌─────────────────┐│
         │                       │    │ 6. Check Local ││
         │                       │    │    Database     ││
         │                       │    └─────────────────┘│
         │                       │                       │
         │                       │    ┌─────────────────┐│
         │                       │    │ 7. Create User  ││
         │                       │    │   (if needed)   ││
         │                       │    └─────────────────┘│
         │                       │                       │
         │  8. API Response      │                       │
         │◄──────────────────────┼───────────────────────┤
         │                       │                       │
```

## Implementation Details

### Database Schema Changes

The `User` model has been updated to support JIT provisioning:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    # Made nullable to support JIT provisioned users
    hashed_password = Column(String, nullable=True)  
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### CRUD Layer Enhancements

The `CRUDUser` class includes a new method for JIT provisioning:

```python
async def create_from_token(self, db: AsyncSession, *, token_data) -> User:
    """Create a new user from JWT token data (JIT Provisioning)."""
    db_obj = User(
        email=token_data.email,
        full_name=token_data.username,
        is_active=True,
        # hashed_password is nullable for JIT provisioned users
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
```

### API Endpoint Updates

The user profile endpoints now implement JIT provisioning:

#### GET /api/v1/users/me

```python
async def read_current_user(
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user),
):
    """
    Returns the profile of the currently authenticated user.
    If the user exists in the JWT but not in the local database,
    a local profile is created automatically (Just-In-Time Provisioning).
    """
    # Look for the user in our local database by email from the token
    db_user = await crud.user.get_by_email(db, email=current_user.email)

    if not db_user:
        # User is authenticated but doesn't have a local profile yet.
        # Create one now (JIT Provisioning).
        logger.info(f"User '{current_user.email}' not found locally. Provisioning new user.")
        db_user = await crud.user.create_from_token(db, token_data=current_user)

    return db_user
```

#### PUT /api/v1/users/me

The update endpoint also supports JIT provisioning, creating a user record before updating if one doesn't exist.

## Benefits

### 1. Seamless User Experience
- Users can immediately access the API after authentication
- No manual account creation or approval process required
- Transparent to the end user

### 2. Reduced Administrative Overhead
- No need to manually create user accounts
- Users are provisioned automatically as they access the system
- Supports scaling to large numbers of users

### 3. Data Integrity
- Local user records maintain relationships with jobs and other data
- Foreign key constraints remain intact
- Audit trail of user creation is preserved

### 4. Flexible Authentication
- Supports multiple authentication providers
- Works with both password-based and token-based authentication
- Easy to integrate with existing identity infrastructure

### 5. Security
- User data comes from trusted identity provider
- No local password storage required for external users
- Role-based access control is preserved

## Security Considerations

### 1. Token Validation
- JWT tokens must be properly validated
- Token expiration must be enforced
- Signature verification is required

### 2. User Data Validation
- Email addresses must be validated and unique
- User roles are derived from trusted token claims
- Input sanitization prevents injection attacks

### 3. Access Control
- Role-based permissions are still enforced
- JIT provisioning doesn't bypass authorization
- Audit logging tracks user creation events

## Monitoring and Observability

### Key Metrics to Track

1. **JIT Provisioning Rate**: Number of new users created per time period
2. **Authentication Success Rate**: Percentage of successful token validations
3. **Database Performance**: Impact of user creation on database performance
4. **Error Rates**: Failed provisioning attempts and reasons

### Logging

The implementation includes comprehensive logging:

```python
logger.info(f"User '{current_user.email}' not found locally. Provisioning new user.")
```

### Health Checks

Monitor these aspects:
- Database connectivity for user operations
- Identity provider availability
- Token validation service health

## Deployment Considerations

### Database Migrations

Run the migration to make `hashed_password` nullable:

```bash
alembic upgrade head
```

### Environment Configuration

Ensure these settings are configured:
- Identity provider endpoints
- JWT validation keys
- Database connection strings
- Logging levels

### Testing

Use the provided test suites:
- Unit tests: `tests/unit/test_user_crud.py`
- Integration tests: `tests/integration/test_user_profile_endpoints.py`
- Demo script: `scripts/demo_jit_provisioning.py`

## Troubleshooting

### Common Issues

#### 1. User Creation Fails
- **Symptoms**: 500 errors on first user access
- **Causes**: Database connectivity, unique constraint violations
- **Solutions**: Check database health, verify email uniqueness

#### 2. Token Validation Errors
- **Symptoms**: 401/403 errors for valid users
- **Causes**: JWT configuration, key validation issues
- **Solutions**: Verify identity provider configuration

#### 3. Performance Issues
- **Symptoms**: Slow response times on user endpoints
- **Causes**: Database performance, missing indexes
- **Solutions**: Add database indexes, optimize queries

### Debug Steps

1. **Check Authentication**:
   ```bash
   # Verify JWT token is valid
   curl -H "Authorization: Bearer <token>" /api/v1/users/me
   ```

2. **Database Inspection**:
   ```sql
   -- Check if user exists
   SELECT * FROM users WHERE email = 'user@example.com';
   
   -- Check recent user creations
   SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
   ```

3. **Log Analysis**:
   ```bash
   # Search for JIT provisioning logs
   grep "Provisioning new user" /var/log/audio-processor.log
   ```

## Migration from Manual User Management

If you're migrating from a system with manual user management:

### 1. Data Assessment
- Identify existing users
- Map external identities to local accounts
- Plan for orphaned records

### 2. Migration Strategy
- Enable JIT provisioning alongside existing system
- Gradually migrate users to token-based authentication
- Decommission manual processes

### 3. Rollback Plan
- Keep migration reversible
- Maintain backup of original user data
- Document rollback procedures

## Future Enhancements

### Possible Improvements

1. **User Profile Enrichment**: Fetch additional user data from identity provider
2. **Bulk Provisioning**: API endpoints for bulk user operations
3. **User Lifecycle Management**: Handle user deactivation and cleanup
4. **Multi-Tenant Support**: Extend JIT provisioning for tenant isolation
5. **Advanced Role Mapping**: Complex role mapping from token claims

### API Extensions

Consider these additional endpoints:
- `GET /api/v1/users/provision-status` - Check provisioning status
- `POST /api/v1/users/bulk-provision` - Bulk user provisioning
- `DELETE /api/v1/users/me` - Self-service account deletion

## Conclusion

JIT user provisioning provides a robust, scalable solution for user management in microservice architectures. It balances automation with data integrity, reducing administrative overhead while maintaining security and auditability.

The implementation follows best practices for authentication, database design, and error handling, making it suitable for production environments with high user volumes and strict security requirements.
