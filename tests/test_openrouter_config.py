#!/usr/bin/env python3
"""
Test script to verify OpenRouter configuration and environment variable support.
This script demonstrates how to configure and test OpenRouter LLM provider.
"""

import asyncio
import json
import os
from datetime import datetime

def show_configuration_help():
    """Display configuration help for OpenRouter."""
    print("🔧 OpenRouter Configuration Guide")
    print("=" * 50)
    print()
    print("1. Environment Variables Required:")
    print("   - OPENROUTER_API_KEY: Your OpenRouter API key")
    print("   - GRAPH_LLM_PROVIDER: Set to 'openrouter'")
    print("   - GRAPH_LLM_MODEL: Model to use (e.g., 'openai/gpt-3.5-turbo')")
    print()
    print("2. Available Models on OpenRouter:")
    print("   - openai/gpt-3.5-turbo")
    print("   - openai/gpt-4")
    print("   - anthropic/claude-3-haiku")
    print("   - anthropic/claude-3-sonnet")
    print("   - meta-llama/llama-2-70b-chat")
    print("   - microsoft/wizardlm-70b")
    print("   - and many more...")
    print()
    print("3. Example Configuration:")
    print("   export OPENROUTER_API_KEY='sk-or-v1-...'")
    print("   export GRAPH_LLM_PROVIDER='openrouter'")
    print("   export GRAPH_LLM_MODEL='openai/gpt-3.5-turbo'")
    print("   export GRAPH_ENABLED='true'")
    print("   export GRAPH_ENTITY_EXTRACTION_METHOD='llm_based'")
    print("   export GRAPH_TOPIC_EXTRACTION_METHOD='llm_based'")
    print("   export GRAPH_SENTIMENT_ANALYSIS_ENABLED='true'")
    print("   export GRAPH_RELATIONSHIP_EXTRACTION_METHOD='llm_based'")
    print()
    print("4. PowerShell Configuration:")
    print("   $env:OPENROUTER_API_KEY='sk-or-v1-...'")
    print("   $env:GRAPH_LLM_PROVIDER='openrouter'")
    print("   $env:GRAPH_LLM_MODEL='openai/gpt-3.5-turbo'")
    print("   $env:GRAPH_ENABLED='true'")
    print("   $env:GRAPH_ENTITY_EXTRACTION_METHOD='llm_based'")
    print("   $env:GRAPH_TOPIC_EXTRACTION_METHOD='llm_based'")
    print("   $env:GRAPH_SENTIMENT_ANALYSIS_ENABLED='true'")
    print("   $env:GRAPH_RELATIONSHIP_EXTRACTION_METHOD='llm_based'")
    print()

