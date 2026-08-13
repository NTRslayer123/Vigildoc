"""
VigilDoc Step 4: API Network Exporter (`build_graph.py`)
Exports API endpoints, schema models, categories, and vector correlation links as graph.json topology dataset.
"""

import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_build_graph():
    base_dir = os.path.dirname(__file__)
    wiki_dir = os.path.join(base_dir, 'wiki')
    meta_path = os.path.join(base_dir, 'embeddings_meta.json')
    raw_dir = os.path.join(base_dir, 'raw')

    if not os.path.exists(meta_path):
        print("❌ Error: embeddings_meta.json not found. Run link.py first.")
        return

    with open(meta_path, 'r', encoding='utf-8') as f:
        link_meta = json.load(f)

    latest_file = os.path.join(raw_dir, "latest.json")
    with open(latest_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    timestamp_id = meta['latest_timestamp']
    target_raw_dir = os.path.join(raw_dir, timestamp_id)

    nodes = []
    edges = []
    category_set = set()
    data_models_set = set()

    # Category nodes
    categories = ["Authentication", "Core Endpoints", "Webhooks", "Data Schemas"]
    for cat in categories:
        nodes.append({
            "id": f"cat_{cat.lower().replace(' ', '_')}",
            "label": cat,
            "group": "category",
            "shape": "ellipse",
            "color": "#4A90E2",
            "size": 25
        })

    # Endpoint nodes
    auto_links = link_meta.get('auto_links', {})

    for ep_id in link_meta.get('endpoints', []):
        raw_file = os.path.join(target_raw_dir, f"{ep_id}.json")
        if not os.path.exists(raw_file):
            continue

        with open(raw_file, 'r', encoding='utf-8') as f:
            ep = json.load(f)

        method = ep.get('method', 'GET')
        cat = ep.get('category', 'Core Endpoints')
        
        # Color by HTTP method
        color_map = {
            "GET": "#2ECC71",
            "POST": "#3498DB",
            "PUT": "#F39C12",
            "DELETE": "#E74C3C",
            "PATCH": "#9B59B6"
        }

        nodes.append({
            "id": ep_id,
            "label": f"{method} {ep.get('path')}",
            "summary": ep.get('summary'),
            "category": cat,
            "group": "endpoint",
            "shape": "box",
            "color": color_map.get(method, "#95A5A6"),
            "size": 15
        })

        # Edge from endpoint to Category
        cat_node_id = f"cat_{cat.lower().replace(' ', '_')}"
        edges.append({
            "from": cat_node_id,
            "to": ep_id,
            "label": "contains",
            "color": "#BDC3C7",
            "arrows": "to"
        })

        # Add data model nodes and edges based on payload schemas
        req_i = json.dumps(ep.get('request_schema', {}))
        resp_i = json.dumps(ep.get('response_schema', {}))
        
        for key, model_name in [
            ('customer_id', 'CustomerModel'),
            ('payment_intent_id', 'PaymentIntentModel'),
            ('charge_id', 'ChargeModel'),
            ('cart_id', 'CartModel'),
            ('order_id', 'OrderModel'),
            ('product_id', 'ProductModel'),
            ('user_id', 'UserModel')
        ]:
            if key in req_i or key in resp_i:
                data_models_set.add(model_name)
                edges.append({
                    "from": ep_id,
                    "to": f"model_{model_name.lower()}",
                    "label": "uses_schema",
                    "color": "#F39C12",
                    "arrows": "to"
                })

        # Vector linkage edges
        links = auto_links.get(ep_id, [])
        for link in links:
            edges.append({
                "from": ep_id,
                "to": link['target_id'],
                "label": "vector_linked",
                "color": "#9B59B6",
                "dashes": True
            })

    # Data Model nodes
    for model_name in data_models_set:
        nodes.append({
            "id": f"model_{model_name.lower()}",
            "label": f"📦 {model_name}",
            "group": "data_model",
            "shape": "diamond",
            "color": "#E67E22",
            "size": 20
        })

    graph_dataset = {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }

    output_graph_file = os.path.join(base_dir, "graph.json")
    with open(output_graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_dataset, f, indent=2)

    print(f"✅ API Topology Graph built! Exported {len(nodes)} nodes & {len(edges)} edges to graph.json.")

if __name__ == '__main__':
    run_build_graph()
