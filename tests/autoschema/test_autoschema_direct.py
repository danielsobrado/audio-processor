#!/usr/bin/env python3
"""
Direct test of AutoSchemaKG functionality
"""
import sys
import os
import tempfile
import json

# Ensure .env file is loaded
from dotenv import load_dotenv
load_dotenv()

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

try:
    # Import required libraries
    from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
    from atlas_rag.kg_construction.triple_config import ProcessingConfig
    from atlas_rag.llm_generator.llm_generator import LLMGenerator
    from openai import OpenAI
    from app.config.settings import get_settings

    print("🧪 AutoSchemaKG Direct Test")
    print("=" * 50)

    # Get settings
    settings = get_settings()

    # Debug: Check settings
    print(f"🔍 Debug - Graph LLM Provider: {settings.graph.llm_provider}")
    print(f"🔍 Debug - Graph LLM Model: {settings.graph.llm_model}")
    print(f"🔍 Debug - Graph LLM API Key: {'***' + settings.graph.llm_api_key[-10:] if settings.graph.llm_api_key else 'None'}")

    # Also check environment variable directly
    import os
    env_api_key = os.getenv("GRAPH_LLM_API_KEY")
    print(f"🔍 Debug - ENV GRAPH_LLM_API_KEY: {'***' + env_api_key[-10:] if env_api_key else 'None'}")

    # Sample text
    sample_text = """
    John Smith works as a senior software engineer at Microsoft Corporation in Seattle, Washington.
    He has been developing applications using Python and JavaScript for over 8 years.
    John graduated from Stanford University with a degree in Computer Science in 2015.
    Microsoft is a leading technology company founded by Bill Gates and Paul Allen in 1975.

    Sarah Chen joined Google LLC in Mountain View, California as a data scientist in 2020.
    She previously worked at Amazon Web Services for 3 years, specializing in machine learning algorithms.
    Sarah holds a PhD in Artificial Intelligence from MIT, which she completed in 2017.
    Her research focuses on natural language processing and computer vision applications.

    David Rodriguez serves as Chief Technology Officer at Tesla Inc., based in Austin, Texas.
    He started his career at SpaceX in 2012 as a propulsion engineer.
    David earned his Master's degree in Aerospace Engineering from Caltech in 2011.
    Tesla was founded by Elon Musk in 2003 and is headquartered in Austin since 2021.

    Lisa Wang is a product manager at Apple Inc. in Cupertino, California.
    She graduated from Harvard Business School with an MBA in 2019.
    Prior to Apple, Lisa worked at Facebook (now Meta) for 4 years in Menlo Park.
    Apple was established by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.

    Michael Brown currently works as a cybersecurity analyst at IBM in Armonk, New York.
    He has 12 years of experience in information security and ethical hacking.
    Michael obtained his Bachelor's degree in Computer Engineering from Carnegie Mellon University in 2010.
    IBM was founded in 1911 and has been a pioneer in computer technology for over a century.

    Jennifer Lopez is a blockchain developer at Coinbase in San Francisco, California.
    She specializes in smart contract development using Solidity and Rust programming languages.
    Jennifer graduated from UC Berkeley with a degree in Mathematics and Computer Science in 2018.
    Coinbase was founded by Brian Armstrong and Fred Ehrsam in 2012.

    Robert Kim works as a DevOps engineer at Netflix in Los Gatos, California.
    He has expertise in cloud infrastructure management using AWS and Kubernetes.
    Robert completed his studies at University of Washington in Seattle, earning a BS in Information Systems in 2016.
    Netflix was founded by Reed Hastings and Marc Randolph in 1997.

    Emily Davis is employed as a UX designer at Adobe Systems in San Jose, California.
    She has been creating user interfaces for mobile and web applications for 6 years.
    Emily holds a Master's degree in Human-Computer Interaction from Georgia Tech, completed in 2017.
    Adobe was founded by John Warnock and Charles Geschke in 1982.

    Tom Wilson serves as a database administrator at Oracle Corporation in Redwood City, California.
    He manages enterprise databases and has 15 years of experience with SQL and NoSQL systems.
    Tom graduated from University of Texas at Austin with a degree in Management Information Systems in 2008.
    Oracle was established by Larry Ellison, Bob Miner, and Ed Oates in 1977.

    Anna Petrov works as a research scientist at NVIDIA in Santa Clara, California.
    She focuses on deep learning frameworks and GPU computing optimization.
    Anna earned her PhD in Computer Science from Stanford University in 2019.
    NVIDIA was founded by Jensen Huang, Chris Malachowsky, and Curtis Priem in 1993.

    The technology industry in Silicon Valley employs over 400,000 people as of 2024.
    Major companies like Google, Apple, Facebook, and Netflix have their headquarters in the San Francisco Bay Area.
    The region is known for its innovation in artificial intelligence, cloud computing, and semiconductor technology.
    Venture capital firms such as Sequoia Capital and Andreessen Horowitz are also based in this area.

    Stanford University and UC Berkeley are two prestigious institutions that supply talent to tech companies.
    Many entrepreneurs and engineers have graduated from these universities and founded successful startups.
    The collaboration between academia and industry has been crucial for technological advancement in the region.

    Programming languages like Python, JavaScript, Java, and C++ are widely used in software development.
    Cloud platforms including Amazon Web Services, Microsoft Azure, and Google Cloud Platform dominate the market.
    Artificial intelligence and machine learning have become essential skills for modern software engineers.
    Agile development methodologies and DevOps practices are standard in most technology companies.
    """

    print(f"📄 Sample text: {sample_text[:100]}...")

    # Test with API key if available
    if settings.graph.llm_api_key and settings.graph.llm_api_key != "":
        print("✅ API key found, testing knowledge graph extraction...")

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
        import tempfile

        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Create processing config
        config = ProcessingConfig(
            model_path=settings.graph.llm_model,
            data_directory=data_dir,
            filename_pattern="test",
            batch_size_triple=2,
            batch_size_concept=4,
            output_directory=temp_dir,
            max_new_tokens=1024,
            max_workers=1,
            remove_doc_spaces=True,
        )

        # Create knowledge graph extractor
        kg_extractor = KnowledgeGraphExtractor(llm_generator, config)

        # Test with a real extraction attempt
        try:
            print("🔍 Testing REAL knowledge graph extraction...")

            # Create proper JSONL input file with 'id', 'text', and 'metadata' fields
            input_file = os.path.join(data_dir, "test.jsonl")
            with open(input_file, 'w', encoding='utf-8') as f:
                # Each line should be a JSON object with id, text, and metadata fields
                json_line = {
                    "id": "sample_1",
                    "text": sample_text.strip(),
                    "metadata": {"source": "test", "timestamp": "2025-01-22", "type": "business_text"}
                }
                f.write(json.dumps(json_line) + '\n')

            print(f"📁 Created input file: {input_file}")
            print(f"📊 File size: {os.path.getsize(input_file)} bytes")

            # Now attempt the real extraction
            print("⚡ Starting REAL knowledge graph extraction...")
            print("   This will call the OpenRouter API and may take 1-2 minutes...")

            try:
                # This is the real extraction call
                kg_extractor.run_extraction()
                print("✅ Knowledge graph extraction completed successfully!")

                # Check output directory for results
                output_files = []
                if os.path.exists(config.output_directory):
                    for root, dirs, files in os.walk(config.output_directory):
                        for file in files:
                            if file.endswith('.csv'):
                                output_files.append(os.path.join(root, file))

                print(f"\n📊 Extraction Results:")
                print(f"   📁 Output directory: {config.output_directory}")
                print(f"   📄 CSV files generated: {len(output_files)}")

                # Show actual results from CSV files
                entities_count = 0
                relationships_count = 0
                concepts_count = 0

                for csv_file in output_files:
                    filename = os.path.basename(csv_file).lower()
                    try:
                        import pandas as pd
                        df = pd.read_csv(csv_file)
                        row_count = len(df)

                        if 'node' in filename or 'entity' in filename:
                            entities_count += row_count
                            print(f"   📋 Entities ({filename}): {row_count} rows")
                            if row_count > 0:
                                print(f"      Sample: {df.head(3).to_string(index=False)}")
                        elif 'edge' in filename or 'relation' in filename:
                            relationships_count += row_count
                            print(f"   🔗 Relationships ({filename}): {row_count} rows")
                            if row_count > 0:
                                print(f"      Sample: {df.head(3).to_string(index=False)}")
                        elif 'concept' in filename:
                            concepts_count += row_count
                            print(f"   💡 Concepts ({filename}): {row_count} rows")
                            if row_count > 0:
                                print(f"      Sample: {df.head(3).to_string(index=False)}")
                    except Exception as e:
                        print(f"   ⚠️ Could not read {filename}: {e}")

                print(f"\n🎯 REAL Extraction Summary:")
                print(f"   📊 Total Entities: {entities_count}")
                print(f"   🔗 Total Relationships: {relationships_count}")
                print(f"   💡 Total Concepts: {concepts_count}")

                if entities_count > 0 or relationships_count > 0:
                    print("\n✅ REAL AutoSchemaKG extraction successful!")
                    print("💡 You can now load this data into Neo4j using:")
                    print(f"   /api/v1/autoschema-kg/load-to-neo4j endpoint")
                else:
                    print("\n⚠️ No entities or relationships extracted. This might be due to:")
                    print("   1. Text too short or simple")
                    print("   2. Model not extracting from this specific content")
                    print("   3. Extraction parameters need adjustment")

            except Exception as extraction_error:
                print(f"❌ REAL extraction failed: {extraction_error}")
                import traceback
                traceback.print_exc()

                # Fall back to showing what we expected to extract
                print("\n📋 Expected extractions from this text would include:")
                print("   📊 Entities: John Smith, Microsoft, Seattle, Sarah Chen, Google, etc.")
                print("   🔗 Relationships: works_at, located_in, graduated_from, etc.")
                print("   💡 Concepts: Employment, Education, Technology, etc.")

        except Exception as e:
            print(f"❌ Extraction test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ No API key found - skipping LLM tests")
        print("💡 Set GRAPH_LLM_API_KEY in .env to test with real LLM")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Make sure all dependencies are installed")

print("\n🎉 Direct test completed!")
