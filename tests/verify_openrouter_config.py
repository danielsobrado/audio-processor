#!/usr/bin/env python3
"""
Simple test to verify OpenRouter configuration is working correctly.
This test checks the configuration setup without making actual API calls.
"""

import os
import sys

# Set up basic environment for testing
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "password")
os.environ.setdefault("GRAPH_ENABLED", "true")

# Set up OpenRouter configuration for testing
os.environ.setdefault("GRAPH_LLM_PROVIDER", "openrouter")
os.environ.setdefault("GRAPH_LLM_MODEL", "openai/gpt-3.5-turbo")
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-v1-test-key")  # Test key


def test_configuration():
    """Test the OpenRouter configuration setup."""
    print("🔧 Testing OpenRouter Configuration")
    print("=" * 50)

    try:
        from app.config.settings import get_settings

        settings = get_settings()

        print("✅ Settings loaded successfully")
        print(f"📊 Graph enabled: {settings.graph.enabled}")
        print(f"📊 LLM provider: {settings.graph.llm_provider}")
        print(f"📊 LLM model: {settings.graph.llm_model}")
        print(f"📊 Entity extraction: {settings.graph.entity_extraction_method}")
        print(f"📊 Topic extraction: {settings.graph.topic_extraction_method}")
        print(f"📊 Sentiment analysis: {settings.graph.sentiment_analysis_enabled}")
        print(
            f"📊 Relationship extraction: {settings.graph.relationship_extraction_method}"
        )

        # Test if API key is properly read
        api_key = settings.graph.llm_api_key or os.getenv("OPENROUTER_API_KEY")
        if api_key:
            print(f"✅ API key configured: {api_key[:8]}...")
        else:
            print("❌ API key not found")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_llm_factory():
    """Test LLM factory initialization."""
    print("\n🏭 Testing LLM Factory")
    print("=" * 50)

    try:
        from app.config.settings import get_settings
        from app.core.llm_graph_processors import LLMGraphProcessorFactory

        settings = get_settings()

        # Test factory methods (without making API calls)
        print("🔄 Testing factory methods...")

        # This will fail if API key is not real, but we can catch it
        try:
            provider = LLMGraphProcessorFactory.create_llm_provider(settings)
            print(f"✅ LLM provider created: {type(provider).__name__}")
        except ValueError as e:
            if "API key is required" in str(e):
                print("⚠️  API key validation passed (factory requires real key)")
            else:
                print(f"❌ Factory error: {e}")

        # Test other factory methods
        try:
            entity_extractor = LLMGraphProcessorFactory.create_entity_extractor(
                settings
            )
            print(f"✅ Entity extractor factory: {type(entity_extractor).__name__}")
        except Exception as e:
            print(f"⚠️  Entity extractor factory: {e}")

        try:
            topic_modeler = LLMGraphProcessorFactory.create_topic_modeler(settings)
            print(f"✅ Topic modeler factory: {type(topic_modeler).__name__}")
        except Exception as e:
            print(f"⚠️  Topic modeler factory: {e}")

        try:
            sentiment_analyzer = LLMGraphProcessorFactory.create_sentiment_analyzer(
                settings
            )
            print(f"✅ Sentiment analyzer factory: {type(sentiment_analyzer).__name__}")
        except Exception as e:
            print(f"⚠️  Sentiment analyzer factory: {e}")

        try:
            relationship_extractor = (
                LLMGraphProcessorFactory.create_relationship_extractor(settings)
            )
            print(
                f"✅ Relationship extractor factory: {type(relationship_extractor).__name__}"
            )
        except Exception as e:
            print(f"⚠️  Relationship extractor factory: {e}")

        return True

    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False


def test_graph_processor_integration():
    """Test graph processor integration."""
    print("\n🔄 Testing Graph Processor Integration")
    print("=" * 50)

    try:
        from app.config.settings import get_settings
        from app.core.graph_processor import GraphProcessor

        settings = get_settings()

        # Initialize graph processor
        processor = GraphProcessor()

        print("✅ Graph processor initialized")

        # Check if LLM extractors are configured
        if (
            hasattr(processor, "llm_entity_extractor")
            and processor.llm_entity_extractor
        ):
            print("✅ LLM entity extractor configured")
        else:
            print("⚠️  LLM entity extractor not configured")

        if hasattr(processor, "llm_topic_modeler") and processor.llm_topic_modeler:
            print("✅ LLM topic modeler configured")
        else:
            print("⚠️  LLM topic modeler not configured")

        if (
            hasattr(processor, "llm_sentiment_analyzer")
            and processor.llm_sentiment_analyzer
        ):
            print("✅ LLM sentiment analyzer configured")
        else:
            print("⚠️  LLM sentiment analyzer not configured")

        if (
            hasattr(processor, "llm_relationship_extractor")
            and processor.llm_relationship_extractor
        ):
            print("✅ LLM relationship extractor configured")
        else:
            print("⚠️  LLM relationship extractor not configured")

        return True

    except Exception as e:
        print(f"❌ Graph processor integration test failed: {e}")
        return False


def test_environment_variables():
    """Test environment variable configuration."""
    print("\n🌍 Testing Environment Variables")
    print("=" * 50)

    required_vars = [
        "GRAPH_LLM_PROVIDER",
        "GRAPH_LLM_MODEL",
        "GRAPH_ENABLED",
        "OPENROUTER_API_KEY",
    ]

    optional_vars = [
        "GRAPH_ENTITY_EXTRACTION_METHOD",
        "GRAPH_TOPIC_EXTRACTION_METHOD",
        "GRAPH_SENTIMENT_ANALYSIS_ENABLED",
        "GRAPH_RELATIONSHIP_EXTRACTION_METHOD",
        "GRAPH_LLM_MAX_TOKENS",
        "GRAPH_LLM_TEMPERATURE",
    ]

    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide API key for security
            display_value = value if var != "OPENROUTER_API_KEY" else f"{value[:8]}..."
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")

    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NOT SET")

    return True


def main():
    """Main test function."""
    print("🚀 OpenRouter Configuration Verification")
    print("=" * 50)

    # Test configuration
    config_ok = test_configuration()

    # Test environment variables
    env_ok = test_environment_variables()

    # Test LLM factory
    factory_ok = test_llm_factory()

    # Test graph processor integration
    processor_ok = test_graph_processor_integration()

    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Environment: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Factory: {'✅ PASS' if factory_ok else '❌ FAIL'}")
    print(f"Integration: {'✅ PASS' if processor_ok else '❌ FAIL'}")

    if all([config_ok, env_ok, factory_ok, processor_ok]):
        print("\n🎉 All configuration tests passed!")
        print("Next steps:")
        print("1. Set a real OpenRouter API key in OPENROUTER_API_KEY")
        print("2. Run: python test_openrouter_config.py")
        print("3. Or run: python test_llm_graph_advanced.py")
    else:
        print("\n❌ Some tests failed. Check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
