#!/usr/bin/env python3
"""
Test script to demonstrate LLM-based graph processing capabilities.
"""

import asyncio
import json
import os
from typing import Dict

# Set up environment variables for testing
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "devpassword")
os.environ.setdefault("GRAPH_ENABLED", "true")

# LLM Configuration examples:
# For OpenAI:
# os.environ.setdefault("GRAPH_LLM_PROVIDER", "openai")
# os.environ.setdefault("GRAPH_LLM_MODEL", "gpt-3.5-turbo")
# os.environ.setdefault("GRAPH_LLM_API_KEY", "your-openai-api-key")

# For Anthropic:
# os.environ.setdefault("GRAPH_LLM_PROVIDER", "anthropic")
# os.environ.setdefault("GRAPH_LLM_MODEL", "claude-3-haiku-20240307")
# os.environ.setdefault("GRAPH_LLM_API_KEY", "your-anthropic-api-key")

# For Local LLM (Ollama, etc.):
# os.environ.setdefault("GRAPH_LLM_PROVIDER", "local")
# os.environ.setdefault("GRAPH_LLM_MODEL", "llama2")
# os.environ.setdefault("GRAPH_LLM_API_BASE", "http://localhost:11434")

# Configure extraction methods
os.environ.setdefault(
    "GRAPH_ENTITY_EXTRACTION_METHOD", "hybrid"
)  # regex_patterns, llm_based, hybrid
os.environ.setdefault(
    "GRAPH_TOPIC_EXTRACTION_METHOD", "hybrid"
)  # keyword_matching, llm_based, hybrid
os.environ.setdefault("GRAPH_SENTIMENT_ANALYSIS_ENABLED", "false")  # true, false
os.environ.setdefault(
    "GRAPH_RELATIONSHIP_EXTRACTION_METHOD", "rule_based"
)  # rule_based, llm_based, hybrid


async def test_llm_graph_processing():
    """Test LLM-based graph processing capabilities."""
    print("🤖 Testing LLM-Based Graph Processing")
    print("=" * 50)

    # Sample conversation with richer content for LLM processing
    sample_segments = [
        {
            "start": 0.0,
            "end": 8.0,
            "text": "Good morning everyone! I'm Dr. Sarah Johnson from Stanford University. Today we'll discuss our AI research breakthrough in medical diagnosis.",
            "speaker": "SPEAKER_00",
        },
        {
            "start": 8.0,
            "end": 15.0,
            "text": "That sounds fascinating, Dr. Johnson! I'm really excited to hear about this. Could you tell us about the specific applications?",
            "speaker": "SPEAKER_01",
        },
        {
            "start": 15.0,
            "end": 25.0,
            "text": "Absolutely! Our deep learning model can analyze chest X-rays and detect pneumonia with 95% accuracy. We've tested it on over 10,000 patients at Stanford Medical Center.",
            "speaker": "SPEAKER_00",
        },
        {
            "start": 25.0,
            "end": 32.0,
            "text": "Wow, that's incredible! What about the cost? I imagine this could save hospitals millions of dollars in diagnostic costs.",
            "speaker": "SPEAKER_01",
        },
        {
            "start": 32.0,
            "end": 42.0,
            "text": "You're absolutely right! Our preliminary analysis shows potential savings of $2.5 million annually per hospital. We're planning to publish these results in Nature Medicine next month.",
            "speaker": "SPEAKER_00",
        },
        {
            "start": 42.0,
            "end": 48.0,
            "text": "This is groundbreaking work! When do you expect this technology to be available to other medical institutions?",
            "speaker": "SPEAKER_01",
        },
        {
            "start": 48.0,
            "end": 58.0,
            "text": "We're currently in discussions with the FDA for approval. If everything goes smoothly, we hope to begin pilot programs at partner hospitals by January 2026.",
            "speaker": "SPEAKER_00",
        },
    ]

    # Create graph data structure
    graph_data = {
        "job_id": "test-llm-processing-001",
        "audio_file_id": "llm-sample-001",
        "language": "en",
        "segments": sample_segments,
    }

    try:
        from app.config.settings import get_settings
        from app.core.graph_processor import graph_processor

        settings = get_settings()

        print("🔧 Configuration:")
        print(f"   Graph enabled: {settings.graph.enabled}")
        print(f"   Entity extraction method: {settings.graph.entity_extraction_method}")
        print(f"   Topic extraction method: {settings.graph.topic_extraction_method}")
        print(
            f"   Sentiment analysis enabled: {settings.graph.sentiment_analysis_enabled}"
        )
        print(
            f"   Relationship extraction method: {settings.graph.relationship_extraction_method}"
        )
        print(f"   LLM provider: {settings.graph.llm_provider}")
        print(f"   LLM model: {settings.graph.llm_model}")
        print("")

        # Test individual LLM processors if configured
        if settings.graph.entity_extraction_method in ["llm_based", "hybrid"]:
            print("🧠 Testing LLM Entity Extraction...")
            try:
                if graph_processor.llm_entity_extractor:
                    test_text = "Dr. Sarah Johnson from Stanford University will publish in Nature Medicine about $2.5 million in savings."
                    entities = (
                        await graph_processor.llm_entity_extractor.extract_entities(
                            test_text
                        )
                    )
                    print(f"   Entities found: {entities}")
                else:
                    print("   LLM entity extractor not initialized (check API key)")
            except Exception as e:
                print(f"   ❌ LLM entity extraction failed: {e}")

        if settings.graph.topic_extraction_method in ["llm_based", "hybrid"]:
            print("🧠 Testing LLM Topic Modeling...")
            try:
                if graph_processor.llm_topic_modeler:
                    test_text = "Our AI research breakthrough in medical diagnosis using deep learning for chest X-ray analysis"
                    topics = await graph_processor.llm_topic_modeler.extract_topics(
                        test_text
                    )
                    print(f"   Topics found: {topics}")
                else:
                    print("   LLM topic modeler not initialized (check API key)")
            except Exception as e:
                print(f"   ❌ LLM topic modeling failed: {e}")

        if settings.graph.sentiment_analysis_enabled:
            print("🧠 Testing LLM Sentiment Analysis...")
            try:
                if graph_processor.llm_sentiment_analyzer:
                    test_text = "That sounds fascinating! I'm really excited to hear about this incredible breakthrough!"
                    sentiment = (
                        await graph_processor.llm_sentiment_analyzer.analyze_sentiment(
                            test_text
                        )
                    )
                    print(f"   Sentiment: {sentiment}")
                else:
                    print("   LLM sentiment analyzer not initialized (check API key)")
            except Exception as e:
                print(f"   ❌ LLM sentiment analysis failed: {e}")

        print("\n📊 Processing full conversation with LLM capabilities...")
        print(f"📋 Graph data: {json.dumps(graph_data, indent=2)}")

        # Process the conversation
        result = await graph_processor.process_transcription_result(graph_data)

        print("✅ LLM-based graph processing completed!")
        print(f"📈 Result summary: {json.dumps(result, indent=2)}")

        # Test the new processing strategies
        print("\n🎭 Testing Sentiment Analysis Strategy...")
        await test_sentiment_strategy(graph_data)

        print("\n🔍 Testing Keyword Spotting Strategy...")
        await test_keyword_spotting_strategy(graph_data)

    except Exception as e:
        print(f"❌ Error during LLM graph processing: {e}")
        import traceback

        traceback.print_exc()


