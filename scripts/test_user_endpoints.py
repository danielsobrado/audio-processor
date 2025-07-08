#!/usr/bin/env python3
"""
Quick test script for user profile endpoints with JIT provisioning.

This script can be used to manually test the user endpoints.
"""

import json
import sys
from datetime import datetime, timedelta

# Mock JWT creation for testing (in production, this comes from Keycloak)
def create_mock_jwt_payload(user_id: str, email: str, username: str, roles=None):
    """Create a mock JWT payload for testing."""
    if roles is None:
        roles = ["user"]
    
    return {
        "sub": user_id,
        "email": email,
        "preferred_username": username,
        "realm_access": {
            "roles": roles
        },
        "iss": "https://your-keycloak-domain.com",
        "aud": "audio-processor-api",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }


def test_scenarios():
    """Define test scenarios for the user endpoints."""
    
    scenarios = [
        {
            "name": "New User - First Time Access",
            "description": "Test JIT provisioning for a brand new user",
            "user": {
                "user_id": "auth0|507f1f77bcf86cd799439011",
                "email": "newuser@example.com",
                "username": "New User",
                "roles": ["user"]
            },
            "expected": {
                "should_create_user": True,
                "response_code": 200,
                "has_profile": True
            }
        },
        {
            "name": "Existing User - Return Visit",
            "description": "Test that existing users don't get recreated",
            "user": {
                "user_id": "auth0|507f1f77bcf86cd799439012",
                "email": "existing@example.com",
                "username": "Existing User",
                "roles": ["user"]
            },
            "expected": {
                "should_create_user": False,
                "response_code": 200,
                "has_profile": True
            }
        },
        {
            "name": "Admin User - Role-Based Access",
            "description": "Test admin user with elevated privileges",
            "user": {
                "user_id": "auth0|507f1f77bcf86cd799439013",
                "email": "admin@example.com",
                "username": "Admin User",
                "roles": ["user", "admin"]
            },
            "expected": {
                "should_create_user": True,
                "response_code": 200,
                "has_profile": True,
                "can_list_users": True
            }
        },
        {
            "name": "Profile Update - JIT Creation",
            "description": "Test profile update that triggers JIT provisioning",
            "user": {
                "user_id": "auth0|507f1f77bcf86cd799439014",
                "email": "updateuser@example.com",
                "username": "Update User",
                "roles": ["user"]
            },
            "update_data": {
                "full_name": "Updated Full Name",
                "is_active": True
            },
            "expected": {
                "should_create_user": True,
                "response_code": 200,
                "updated_name": "Updated Full Name"
            }
        }
    ]
    
    return scenarios


def print_test_curl_commands():
    """Print curl commands for manual testing."""
    
    print("=== Manual Testing with curl ===\n")
    
    print("Note: Replace <JWT_TOKEN> with actual JWT token from Keycloak\n")
    
    commands = [
        {
            "name": "Get Current User Profile",
            "command": 'curl -X GET "http://localhost:8000/api/v1/users/me" \\\n  -H "Authorization: Bearer <JWT_TOKEN>" \\\n  -H "Content-Type: application/json"'
        },
        {
            "name": "Update Current User Profile",
            "command": 'curl -X PUT "http://localhost:8000/api/v1/users/me" \\\n  -H "Authorization: Bearer <JWT_TOKEN>" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"full_name": "Updated Name", "is_active": true}\''
        },
        {
            "name": "List All Users (Admin Only)",
            "command": 'curl -X GET "http://localhost:8000/api/v1/users/" \\\n  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \\\n  -H "Content-Type: application/json"'
        },
        {
            "name": "Create New User (Public)",
            "command": 'curl -X POST "http://localhost:8000/api/v1/users/" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"email": "newuser@example.com", "password": "securepass123", "full_name": "New User"}\''
        }
    ]
    
    for cmd in commands:
        print(f"## {cmd['name']}")
        print(f"```bash\n{cmd['command']}\n```\n")


def print_jwt_example():
    """Print example JWT tokens for testing."""
    
    print("=== Example JWT Payloads ===\n")
    
    examples = [
        {
            "name": "Regular User",
            "payload": create_mock_jwt_payload(
                "auth0|507f1f77bcf86cd799439011",
                "user@example.com",
                "Regular User",
                ["user"]
            )
        },
        {
            "name": "Admin User",
            "payload": create_mock_jwt_payload(
                "auth0|507f1f77bcf86cd799439012",
                "admin@example.com",
                "Admin User",
                ["user", "admin"]
            )
        },
        {
            "name": "Premium User",
            "payload": create_mock_jwt_payload(
                "auth0|507f1f77bcf86cd799439013",
                "premium@example.com",
                "Premium User",
                ["user", "premium"]
            )
        }
    ]
    
    for example in examples:
        print(f"## {example['name']}")
        print("```json")
        print(json.dumps(example['payload'], indent=2))
        print("```\n")


def print_test_scenarios():
    """Print detailed test scenarios."""
    
    print("=== Test Scenarios ===\n")
    
    scenarios = test_scenarios()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"## Scenario {i}: {scenario['name']}")
        print(f"**Description**: {scenario['description']}\n")
        
        print("**User Data**:")
        print(f"- Email: {scenario['user']['email']}")
        print(f"- Username: {scenario['user']['username']}")
        print(f"- Roles: {scenario['user']['roles']}\n")
        
        print("**Expected Behavior**:")
        for key, value in scenario['expected'].items():
            print(f"- {key.replace('_', ' ').title()}: {value}")
        
        if 'update_data' in scenario:
            print(f"\n**Update Data**: {scenario['update_data']}")
        
        print("\n" + "-" * 50 + "\n")


def print_validation_checklist():
    """Print validation checklist for manual testing."""
    
    print("=== Validation Checklist ===\n")
    
    checklist = [
        "□ JWT token validation works correctly",
        "□ New users are created automatically on first access",
        "□ Existing users are not duplicated",
        "□ User profile data is correctly extracted from JWT",
        "□ Profile updates work for both new and existing users",
        "□ Role-based access control is enforced",
        "□ Database transactions are properly handled",
        "□ Error responses are informative and secure",
        "□ Logging captures JIT provisioning events",
        "□ Performance is acceptable under load",
        "□ Security headers are present in responses",
        "□ API documentation is accurate and complete"
    ]
    
    print("Check off each item as you validate the functionality:\n")
    for item in checklist:
        print(item)
    
    print("\n")


def main():
    """Main function to run the test guide."""
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        action = "all"
    
    print("User Profile Endpoints Test Guide")
    print("=" * 40 + "\n")
    
    if action in ["all", "scenarios"]:
        print_test_scenarios()
    
    if action in ["all", "curl"]:
        print_test_curl_commands()
    
    if action in ["all", "jwt"]:
        print_jwt_example()
    
    if action in ["all", "checklist"]:
        print_validation_checklist()
    
    if action not in ["scenarios", "curl", "jwt", "checklist", "all"]:
        print("Usage: python test_user_endpoints.py [scenarios|curl|jwt|checklist|all]")
        print("\nOptions:")
        print("  scenarios  - Show test scenarios")
        print("  curl      - Show curl commands")
        print("  jwt       - Show JWT examples")
        print("  checklist - Show validation checklist")
        print("  all       - Show everything (default)")


if __name__ == "__main__":
    main()
