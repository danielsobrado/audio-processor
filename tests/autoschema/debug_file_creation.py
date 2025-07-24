#!/usr/bin/env python3
"""
Debug script to check what files are created during AutoSchemaKG extraction
"""
import os
import tempfile
import requests
import time

def list_directory_contents(directory, title="Directory contents"):
    """List all files and subdirectories recursively"""
    print(f"\n{title}: {directory}")
    print("=" * 60)

    if not os.path.exists(directory):
        print("Directory does not exist!")
        return

    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{subindent}{file} ({file_size} bytes)")

def check_file_content(file_path, max_lines=10):
    """Check the content of a file"""
    try:
        print(f"\n📄 Content of {file_path}:")
        print("-" * 40)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:max_lines]):
                print(f"{i+1:2d}: {line.rstrip()}")
            if len(lines) > max_lines:
                print(f"... and {len(lines) - max_lines} more lines")
    except Exception as e:
        print(f"Error reading file: {e}")

# Create a small test
sample_text = """
Dr. Sarah Johnson works at TechCorp. TechCorp is a company founded by Michael Zhang.
Sarah has a PhD from MIT. MIT is a university in Boston.
"""

print("🔍 Testing AutoSchemaKG file creation")
print("=" * 50)

# Run extraction
url = "http://localhost:8000/api/v1/autoschema-kg/extract"
data = {
    "text_data": sample_text,
    "batch_size_triple": 1,
    "batch_size_concept": 1,
    "max_new_tokens": 512,
    "max_workers": 1
}

print(f"🚀 Running extraction...")
print(f"📄 Text: {sample_text.strip()}")

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    output_dir = result['output_directory']

    print(f"✅ Extraction completed!")
    print(f"📁 Output directory: {output_dir}")

    # List all files created
    list_directory_contents(output_dir, "Files created during extraction")

    # Check specific files if they exist
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(('.json', '.csv')):
                check_file_content(os.path.join(root, file))

else:
    print(f"❌ Extraction failed: {response.status_code}")
    print(f"Error: {response.text}")