def check_environment_variables():
    """Check if required environment variables are set."""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    required_vars = {
        "OPENROUTER_API_KEY": "OpenRouter API key",
        "GRAPH_LLM_PROVIDER": "LLM provider (should be 'openrouter')",
        "GRAPH_LLM_MODEL": "LLM model to use",
        "GRAPH_ENABLED": "Graph processing enabled",
    }
    
    optional_vars = {
        "GRAPH_ENTITY_EXTRACTION_METHOD": "Entity extraction method",
        "GRAPH_TOPIC_EXTRACTION_METHOD": "Topic extraction method",
        "GRAPH_SENTIMENT_ANALYSIS_ENABLED": "Sentiment analysis enabled",
        "GRAPH_RELATIONSHIP_EXTRACTION_METHOD": "Relationship extraction method",
        "GRAPH_LLM_MAX_TOKENS": "Max tokens for LLM",
        "GRAPH_LLM_TEMPERATURE": "Temperature for LLM",
    }
    
    all_set = True
    
    print("Required variables:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            # Hide API key for security
            display_value = value if var != "OPENROUTER_API_KEY" else f"{value[:8]}..."
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET ({desc})")
            all_set = False
    
    print("\nOptional variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NOT SET ({desc})")
    
    print()
    return all_set

async def test_openrouter_provider():
    """Test OpenRouter provider directly."""
    print("🧪 Testing OpenRouter Provider")
    print("=" * 50)
    
    try:
        from app.core.llm_graph_processors import OpenRouterProvider
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY not found in environment")
            return False
        
        model = os.getenv("GRAPH_LLM_MODEL", "openai/gpt-3.5-turbo")
        
        print(f"📡 Testing OpenRouter with model: {model}")
        provider = OpenRouterProvider(api_key=api_key, model=model)
        
        # Test simple completion
        test_prompt = "Extract entities from this text: 'Dr. Sarah Johnson from Stanford University discovered a new AI breakthrough.'"
        
        print("🔄 Sending test request...")
        response = await provider.generate_completion(test_prompt, max_tokens=100)
        
        print(f"✅ Response received: {response[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False

async def test_llm_factory():
    """Test LLM factory with OpenRouter."""
    print("🏭 Testing LLM Factory")
    print("=" * 50)
    
    try:
        from app.core.llm_graph_processors import LLMGraphProcessorFactory
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        print(f"📊 Settings provider: {settings.graph.llm_provider}")
        print(f"📊 Settings model: {settings.graph.llm_model}")
        
        # Test factory creation
        provider = LLMGraphProcessorFactory.create_llm_provider(settings)
        print(f"✅ Provider created: {type(provider).__name__}")
        
        # Test entity extractor
        entity_extractor = LLMGraphProcessorFactory.create_entity_extractor(settings)
        print(f"✅ Entity extractor created: {type(entity_extractor).__name__}")
        
        # Test topic modeler
        topic_modeler = LLMGraphProcessorFactory.create_topic_modeler(settings)
        print(f"✅ Topic modeler created: {type(topic_modeler).__name__}")
        
        # Test sentiment analyzer
        sentiment_analyzer = LLMGraphProcessorFactory.create_sentiment_analyzer(settings)
        print(f"✅ Sentiment analyzer created: {type(sentiment_analyzer).__name__}")
        
        # Test relationship extractor
        relationship_extractor = LLMGraphProcessorFactory.create_relationship_extractor(settings)
        print(f"✅ Relationship extractor created: {type(relationship_extractor).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False

async def test_entity_extraction():
    """Test entity extraction with OpenRouter."""
    print("🏷️ Testing Entity Extraction")
    print("=" * 50)
    
    try:
        from app.core.llm_graph_processors import LLMGraphProcessorFactory
        from app.config.settings import get_settings
        
        settings = get_settings()
        entity_extractor = LLMGraphProcessorFactory.create_entity_extractor(settings)
        
        test_text = "Dr. Sarah Johnson from Stanford University met with John Smith from TechCorp Inc. in San Francisco on March 15th, 2024."
        
        print(f"📝 Test text: {test_text}")
        print("🔄 Extracting entities...")
        
        entities = await entity_extractor.extract_entities(test_text)
        
        print(f"✅ Extracted {len(entities)} entities:")
        for entity_text, entity_type, confidence in entities:
            print(f"  - {entity_text} ({entity_type}, confidence: {confidence:.2f})")
        
        return len(entities) > 0
        
    except Exception as e:
        print(f"❌ Entity extraction test failed: {e}")
        return False

async def test_topic_modeling():
    """Test topic modeling with OpenRouter."""
    print("📊 Testing Topic Modeling")
    print("=" * 50)
    
    try:
        from app.core.llm_graph_processors import LLMGraphProcessorFactory
        from app.config.settings import get_settings
        
        settings = get_settings()
        topic_modeler = LLMGraphProcessorFactory.create_topic_modeler(settings)
        
        test_text = "Our research team has developed an AI system that can diagnose cancer with 95% accuracy using medical imaging. This breakthrough in healthcare technology could save thousands of lives and revolutionize medical diagnostics."
        
        print(f"📝 Test text: {test_text}")
        print("🔄 Extracting topics...")
        
        topics = await topic_modeler.extract_topics(test_text)
        
        print(f"✅ Extracted {len(topics)} topics:")
        for topic_name, confidence in topics:
            print(f"  - {topic_name} (confidence: {confidence:.2f})")
        
        return len(topics) > 0
        
    except Exception as e:
        print(f"❌ Topic modeling test failed: {e}")
        return False

async def test_sentiment_analysis():
    """Test sentiment analysis with OpenRouter."""
    print("💭 Testing Sentiment Analysis")
    print("=" * 50)
    
    try:
        from app.core.llm_graph_processors import LLMGraphProcessorFactory
        from app.config.settings import get_settings
        
        settings = get_settings()
        sentiment_analyzer = LLMGraphProcessorFactory.create_sentiment_analyzer(settings)
        
        test_texts = [
            "I'm excited about this collaboration! This technology could save thousands of lives.",
            "However, we need to address regulatory compliance and patient privacy concerns first.",
            "This is a neutral statement about the meeting schedule for next Friday."
        ]
        
        for i, test_text in enumerate(test_texts, 1):
            print(f"📝 Test text {i}: {test_text}")
            print("🔄 Analyzing sentiment...")
            
            sentiment_result = await sentiment_analyzer.analyze_sentiment(test_text)
            
            sentiment_label = sentiment_result.get("sentiment", "neutral")
            confidence = sentiment_result.get("confidence", 0.5)
            emotions = sentiment_result.get("emotions", [])
            intensity = sentiment_result.get("intensity", 0.5)
            
            print(f"✅ Sentiment: {sentiment_label} (confidence: {confidence:.2f})")
            if emotions:
                print(f"   Emotions: {', '.join(emotions)}")
            print(f"   Intensity: {intensity:.2f}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Sentiment analysis test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 OpenRouter Configuration Test")
    print("=" * 50)
    print()
    
    # Show configuration help
    show_configuration_help()
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("❌ Required environment variables not set. Please configure them first.")
        return
    
    # Test OpenRouter provider
    print()
    provider_ok = await test_openrouter_provider()
    
    if not provider_ok:
        print("❌ OpenRouter provider test failed. Check your API key and configuration.")
        return
    
    # Test LLM factory
    print()
    factory_ok = await test_llm_factory()
    
    if not factory_ok:
        print("❌ LLM factory test failed.")
        return
    
    # Test individual components
    print()
    await test_entity_extraction()
    
    print()
    await test_topic_modeling()
    
    print()
    await test_sentiment_analysis()
    
    print()
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
