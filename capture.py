"""
VigilDoc Step 1: Ingestion Engine (`capture.py`)
Parses OpenAPI specs and code router files in docs/, extracting HTTP methods, paths, parameters, docstrings, and schemas into raw/<timestamp_id>/.
"""

import os
import sys
import json
import time
import glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from lib.parser_utils import parse_openapi_spec, parse_python_routes

def run_capture():
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    raw_dir = os.path.join(os.path.dirname(__file__), 'raw')
    
    timestamp_id = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(raw_dir, timestamp_id)
    os.makedirs(output_dir, exist_ok=True)

    all_endpoints = []
    spec_files = glob.glob(os.path.join(docs_dir, "*.*"))

    print(f"🔍 Found {len(spec_files)} API spec/source files in docs/:")
    for filepath in spec_files:
        filename = os.path.basename(filepath)
        print(f"  • Ingesting: {filename}...")
        if filename.endswith('.yaml') or filename.endswith('.yml') or filename.endswith('.json'):
            parsed = parse_openapi_spec(filepath)
            all_endpoints.extend(parsed)
            print(f"    ↳ Parsed {len(parsed)} endpoints")
        elif filename.endswith('.py'):
            parsed = parse_python_routes(filepath)
            all_endpoints.extend(parsed)
            print(f"    ↳ Parsed {len(parsed)} endpoints")

    print(f"\n💾 Saving {len(all_endpoints)} captured endpoint definitions to raw/{timestamp_id}/...")
    manifest = []
    for ep in all_endpoints:
        ep_file = os.path.join(output_dir, f"{ep['id']}.json")
        with open(ep_file, 'w', encoding='utf-8') as f:
            json.dump(ep, f, indent=2)
        manifest.append(ep['id'])

    manifest_file = os.path.join(output_dir, "_manifest.json")
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp_id": timestamp_id,
            "total_endpoints": len(all_endpoints),
            "endpoints": manifest
        }, f, indent=2)

    # Update latest symlink/reference
    latest_file = os.path.join(raw_dir, "latest.json")
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump({"latest_timestamp": timestamp_id, "total_endpoints": len(all_endpoints)}, f, indent=2)

    print(f"✅ Ingestion complete! Total Endpoints Captured: {len(all_endpoints)}")

if __name__ == '__main__':
    run_capture()
