#!/usr/bin/env python3
"""
Test script to demonstrate LLM-based graph processing capabilities.
This script shows how to use different LLM providers for entity extraction,
topic modeling, sentiment analysis, and relationship extraction.
"""

import asyncio
import json
import os
from datetime import datetime

# Set up environment variables for testing
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "devpassword")
os.environ.setdefault("GRAPH_ENABLED", "true")

# LLM Configuration - uncomment and configure as needed
# os.environ.setdefault("GRAPH_LLM_PROVIDER", "openrouter")  # or "openai", "anthropic", "local"
# os.environ.setdefault("GRAPH_LLM_MODEL", "openai/gpt-3.5-turbo")  # or your preferred model
# os.environ.setdefault("OPENROUTER_API_KEY", "your_openrouter_key_here")

# For testing without LLM, use rule-based methods
os.environ.setdefault("GRAPH_ENTITY_EXTRACTION_METHOD", "regex_patterns")
os.environ.setdefault("GRAPH_TOPIC_EXTRACTION_METHOD", "keyword_matching")
os.environ.setdefault("GRAPH_SENTIMENT_ANALYSIS_ENABLED", "false")
os.environ.setdefault("GRAPH_RELATIONSHIP_EXTRACTION_METHOD", "rule_based")

# Enable LLM-based processing (uncomment when you have API keys configured)
# os.environ.setdefault("GRAPH_ENTITY_EXTRACTION_METHOD", "llm_based")
# os.environ.setdefault("GRAPH_TOPIC_EXTRACTION_METHOD", "llm_based")
# os.environ.setdefault("GRAPH_SENTIMENT_ANALYSIS_ENABLED", "true")
# os.environ.setdefault("GRAPH_RELATIONSHIP_EXTRACTION_METHOD", "llm_based")


