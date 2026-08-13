"""
VigilDoc Step 3: Vector Embedding & Schema Dependency Auto-Linker (`link.py`)
Computes vector embeddings over endpoint schemas and descriptions, calculates similarity correlation matrix, and appends Obsidian [[wikilinks]] for shared data structures.
"""

import os
import sys
import json
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from lib.vector_utils import compute_embeddings, compute_similarity_matrix

def run_link():
    base_dir = os.path.dirname(__file__)
    wiki_dir = os.path.join(base_dir, 'wiki')
    raw_dir = os.path.join(base_dir, 'raw')

    manifest_path = os.path.join(wiki_dir, "_wiki_manifest.json")
    if not os.path.exists(manifest_path):
        print("❌ Error: No wiki manifest found. Run classify.py first.")
        return

    with open(manifest_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    latest_file = os.path.join(raw_dir, "latest.json")
    with open(latest_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    timestamp_id = meta['latest_timestamp']
    target_raw_dir = os.path.join(raw_dir, timestamp_id)

    # Collect texts for embedding
    texts = []
    ep_data = []

    for doc in docs:
        ep_id = doc['id']
        raw_file = os.path.join(target_raw_dir, f"{ep_id}.json")
        if os.path.exists(raw_file):
            with open(raw_file, 'r', encoding='utf-8') as f:
                ep = json.load(f)
        else:
            ep = doc

        # Formulate rich text representation of endpoint schema and parameters
        req_str = json.dumps(ep.get('request_schema', {}))
        resp_str = json.dumps(ep.get('response_schema', {}))
        params_str = " ".join([p.get('name', '') for p in ep.get('parameters', [])])

        corpus_text = f"{ep.get('summary', '')} {ep.get('description', '')} {ep.get('path', '')} {params_str} {req_str} {resp_str}"
        texts.append(corpus_text)
        ep_data.append(ep)

    print(f"🔗 Computing vector embeddings for {len(texts)} endpoint schema definitions...")
    embeddings_matrix, vectorizer = compute_embeddings(texts)
    similarity_matrix = compute_similarity_matrix(embeddings_matrix)

    threshold = float(os.getenv("AUTO_LINK_THRESHOLD", "0.60"))
    auto_links = {}

    for i, ep_i in enumerate(ep_data):
        links = []
        for j, ep_j in enumerate(ep_data):
            if i == j:
                continue
            sim = float(similarity_matrix[i][j])
            
            # Check direct schema overlap (e.g., both contain customer_id, payment_intent_id, product_id, or cart_id)
            req_i = json.dumps(ep_i.get('request_schema', {}))
            resp_i = json.dumps(ep_i.get('response_schema', {}))
            req_j = json.dumps(ep_j.get('request_schema', {}))
            resp_j = json.dumps(ep_j.get('response_schema', {}))

            common_keys = set()
            for key in ['customer_id', 'payment_intent_id', 'charge_id', 'cart_id', 'order_id', 'product_id', 'user_id']:
                if (key in req_i or key in resp_i) and (key in req_j or key in resp_j):
                    common_keys.add(key)

            if sim >= threshold or len(common_keys) > 0:
                reason = f"Shared schema models: {', '.join(common_keys)}" if common_keys else f"Vector similarity: {sim:.2f}"
                links.append({
                    "target_id": ep_j['id'],
                    "target_path": ep_j['path'],
                    "target_method": ep_j['method'],
                    "similarity": sim,
                    "reason": reason
                })

        auto_links[ep_i['id']] = links

    print(f"📝 Appending [[wikilinks]] to markdown documentation files...")
    for doc in docs:
        ep_id = doc['id']
        rel_wiki_path = doc['wiki_file']
        full_wiki_path = os.path.join(wiki_dir, rel_wiki_path)

        if not os.path.exists(full_wiki_path):
            continue

        with open(full_wiki_path, 'r', encoding='utf-8') as f:
            content = f.read()

        links = auto_links.get(ep_id, [])
        wikilink_block = ""
        if links:
            wikilink_block += "### Linked Endpoints & Data Dependencies\n\n"
            for link in links[:5]:  # Top 5 links
                target_slug = link['target_id']
                wikilink_block += f"- [[{target_slug}]] (`{link['target_method']} {link['target_path']}`) — *{link['reason']}*\n"
        else:
            wikilink_block += "*No schema dependency links detected.*"

        if "<!-- AUTO_LINK_PLACEHOLDER -->" in content:
            updated_content = content.replace("<!-- AUTO_LINK_PLACEHOLDER -->", wikilink_block)
        else:
            updated_content = content + "\n\n" + wikilink_block

        with open(full_wiki_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    # Save embeddings binary & metadata
    np.save(os.path.join(base_dir, "embeddings.npy"), embeddings_matrix)
    
    meta_output = {
        "endpoints": [e['id'] for e in ep_data],
        "auto_links": auto_links,
        "total_embeddings": len(ep_data)
    }
    with open(os.path.join(base_dir, "embeddings_meta.json"), 'w', encoding='utf-8') as f:
        json.dump(meta_output, f, indent=2)

    print(f"✅ Vector Schema Auto-Linking complete! Saved embeddings.npy and updated wiki articles with [[wikilinks]].")

if __name__ == '__main__':
    run_link()
