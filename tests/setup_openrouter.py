#!/usr/bin/env python3
"""
Configuration script for OpenRouter LLM integration.
This script helps set up environment variables for OpenRouter testing.
"""

import sys


def create_env_file():
    """Create a .env file with OpenRouter configuration."""
    print("🔧 Creating .env file for OpenRouter configuration")
    print("=" * 50)

    # Ask for API key
    api_key = input("Enter your OpenRouter API key (starts with 'sk-or-v1-'): ").strip()

    if not api_key:
        print("❌ API key is required!")
        return False

    if not api_key.startswith("sk-or-v1-"):
        print("⚠️  Warning: API key doesn't start with 'sk-or-v1-', but proceeding...")

    # Choose model
    print("\nAvailable models:")
    models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "anthropic/claude-3-haiku",
        "anthropic/claude-3-sonnet",
        "anthropic/claude-3-opus",
        "meta-llama/llama-2-70b-chat",
        "microsoft/wizardlm-70b",
        "google/palm-2-codechat-bison",
        "cohere/command-r-plus",
    ]

    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")

    choice = input(f"\nChoose model (1-{len(models)}) [1]: ").strip()

    if not choice:
        choice = "1"

    try:
        model_index = int(choice) - 1
        if 0 <= model_index < len(models):
            selected_model = models[model_index]
        else:
            print("❌ Invalid choice, using default model")
            selected_model = models[0]
    except ValueError:
        print("❌ Invalid choice, using default model")
        selected_model = models[0]

    # Graph database settings
    print("\nGraph database configuration:")
    neo4j_url = (
        input("Neo4j URL [bolt://localhost:7687]: ").strip() or "bolt://localhost:7687"
    )
    neo4j_user = input("Neo4j username [neo4j]: ").strip() or "neo4j"
    neo4j_password = input("Neo4j password [password]: ").strip() or "password"

    # Create .env content
    env_content = f"""# OpenRouter LLM Configuration
OPENROUTER_API_KEY={api_key}
GRAPH_LLM_PROVIDER=openrouter
GRAPH_LLM_MODEL={selected_model}

# Graph Processing Configuration
GRAPH_ENABLED=true
GRAPH_ENTITY_EXTRACTION_METHOD=llm_based
GRAPH_TOPIC_EXTRACTION_METHOD=llm_based
GRAPH_SENTIMENT_ANALYSIS_ENABLED=true
GRAPH_RELATIONSHIP_EXTRACTION_METHOD=llm_based

# LLM Settings
GRAPH_LLM_MAX_TOKENS=1000
GRAPH_LLM_TEMPERATURE=0.1
GRAPH_LLM_BATCH_SIZE=5

# Graph Database Configuration
GRAPH_DATABASE_TYPE=neo4j
GRAPH_DATABASE_URL={neo4j_url}
GRAPH_DATABASE_USERNAME={neo4j_user}
GRAPH_DATABASE_PASSWORD={neo4j_password}
GRAPH_DATABASE_NAME=neo4j

# Application Settings
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ .env file created successfully!")
        print("\nTo use this configuration:")
        print("1. Load the environment variables:")
        print("   - Linux/Mac: source .env")
        print(
            "   - Windows PowerShell: Get-Content .env | ForEach-Object { $name, $value = $_.split('=', 2); Set-Item -Path \"env:$name\" -Value $value }"
        )
        print("2. Run the test: python test_openrouter_config.py")

        return True

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def create_powershell_script():
    """Create a PowerShell script to set environment variables."""
    print("🔧 Creating PowerShell script for environment setup")
    print("=" * 50)

    # Ask for API key
    api_key = input("Enter your OpenRouter API key (starts with 'sk-or-v1-'): ").strip()

    if not api_key:
        print("❌ API key is required!")
        return False

    # Choose model
    print("\nAvailable models:")
    models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-2-70b-chat",
    ]

    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")

    choice = input(f"\nChoose model (1-{len(models)}) [1]: ").strip()

    if not choice:
        choice = "1"

    try:
        model_index = int(choice) - 1
        if 0 <= model_index < len(models):
            selected_model = models[model_index]
        else:
            selected_model = models[0]
    except ValueError:
        selected_model = models[0]

    # Create PowerShell script
    ps_content = f"""# OpenRouter LLM Configuration Script
Write-Host "Setting up OpenRouter environment variables..." -ForegroundColor Green

# OpenRouter Configuration
$env:OPENROUTER_API_KEY = "{api_key}"
$env:GRAPH_LLM_PROVIDER = "openrouter"
$env:GRAPH_LLM_MODEL = "{selected_model}"

# Graph Processing Configuration
$env:GRAPH_ENABLED = "true"
$env:GRAPH_ENTITY_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_TOPIC_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_SENTIMENT_ANALYSIS_ENABLED = "true"
$env:GRAPH_RELATIONSHIP_EXTRACTION_METHOD = "llm_based"

# LLM Settings
$env:GRAPH_LLM_MAX_TOKENS = "1000"
$env:GRAPH_LLM_TEMPERATURE = "0.1"
$env:GRAPH_LLM_BATCH_SIZE = "5"

# Graph Database Configuration
$env:GRAPH_DATABASE_TYPE = "neo4j"
$env:GRAPH_DATABASE_URL = "bolt://localhost:7687"
$env:GRAPH_DATABASE_USERNAME = "neo4j"
$env:GRAPH_DATABASE_PASSWORD = "password"
$env:GRAPH_DATABASE_NAME = "neo4j"

# Application Settings
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"
$env:LOG_LEVEL = "INFO"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "You can now run the tests:" -ForegroundColor Yellow
Write-Host "  python verify_openrouter_config.py" -ForegroundColor Yellow
Write-Host "  python test_openrouter_config.py" -ForegroundColor Yellow
Write-Host "  python test_llm_graph_advanced.py" -ForegroundColor Yellow
"""

    try:
        with open("setup_openrouter.ps1", "w") as f:
            f.write(ps_content)

        print("✅ PowerShell script created successfully!")
        print("\nTo use this script:")
        print("1. Run in PowerShell: .\\setup_openrouter.ps1")
        print("2. Run the test: python test_openrouter_config.py")

        return True

    except Exception as e:
        print(f"❌ Error creating PowerShell script: {e}")
        return False


def main():
    """Main configuration function."""
    print("🚀 OpenRouter Configuration Setup")
    print("=" * 50)
    print()

    print("Choose configuration method:")
    print("1. Create .env file")
    print("2. Create PowerShell script")
    print("3. Display manual configuration")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        create_env_file()
    elif choice == "2":
        create_powershell_script()
    elif choice == "3":
        print("\n📋 Manual Configuration:")
        print("Set these environment variables:")
        print("- OPENROUTER_API_KEY=your_api_key_here")
        print("- GRAPH_LLM_PROVIDER=openrouter")
        print("- GRAPH_LLM_MODEL=openai/gpt-3.5-turbo")
        print("- GRAPH_ENABLED=true")
        print("- GRAPH_ENTITY_EXTRACTION_METHOD=llm_based")
        print("- GRAPH_TOPIC_EXTRACTION_METHOD=llm_based")
        print("- GRAPH_SENTIMENT_ANALYSIS_ENABLED=true")
        print("- GRAPH_RELATIONSHIP_EXTRACTION_METHOD=llm_based")
    else:
        print("❌ Invalid choice!")
        sys.exit(1)


if __name__ == "__main__":
    main()