async def test_llm_graph_processing():
    """Test LLM-based graph processing capabilities."""
    print("🤖 Testing LLM-based Graph Processing")
    print("=" * 50)
    
    # More complex sample text with entities and relationships
    sample_segments = [
        {
            "start": 0.0,
            "end": 8.0,
            "text": "Hello everyone, I'm Dr. Sarah Johnson from Stanford University. Today we'll discuss the revolutionary AI breakthrough in healthcare.",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 8.0,
            "end": 15.0,
            "text": "Our research team at Stanford has developed an AI system that can diagnose cancer with 95% accuracy using medical imaging.",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 15.0,
            "end": 22.0,
            "text": "That's incredible, Dr. Johnson! I'm John Smith from TechCorp Inc. We're very interested in partnering with Stanford on this project.",
            "speaker": "SPEAKER_01"
        },
        {
            "start": 22.0,
            "end": 30.0,
            "text": "We believe this technology could save thousands of lives and generate revenue of $100 million annually by 2025.",
            "speaker": "SPEAKER_01"
        },
        {
            "start": 30.0,
            "end": 38.0,
            "text": "I'm excited about this collaboration! However, we need to address regulatory compliance and patient privacy concerns first.",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 38.0,
            "end": 45.0,
            "text": "Absolutely. We should schedule a meeting next Friday at 2:00 PM to discuss the details. You can reach me at john.smith@techcorp.com.",
            "speaker": "SPEAKER_01"
        }
    ]
    
    # Create graph data structure
    graph_data = {
        "job_id": "test-llm-001",
        "audio_file_id": "llm-sample-001",
        "language": "en",
        "segments": sample_segments
    }
    
    try:
        # Import the graph processor
        from app.core.graph_processor import graph_processor
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        print("📊 Processing complex text data with LLM capabilities...")
        print(f"📋 Graph data: {json.dumps(graph_data, indent=2)}")
        
        # Display current configuration
        print(f"\n🔧 Configuration:")
        print(f"   Graph enabled: {settings.graph.enabled}")
        print(f"   Entity extraction method: {settings.graph.entity_extraction_method}")
        print(f"   Topic extraction method: {settings.graph.topic_extraction_method}")
        print(f"   Sentiment analysis enabled: {settings.graph.sentiment_analysis_enabled}")
        print(f"   Relationship extraction method: {settings.graph.relationship_extraction_method}")
        print(f"   LLM provider: {settings.graph.llm_provider}")
        print(f"   LLM model: {settings.graph.llm_model}")
        
        # Test individual LLM components if configured
        await test_individual_llm_components(sample_segments)
        
        # Process the text data with graph processor
        print(f"\n🚀 Running full graph processing pipeline...")
        result = await graph_processor.process_transcription_result(graph_data)
        
        print("✅ Graph processing completed!")
        print(f"📈 Result summary: {json.dumps(result, indent=2)}")
        
        # Test querying the enhanced graph
        print(f"\n🔍 Testing enhanced graph queries...")
        await test_enhanced_graph_queries()
        
    except Exception as e:
        print(f"❌ Error during LLM graph processing: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_llm_components(segments):
    """Test individual LLM components if they're available."""
    try:
        from app.core.llm_graph_processors import LLMGraphProcessorFactory
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        # Test entity extraction
        if settings.graph.entity_extraction_method == "llm_based":
            print(f"\n🧠 Testing LLM Entity Extraction...")
            try:
                entity_extractor = LLMGraphProcessorFactory.create_entity_extractor(settings)
                sample_text = segments[0]["text"]
                entities = await entity_extractor.extract_entities(sample_text)
                print(f"   Entities found: {entities}")
            except Exception as e:
                print(f"   ⚠️  LLM Entity extraction not available: {e}")
        
        # Test topic modeling
        if settings.graph.topic_extraction_method == "llm_based":
            print(f"\n🧠 Testing LLM Topic Modeling...")
            try:
                topic_modeler = LLMGraphProcessorFactory.create_topic_modeler(settings)
                sample_text = segments[1]["text"]
                topics = await topic_modeler.extract_topics(sample_text)
                print(f"   Topics found: {topics}")
            except Exception as e:
                print(f"   ⚠️  LLM Topic modeling not available: {e}")
        
        # Test sentiment analysis
        if settings.graph.sentiment_analysis_enabled:
            print(f"\n🧠 Testing LLM Sentiment Analysis...")
            try:
                sentiment_analyzer = LLMGraphProcessorFactory.create_sentiment_analyzer(settings)
                sample_text = segments[4]["text"]  # Excited text
                sentiment = await sentiment_analyzer.analyze_sentiment(sample_text)
                print(f"   Sentiment: {sentiment}")
            except Exception as e:
                print(f"   ⚠️  LLM Sentiment analysis not available: {e}")
        
        # Test relationship extraction
        if settings.graph.relationship_extraction_method == "llm_based":
            print(f"\n🧠 Testing LLM Relationship Extraction...")
            try:
                relationship_extractor = LLMGraphProcessorFactory.create_relationship_extractor(settings)
                sample_text = segments[2]["text"]
                entities = ["Dr. Johnson", "John Smith", "TechCorp Inc", "Stanford"]
                relationships = await relationship_extractor.extract_relationships(sample_text, entities)
                print(f"   Relationships found: {relationships}")
            except Exception as e:
                print(f"   ⚠️  LLM Relationship extraction not available: {e}")
                
    except Exception as e:
        print(f"   ⚠️  LLM components not available: {e}")


async def test_enhanced_graph_queries():
    """Test querying the enhanced graph with LLM-extracted data."""
    try:
        from app.db.graph_session import get_graph_db_manager
        
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()
        
        print(f"\n📊 Enhanced Graph Statistics:")
        
        # Check for entities with types
        entity_query = """
        MATCH (e:Entity)
        RETURN e.entity_type as type, count(e) as count
        ORDER BY count DESC
        """
        entity_result = await manager.execute_read_transaction(entity_query)
        print(f"   Entity types:")
        for record in entity_result:
            print(f"     {record['type']}: {record['count']}")
        
        # Check for sentiment data (if available)
        sentiment_query = """
        MATCH (s:TranscriptSegment)
        WHERE s.sentiment IS NOT NULL
        RETURN s.sentiment as sentiment, count(s) as count
        ORDER BY count DESC
        """
        sentiment_result = await manager.execute_read_transaction(sentiment_query)
        if sentiment_result:
            print(f"   Sentiment distribution:")
            for record in sentiment_result:
                print(f"     {record['sentiment']}: {record['count']}")
        else:
            print(f"   No sentiment data found")
        
        # Show some sample extracted entities
        sample_entities_query = """
        MATCH (e:Entity)
        RETURN e.text as entity, e.entity_type as type, e.confidence_score as confidence
        ORDER BY e.confidence_score DESC
        LIMIT 5
        """
        entities_result = await manager.execute_read_transaction(sample_entities_query)
        print(f"   Sample entities:")
        for record in entities_result:
            print(f"     {record['entity']} ({record['type']}) - confidence: {record['confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ Error querying enhanced graph: {e}")


def print_configuration_help():
    """Print help on how to configure LLM providers."""
    print(f"\n💡 LLM Configuration Help:")
    print(f"=" * 30)
    print(f"To enable LLM-based graph processing, set these environment variables:")
    print(f"")
    print(f"For OpenRouter:")
    print(f"  export GRAPH_LLM_PROVIDER=openrouter")
    print(f"  export GRAPH_LLM_MODEL=openai/gpt-3.5-turbo")
    print(f"  export OPENROUTER_API_KEY=your_key_here")
    print(f"")
    print(f"For OpenAI:")
    print(f"  export GRAPH_LLM_PROVIDER=openai")
    print(f"  export GRAPH_LLM_MODEL=gpt-3.5-turbo")
    print(f"  export OPENAI_API_KEY=your_key_here")
    print(f"")
    print(f"For Anthropic:")
    print(f"  export GRAPH_LLM_PROVIDER=anthropic")
    print(f"  export GRAPH_LLM_MODEL=claude-3-haiku-20240307")
    print(f"  export ANTHROPIC_API_KEY=your_key_here")
    print(f"")
    print(f"Enable LLM processing methods:")
    print(f"  export GRAPH_ENTITY_EXTRACTION_METHOD=llm_based")
    print(f"  export GRAPH_TOPIC_EXTRACTION_METHOD=llm_based")
    print(f"  export GRAPH_SENTIMENT_ANALYSIS_ENABLED=true")
    print(f"  export GRAPH_RELATIONSHIP_EXTRACTION_METHOD=llm_based")


if __name__ == "__main__":
    print_configuration_help()
    asyncio.run(test_llm_graph_processing())
