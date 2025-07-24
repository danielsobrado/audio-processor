#!/usr/bin/env python3
"""
Direct test of AutoSchemaKG extraction without the API
"""
import sys
import os
import tempfile
import json
from datetime import datetime

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

print("🧪 Direct AutoSchemaKG Test")
print("=" * 50)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Simple test text
sample_text = """
Dr. Sarah Johnson works at TechCorp. TechCorp is a company founded by Michael Zhang.
Sarah has a PhD from MIT. MIT is a university in Boston.
"""

try:
    from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
    from atlas_rag.kg_construction.triple_config import ProcessingConfig
    from atlas_rag.llm_generator import LLMGenerator

    print("✅ Successfully imported AutoSchemaKG libraries")

    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        json.dump({"id": "test", "text": sample_text, "metadata": {"lang": "en"}}, f)
        f.write('\n')
        input_file = f.name

    # Create temporary output directory
    output_dir = tempfile.mkdtemp(prefix="autoschema_test_")
    data_dir = os.path.dirname(input_file)
    filename_pattern = os.path.basename(input_file).replace('.jsonl', '')

    print(f"📄 Input file: {input_file}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🔍 Pattern: {filename_pattern}")

    # Create LLM generator with OpenRouter
    try:
        from openai import OpenAI

        # Set up OpenRouter client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("GRAPH_LLM_API_KEY"),
        )

        llm_generator = LLMGenerator(
            client=client,
            model_name="meta-llama/llama-3.2-3b-instruct"
        )
        print("✅ LLM Generator created successfully")
    except Exception as e:
        print(f"❌ Failed to create LLM Generator: {e}")
        exit(1)

    # Create processing config
    config = ProcessingConfig(
        model_path="meta-llama/llama-3.2-3b-instruct",
        data_directory=data_dir,
        filename_pattern=filename_pattern,
        output_directory=output_dir,
        batch_size_triple=1,
        batch_size_concept=1,
        max_new_tokens=512,
        max_workers=1,
        debug_mode=True,
        record=False
    )

    print("✅ Configuration created")

    # Create extractor
    extractor = KnowledgeGraphExtractor(model=llm_generator, config=config)
    print("✅ Extractor created")

    # Run extraction step by step
    try:
        print("🚀 Running extraction...")
        extractor.run_extraction()
        print("✅ Extraction completed")

        # List files created
        print("\\n📁 Files created:")
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                print(f"  {file} ({size} bytes)")

                # Show content of small files
                if size < 1000 and file.endswith('.json'):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        print(f"    Content: {content[:200]}...")

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

    # Clean up
    os.unlink(input_file)

except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

print("\\n🎉 Direct test completed!")
