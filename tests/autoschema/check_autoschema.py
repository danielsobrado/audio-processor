#!/usr/bin/env python3
"""
Quick test to check AutoSchemaKG availability
"""
import sys
import os

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

try:
    import sentence_transformers
    print("✅ sentence_transformers available")
except ImportError as e:
    print(f"❌ sentence_transformers not available: {e}")

try:
    from atlas_rag.kg_construction.autoschema_kg import AutoSchemaKG
    print("✅ AutoSchemaKG available")
except ImportError as e:
    print(f"❌ AutoSchemaKG not available: {e}")

try:
    from atlas_rag.llm_generator.openai import OpenAIProvider
    print("✅ OpenAIProvider available")
except ImportError as e:
    print(f"❌ OpenAIProvider not available: {e}")

# Test basic functionality
try:
    # Create AutoSchemaKG instance
    kg = AutoSchemaKG()
    print("✅ AutoSchemaKG instance created successfully")

    # Test with sample text
    sample_text = "John works at Microsoft. He loves programming in Python."
    result = kg.extract_knowledge_graph(sample_text)
    print(f"✅ Knowledge graph extraction successful: {len(result.get('entities', []))} entities, {len(result.get('relationships', []))} relationships")

except Exception as e:
    print(f"❌ AutoSchemaKG test failed: {e}")

print("🎉 AutoSchemaKG check completed!")