async def test_sentiment_strategy(graph_data: dict):
    """Test the sentiment analysis strategy."""
    try:
        from app.core.processing_strategies import (
            ProcessingContext,
            SentimentAnalysisStrategy,
        )

        # Create processing context
        context = ProcessingContext(
            request_data={"request_id": "test-sentiment"}, audio_path=None
        )
        context.processing_result = graph_data

        # Run sentiment analysis strategy
        strategy = SentimentAnalysisStrategy()
        result_context = await strategy.process(context)

        if not result_context.is_failed() and result_context.processing_result:
            print("   ✅ Sentiment analysis strategy completed successfully")
            # Show sentiment for first few segments
            for i, segment in enumerate(
                result_context.processing_result["segments"][:3]
            ):
                sentiment = segment.get("sentiment", {})
                print(
                    f"   Segment {i+1}: {sentiment.get('sentiment', 'unknown')} (confidence: {sentiment.get('confidence', 0)})"
                )
        else:
            print(f"   ❌ Sentiment analysis strategy failed: {result_context.error}")

    except Exception as e:
        print(f"   ❌ Error testing sentiment strategy: {e}")


async def test_keyword_spotting_strategy(graph_data: dict):
    """Test the keyword spotting strategy."""
    try:
        from app.core.processing_strategies import (
            KeywordSpottingStrategy,
            ProcessingContext,
        )

        # Create processing context
        context = ProcessingContext(
            request_data={"request_id": "test-keywords"}, audio_path=None
        )
        context.processing_result = graph_data

        # Run keyword spotting strategy
        strategy = KeywordSpottingStrategy()
        result_context = await strategy.process(context)

        if not result_context.is_failed() and result_context.processing_result:
            print("   ✅ Keyword spotting strategy completed successfully")
            # Show entities and topics for first few segments
            for i, segment in enumerate(
                result_context.processing_result["segments"][:3]
            ):
                entities = segment.get("entities", [])
                topics = segment.get("topics", [])
                print(
                    f"   Segment {i+1}: {len(entities)} entities, {len(topics)} topics"
                )
        else:
            print(f"   ❌ Keyword spotting strategy failed: {result_context.error}")

    except Exception as e:
        print(f"   ❌ Error testing keyword spotting strategy: {e}")


if __name__ == "__main__":
    print("🌟 Audio Processor LLM Graph Testing Suite")
    print("=" * 60)
    print("📝 To enable LLM processing, set environment variables:")
    print("   GRAPH_LLM_PROVIDER=openai (or anthropic, local)")
    print("   GRAPH_LLM_API_KEY=your-api-key")
    print("   GRAPH_ENTITY_EXTRACTION_METHOD=llm_based")
    print("   GRAPH_TOPIC_EXTRACTION_METHOD=llm_based")
    print("   GRAPH_SENTIMENT_ANALYSIS_ENABLED=true")
    print("=" * 60)
    print()

    asyncio.run(test_llm_graph_processing())
