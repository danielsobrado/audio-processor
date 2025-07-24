#!/usr/bin/env python3
"""
Patched AutoSchemaKG test that handles datetime serialization
"""
import sys
import os
import tempfile
import json
from datetime import datetime

# Ensure .env file is loaded
from dotenv import load_dotenv
load_dotenv()

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Monkey patch the json.dumps function to use our custom encoder
original_dumps = json.dumps
def patched_dumps(obj, *args, **kwargs):
    kwargs.setdefault('cls', DateTimeEncoder)
    return original_dumps(obj, *args, **kwargs)

json.dumps = patched_dumps

try:
    # Import required libraries
    from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
    from atlas_rag.kg_construction.triple_config import ProcessingConfig
    from atlas_rag.llm_generator.llm_generator import LLMGenerator
    from openai import OpenAI
    from app.config.settings import get_settings

    print("🧪 AutoSchemaKG Real Extraction Test (Patched)")
    print("=" * 60)

    # Get settings
    settings = get_settings()

    # Debug: Check settings
    print(f"🔍 Graph LLM Provider: {settings.graph.llm_provider}")
    print(f"🔍 Graph LLM Model: {settings.graph.llm_model}")
    print(f"🔍 API Key: {'***' + settings.graph.llm_api_key[-10:] if settings.graph.llm_api_key else 'None'}")

    # Sample text - keeping it shorter for faster processing
    sample_text = """
    John Smith works as a senior software engineer at Microsoft Corporation in Seattle, Washington.
    He has been developing applications using Python and JavaScript for over 8 years.
    John graduated from Stanford University with a degree in Computer Science in 2015.
    Microsoft is a leading technology company founded by Bill Gates and Paul Allen in 1975.

    Sarah Chen joined Google LLC in Mountain View, California as a data scientist in 2020.
    She previously worked at Amazon Web Services for 3 years, specializing in machine learning algorithms.
    Sarah holds a PhD in Artificial Intelligence from MIT, which she completed in 2017.
    Her research focuses on natural language processing and computer vision applications.
    """

    print(f"📄 Sample text length: {len(sample_text)} characters")

    # Test with API key if available
    if settings.graph.llm_api_key and settings.graph.llm_api_key != "":
        print("✅ API key found, starting real extraction...")

        # Create OpenRouter client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.graph.llm_api_key,
        )

        # Create LLM Generator
        llm_generator = LLMGenerator(
            client=client,
            model_name=settings.graph.llm_model
        )

        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        print(f"📁 Working directory: {temp_dir}")

        # Create processing config with smaller batches for testing
        config = ProcessingConfig(
            model_path=settings.graph.llm_model,
            data_directory=data_dir,
            filename_pattern="test",
            batch_size_triple=1,  # Smaller batch for testing
            batch_size_concept=2,
            output_directory=temp_dir,
            max_new_tokens=512,  # Smaller token limit for faster processing
            max_workers=1,
            remove_doc_spaces=True,
        )

        # Create knowledge graph extractor
        kg_extractor = KnowledgeGraphExtractor(llm_generator, config)

        try:
            print("🔍 Creating input file...")

            # Create proper JSONL input file
            input_file = os.path.join(data_dir, "test.jsonl")
            with open(input_file, 'w', encoding='utf-8') as f:
                json_line = {
                    "id": "sample_1",
                    "text": sample_text.strip(),
                    "metadata": {"source": "test", "timestamp": "2025-01-22", "type": "business_text"}
                }
                f.write(json.dumps(json_line) + '\n')

            print(f"✅ Input file created: {os.path.getsize(input_file)} bytes")

            # Run the real extraction
            print("⚡ Starting REAL AutoSchemaKG extraction...")
            print("   🤖 This will call OpenRouter API...")
            print("   ⏱️ Estimated time: 30-60 seconds")
            print("")

            # This is the actual extraction
            kg_extractor.run_extraction()

            print("\n✅ Knowledge graph extraction completed!")

            # Check and display results
            output_files = []
            if os.path.exists(config.output_directory):
                for root, dirs, files in os.walk(config.output_directory):
                    for file in files:
                        if file.endswith('.csv'):
                            output_files.append(os.path.join(root, file))

            print(f"\n📊 Results Analysis:")
            print(f"   📁 Output directory: {config.output_directory}")
            print(f"   📄 CSV files created: {len(output_files)}")

            if output_files:
                print("\n📋 Generated Files:")
                for csv_file in output_files:
                    filename = os.path.basename(csv_file)
                    size = os.path.getsize(csv_file)
                    print(f"   • {filename} ({size} bytes)")

            # Analyze the actual extracted data
            total_entities = 0
            total_relationships = 0
            total_concepts = 0

            for csv_file in output_files:
                filename = os.path.basename(csv_file).lower()
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_file)
                    row_count = len(df)

                    print(f"\n📄 {filename.upper()}:")
                    print(f"   Rows: {row_count}")

                    if row_count > 0:
                        print(f"   Columns: {list(df.columns)}")
                        print(f"   Sample data:")
                        for idx, (i, row) in enumerate(df.head(3).iterrows()):
                            print(f"      {idx+1}: {dict(row)}")

                    if 'node' in filename or 'entity' in filename:
                        total_entities += row_count
                    elif 'edge' in filename or 'relation' in filename:
                        total_relationships += row_count
                    elif 'concept' in filename:
                        total_concepts += row_count

                except Exception as e:
                    print(f"   ⚠️ Error reading {filename}: {e}")

            print(f"\n🎯 FINAL RESULTS:")
            print(f"   📊 Entities extracted: {total_entities}")
            print(f"   🔗 Relationships extracted: {total_relationships}")
            print(f"   💡 Concepts extracted: {total_concepts}")

            if total_entities > 0 or total_relationships > 0:
                print(f"\n🎉 SUCCESS! AutoSchemaKG extracted real knowledge graph data!")
                print(f"💡 Next steps:")
                print(f"   1. Load into Neo4j: /api/v1/autoschema-kg/load-to-neo4j")
                print(f"   2. Query in Neo4j Browser: http://localhost:7474")
                print(f"   3. Visualize the knowledge graph")
            else:
                print(f"\n⚠️ No entities or relationships were extracted.")
                print(f"💡 This could be due to:")
                print(f"   • Model interpretation of the text")
                print(f"   • Extraction prompts/parameters")
                print(f"   • Text complexity")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            import shutil
            try:
                shutil.rmtree(temp_dir)
                print(f"\n🧹 Cleaned up temporary directory")
            except:
                pass

    else:
        print("⚠️ No API key found")
        print("💡 Set GRAPH_LLM_API_KEY environment variable")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Make sure all dependencies are installed")

print("\n🎉 AutoSchemaKG test completed!")
