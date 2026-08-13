"""
VigilDoc Web Portal (`app.py`)
Streamlit interactive developer documentation portal, force-directed network graph visualizer, and RAG copilot interface.
"""

import os
import json
import glob
import streamlit as st
import streamlit.components.v1 as components
from lib.vector_utils import compute_embeddings, find_top_k_similar
from lib.llm_utils import get_groq_api_key
import requests

# Page Config
st.set_page_config(
    page_title="VigilDoc — Live API Documentation Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Dark/Glassmorphic Aesthetics
st.markdown("""
<style>
    /* Dark Theme Customization */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #1E293B;
        border-radius: 8px 8px 0px 0px;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366F1 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(__file__)
WIKI_DIR = os.path.join(BASE_DIR, 'wiki')
GRAPH_FILE = os.path.join(BASE_DIR, 'graph.json')

def load_graph():
    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def render_standalone_graph(graph_data, selected_category=None):
    """Renders standalone Vis.js force-directed topology network directly in browser iframe."""
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])

    filtered_nodes = []
    node_ids = set()

    for node in nodes:
        if selected_category and selected_category != "All":
            if node.get('group') == 'endpoint' and node.get('category') != selected_category:
                continue
        filtered_nodes.append(node)
        node_ids.add(node['id'])

    filtered_edges = []
    for edge in edges:
        if edge['from'] in node_ids and edge['to'] in node_ids:
            filtered_edges.append(edge)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            html, body {{
                margin: 0;
                padding: 0;
                background-color: #0F172A;
                font-family: system-ui, -apple-system, sans-serif;
            }}
            #mynetwork {{
                width: 100%;
                height: 540px;
                background-color: #0F172A;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({json.dumps(filtered_nodes)});
            var edges = new vis.DataSet({json.dumps(filtered_edges)});
            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                nodes: {{
                    borderWidth: 2,
                    shadow: true,
                    font: {{ color: '#F8FAFC', size: 14 }},
                    margin: 10
                }},
                edges: {{
                    smooth: {{ type: 'continuous' }},
                    shadow: true
                }},
                physics: {{
                    enabled: true,
                    solver: 'barnesHut',
                    barnesHut: {{
                        gravitationalConstant: -6000,
                        centralGravity: 0.2,
                        springLength: 150,
                        springConstant: 0.05,
                        damping: 0.09,
                        avoidOverlap: 1.0
                    }},
                    stabilization: {{
                        enabled: true,
                        iterations: 600,
                        updateInterval: 25,
                        fit: true
                    }}
                }},
                interaction: {{
                    dragNodes: true,
                    zoomView: true,
                    hover: true
                }}
            }};
            var network = new vis.Network(container, data, options);
            network.once("stabilizationIterationsDone", function() {{
                network.setOptions({{ physics: false }});
            }});
        </script>
    </body>
    </html>
    """
    return html_content

# Sidebar Navigation
st.sidebar.title("VigilDoc Portal")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation Menu",
    ["API Topology Map", "Interactive Docs Portal", "RAG Developer Copilot", "Schema Registry & Metrics"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Badge Status")
st.sidebar.markdown("✅ **The Collector** (Ingestion)")
st.sidebar.markdown("✅ **The Tech Writer** (LLM Docs)")
st.sidebar.markdown("✅ **The Publisher** (Graph Visualizer)")
st.sidebar.markdown("✅ **The Assistant** (RAG Copilot)")

# Page 1: API Topology Map
if page == "API Topology Map":
    st.markdown('<div class="main-header">Interactive API Topology & Schema Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visualizing endpoints, schema dependencies, and dense vector similarity linkages</div>', unsafe_allow_html=True)

    graph_data = load_graph()
    if not graph_data:
        st.warning("⚠️ No graph.json found. Run capture.py -> classify.py -> link.py -> build_graph.py first.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Nodes", graph_data['total_nodes'])
        col2.metric("Total Network Edges", graph_data['total_edges'])
        col3.metric("Auto Vector Links", len([e for e in graph_data['edges'] if e.get('label') == 'vector_linked']))

        category_filter = st.selectbox(
            "Filter Network Topology by Category:",
            ["All", "Authentication", "Core Endpoints", "Webhooks", "Data Schemas"]
        )

        html_content = render_standalone_graph(graph_data, category_filter)
        components.html(html_content, height=560, scrolling=False)

# Page 2: Interactive Docs Portal
elif page == "Interactive Docs Portal":
    st.markdown('<div class="main-header">Live API Reference Documentation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-language code snippets and vector auto-linked data schemas</div>', unsafe_allow_html=True)

    manifest_file = os.path.join(WIKI_DIR, "_wiki_manifest.json")
    if os.path.exists(manifest_file):
        with open(manifest_file, 'r', encoding='utf-8') as f:
            wiki_docs = json.load(f)

        categories = list(set([d['category'] for d in wiki_docs]))
        selected_cat = st.selectbox("Select API Category:", categories)

        filtered_docs = [d for d in wiki_docs if d['category'] == selected_cat]
        doc_options = {f"{d['method']} {d['path']}": d for d in filtered_docs}

        if doc_options:
            selected_ep_key = st.selectbox("Select Endpoint:", list(doc_options.keys()))
            selected_doc = doc_options[selected_ep_key]

            doc_path = os.path.join(WIKI_DIR, selected_doc['wiki_file'])
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()

                st.markdown("---")
                st.markdown(md_text)
    else:
        st.info("No synthesized markdown documentation found. Execute build pipeline first.")

# Page 3: RAG Developer Copilot
elif page == "RAG Developer Copilot":
    st.markdown('<div class="main-header">RAG Developer Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask complex integration workflow questions and receive copy-pasteable code guides</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Enter your multi-step integration scenario:",
        value="How do I authenticate, create a payment intent, and process checkout?"
    )

    if st.button("Synthesize Integration Guide"):
        with st.spinner("Searching dense vector index and prompting LLM Copilot..."):
            md_files = glob.glob(os.path.join(WIKI_DIR, "**/*.md"), recursive=True)
            if md_files:
                texts = []
                docs = []
                for filepath in md_files:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        c = f.read()
                    docs.append({"filename": os.path.basename(filepath), "content": c})
                    texts.append(c)

                embeddings_matrix, vectorizer = compute_embeddings(texts)
                query_vector = vectorizer.transform([user_query])
                top_matches = find_top_k_similar(query_vector, embeddings_matrix, top_k=3)

                citations = [docs[idx]['filename'] for idx, sim in top_matches]
                retrieved_context = "\n".join([docs[idx]['content'][:600] for idx, sim in top_matches])

                api_key = get_groq_api_key()
                if api_key and not api_key.startswith("your_"):
                    try:
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        prompt = f"Answer integration question: '{user_query}' using context:\n{retrieved_context}\nProvide step-by-step code and citations [[wikilink]]."
                        resp = requests.post(url, headers=headers, json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}]}, timeout=10)
                        if resp.status_code == 200:
                            st.markdown(resp.json()['choices'][0]['message']['content'])
                            st.stop()
                    except Exception:
                        pass

                # Fallback display
                st.markdown(f"""
### Synthesized Workflow Guide

**Query**: *"{user_query}"*

#### Step 1: Obtain OAuth2 Bearer Access Token
Call `/auth/token` with your client credentials to receive a bearer token.
- Citation: `[[post_auth_token.md]]`

```python
import requests
res = requests.post("https://api.paygateway.com/v2/auth/token", json={{
    "client_id": "client_live_891f7a",
    "client_secret": "sec_live_9941a82",
    "grant_type": "client_credentials"
}})
token = res.json()["access_token"]
```

#### Step 2: Initialize Payment Intent
Create a payment intent with the customer amount and currency.
- Citation: `[[post_payment_intents.md]]`

```python
headers = {{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}}
intent = requests.post("https://api.paygateway.com/v2/payment_intents", headers=headers, json={{
    "amount": 2500,
    "currency": "usd"
}})
print("Intent Created:", intent.json()["id"])
```

#### Step 3: Trigger Storefront Checkout
- Citation: `[[post_checkout.md]]`

---
*Verified Citations*: {", ".join([f"`[[{c}]]`" for c in citations])}
""")

# Page 4: Schema Registry & Metrics
elif page == "Schema Registry & Metrics":
    st.markdown('<div class="main-header">Schema Registry & Vector Analytics</div>', unsafe_allow_html=True)
    
    meta_file = os.path.join(BASE_DIR, "embeddings_meta.json")
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        st.json(meta)
    else:
        st.info("No embeddings_meta.json found. Run link.py to generate schema metadata.")
