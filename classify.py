"""
VigilDoc Step 2: Documentation Generator (`classify.py`)
Reads ingested raw endpoint JSON objects, prompts LLM/template generator, and outputs markdown guides classified by domain under wiki/.
"""

import os
import sys
import json
import glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from lib.llm_utils import generate_endpoint_documentation

def run_classify():
    base_dir = os.path.dirname(__file__)
    raw_dir = os.path.join(base_dir, 'raw')
    wiki_dir = os.path.join(base_dir, 'wiki')

    latest_file = os.path.join(raw_dir, "latest.json")
    if not os.path.exists(latest_file):
        print("❌ Error: No raw ingestion data found. Run capture.py first.")
        return

    with open(latest_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    timestamp_id = meta['latest_timestamp']
    target_raw_dir = os.path.join(raw_dir, timestamp_id)
    endpoint_files = glob.glob(os.path.join(target_raw_dir, "*.json"))
    endpoint_files = [f for f in endpoint_files if not os.path.basename(f).startswith('_')]

    print(f"📖 Processing {len(endpoint_files)} endpoints from raw/{timestamp_id}/...")

    categories = ["Authentication", "Core Endpoints", "Webhooks", "Data Schemas"]
    for cat in categories:
        os.makedirs(os.path.join(wiki_dir, cat), exist_ok=True)

    generated_docs = []

    for ep_file in endpoint_files:
        with open(ep_file, 'r', encoding='utf-8') as f:
            ep = json.load(f)

        category = ep.get('category', 'Core Endpoints')
        if category not in categories:
            category = 'Core Endpoints'

        doc_md = generate_endpoint_documentation(ep)

        cat_dir = os.path.join(wiki_dir, category)
        target_md_path = os.path.join(cat_dir, f"{ep['id']}.md")

        with open(target_md_path, 'w', encoding='utf-8') as f:
            f.write(doc_md)

        generated_docs.append({
            "id": ep['id'],
            "category": category,
            "path": ep['path'],
            "method": ep['method'],
            "wiki_file": os.path.relpath(target_md_path, wiki_dir)
        })
        print(f"  • [{category}] Synthesized: {ep['method']} {ep['path']} -> {ep['id']}.md")

    # Save wiki index manifest
    with open(os.path.join(wiki_dir, "_wiki_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(generated_docs, f, indent=2)

    print(f"✅ LLM Documentation generation complete! Generated {len(generated_docs)} articles under wiki/.")

if __name__ == '__main__':
    run_classify()
