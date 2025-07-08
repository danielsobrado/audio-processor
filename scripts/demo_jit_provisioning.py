"""
Demo script showing JIT (Just-In-Time) user provisioning in action.

This script demonstrates how the user profile endpoint automatically creates
local user records when authenticated users access the API for the first time.
"""

import asyncio
import logging
from typing import Optional

from app.api.dependencies import CurrentUser
from app.db.session import AsyncSessionLocal
from app.db import crud
from app.schemas.database import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simulate_jit_provisioning():
    """
    Simulate the JIT provisioning process that happens in the user profile endpoint.
    """
    
    # Simulate a user authenticated via Keycloak JWT token
    mock_token_user = CurrentUser(
        user_id="auth0|507f1f77bcf86cd799439011",
        username="John Demo User",
        email="john.demo@example.com",
        roles=["user"],
        claims={"iss": "https://your-keycloak-domain.com"}
    )
    
    logger.info("=== JIT User Provisioning Demo ===")
    logger.info(f"Simulating authenticated user: {mock_token_user.email}")
    logger.info(f"User ID from token: {mock_token_user.user_id}")
    logger.info(f"Username from token: {mock_token_user.username}")
    logger.info(f"Roles: {mock_token_user.roles}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Check if user exists in local database
            logger.info("\n--- Step 1: Checking if user exists locally ---")
            existing_user = await crud.user.get_by_email(db, email=mock_token_user.email)
            
            if existing_user:
                logger.info(f"✓ User found in database: ID={existing_user.id}")
                logger.info(f"  Email: {existing_user.email}")
                logger.info(f"  Full Name: {existing_user.full_name}")
                logger.info(f"  Active: {existing_user.is_active}")
                logger.info(f"  Created: {existing_user.created_at}")
                return existing_user
            else:
                logger.info("✗ User not found in local database")
                
                # Step 2: Create user via JIT provisioning
                logger.info("\n--- Step 2: Creating user via JIT provisioning ---")
                new_user = await crud.user.create_from_token(db, token_data=mock_token_user)
                
                logger.info(f"✓ User created successfully!")
                logger.info(f"  Database ID: {new_user.id}")
                logger.info(f"  Email: {new_user.email}")
                logger.info(f"  Full Name: {new_user.full_name}")
                logger.info(f"  Active: {new_user.is_active}")
                logger.info(f"  Created: {new_user.created_at}")
                logger.info(f"  Has Password: {new_user.hashed_password is not None}")
                
                return new_user
                
        except Exception as e:
            logger.error(f"Error during JIT provisioning: {e}")
            await db.rollback()
            raise
        else:
            await db.commit()


async def simulate_profile_update():
    """
    Simulate updating a user profile, demonstrating JIT provisioning during updates.
    """
    
    mock_token_user = CurrentUser(
        user_id="auth0|507f1f77bcf86cd799439012",
        username="Jane Update Demo",
        email="jane.update@example.com",
        roles=["user", "premium"],
        claims={}
    )
    
    logger.info("\n\n=== User Profile Update Demo ===")
    logger.info(f"Simulating profile update for: {mock_token_user.email}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if user exists, create if not (JIT provisioning)
            db_user = await crud.user.get_by_email(db, email=mock_token_user.email)
            
            if not db_user:
                logger.info("User not found, creating via JIT provisioning...")
                db_user = await crud.user.create_from_token(db, token_data=mock_token_user)
                logger.info(f"✓ User created: {db_user.email}")
            else:
                logger.info(f"✓ Existing user found: {db_user.email}")
            
            # Update user profile
            update_data = {
                "full_name": "Jane Updated Full Name",
                "is_active": True
            }
            
            logger.info(f"\nUpdating profile with: {update_data}")
            updated_user = await crud.user.update(db, db_obj=db_user, obj_in=update_data)
            
            logger.info(f"✓ Profile updated successfully!")
            logger.info(f"  Full Name: {updated_user.full_name}")
            logger.info(f"  Active: {updated_user.is_active}")
            logger.info(f"  Updated: {updated_user.updated_at}")
            
        except Exception as e:
            logger.error(f"Error during profile update: {e}")
            await db.rollback()
            raise
        else:
            await db.commit()


async def demonstrate_role_based_access():
    """
    Demonstrate how different user roles affect access patterns.
    """
    
    users = [
        CurrentUser(
            user_id="auth0|regular_user",
            username="Regular User",
            email="regular@example.com",
            roles=["user"],
            claims={}
        ),
        CurrentUser(
            user_id="auth0|admin_user",
            username="Admin User",
            email="admin@example.com",
            roles=["user", "admin"],
            claims={}
        ),
        CurrentUser(
            user_id="auth0|premium_user",
            username="Premium User",
            email="premium@example.com",
            roles=["user", "premium"],
            claims={}
        )
    ]
    
    logger.info("\n\n=== Role-Based Access Demo ===")
    
    for user in users:
        logger.info(f"\nProcessing user: {user.email}")
        logger.info(f"  Roles: {user.roles}")
        logger.info(f"  Has admin role: {user.has_role('admin')}")
        logger.info(f"  Has premium access: {user.has_any_role(['premium', 'admin'])}")
        
        # Simulate JIT provisioning for each user type
        async with AsyncSessionLocal() as db:
            try:
                db_user = await crud.user.get_by_email(db, email=user.email)
                if not db_user:
                    db_user = await crud.user.create_from_token(db, token_data=user)
                    logger.info(f"  ✓ User provisioned with ID: {db_user.id}")
                else:
                    logger.info(f"  ✓ User exists with ID: {db_user.id}")
                    
            except Exception as e:
                logger.error(f"  ✗ Error processing user: {e}")
                await db.rollback()
            else:
                await db.commit()


async def cleanup_demo_users():
    """
    Clean up demo users created during this demonstration.
    """
    
    demo_emails = [
        "john.demo@example.com",
        "jane.update@example.com",
        "regular@example.com",
        "admin@example.com",
        "premium@example.com"
    ]
    
    logger.info("\n\n=== Cleanup Demo Users ===")
    
    async with AsyncSessionLocal() as db:
        try:
            for email in demo_emails:
                user = await crud.user.get_by_email(db, email=email)
                if user:
                    await db.delete(user)
                    logger.info(f"✓ Deleted demo user: {email}")
                else:
                    logger.info(f"- Demo user not found: {email}")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise
        else:
            await db.commit()
            logger.info("✓ Cleanup completed")


async def main():
    """
    Run the complete JIT provisioning demonstration.
    """
    
    try:
        logger.info("Starting JIT User Provisioning Demonstration")
        logger.info("=" * 50)
        
        # Demonstrate basic JIT provisioning
        await simulate_jit_provisioning()
        
        # Demonstrate JIT provisioning during profile updates
        await simulate_profile_update()
        
        # Demonstrate role-based access patterns
        await demonstrate_role_based_access()
        
        logger.info("\n" + "=" * 50)
        logger.info("Demo completed successfully!")
        logger.info("\nKey Benefits of JIT Provisioning:")
        logger.info("1. Users are automatically created when first accessed")
        logger.info("2. No manual user management required")
        logger.info("3. Seamless integration with external identity providers")
        logger.info("4. Local database maintains referential integrity")
        logger.info("5. Supports both password-based and token-based authentication")
        
        # Ask if user wants to clean up
        print("\nWould you like to clean up the demo users? (y/n): ", end="")
        # In a real script, you'd get user input here
        # For demo purposes, we'll assume 'y'
        choice = 'y'
        
        if choice.lower() == 'y':
            await cleanup_demo_users()
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
