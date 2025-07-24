#!/usr/bin/env python3
"""
Check what files are actually created by the API
"""
import os
import requests

def check_output_directory(output_dir):
    """Check what files exist in the output directory"""
    print(f"\n🔍 Checking output directory: {output_dir}")

    if not os.path.exists(output_dir):
        print("❌ Output directory does not exist!")
        return

    print("📁 Directory structure:")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{subindent}{file} ({file_size} bytes)")

            # Show content of small JSON files
            if file_size < 5000 and file.endswith(('.json', '.csv')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"{subindent}  Content preview: {content[:200]}...")
                except Exception as e:
                    print(f"{subindent}  Error reading file: {e}")

# Simple test text
sample_text = """Dr. Sarah Johnson works at TechCorp. TechCorp was founded by Michael Zhang."""

print("🔍 Testing API extraction with file output check")
print("=" * 60)

# Run extraction
url = "http://localhost:8000/api/v1/autoschema-kg/extract"
data = {
    "text_data": sample_text,
    "batch_size_triple": 1,
    "batch_size_concept": 1,
    "max_new_tokens": 512,
    "max_workers": 1
}

print(f"🚀 Running extraction via API...")
print(f"📄 Text: {sample_text}")

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print(f"✅ API call successful!")
    print(f"📊 Job ID: {result['job_id']}")
    print(f"📊 Node count: {result['node_count']}")
    print(f"📊 Edge count: {result['edge_count']}")
    print(f"📊 Concept count: {result['concept_count']}")
    print(f"📁 Output directory: {result['output_directory']}")

    # Check what files were actually created
    check_output_directory(result['output_directory'])

else:
    print(f"❌ API call failed: {response.status_code}")
    print(f"Error: {response.text}")

print("\\n🎉 File check completed!")
