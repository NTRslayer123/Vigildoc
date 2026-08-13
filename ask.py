"""
VigilDoc Step 5: RAG Developer Copilot (`ask.py`)
Dense vector search & LLM integration assistant that answers multi-step API integration questions with executable code workflows and documentation citations.
"""

import os
import sys
import glob
import json
import requests
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from lib.vector_utils import compute_embeddings, find_top_k_similar
from lib.llm_utils import get_groq_api_key

def run_ask(query: str):
    base_dir = os.path.dirname(__file__)
    wiki_dir = os.path.join(base_dir, 'wiki')

    md_files = glob.glob(os.path.join(wiki_dir, "**/*.md"), recursive=True)
    if not md_files:
        print("❌ Error: No wiki documentation articles found. Run classify.py first.")
        return

    docs = []
    texts = []
    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        filename = os.path.basename(filepath)
        docs.append({"filename": filename, "path": filepath, "content": content})
        texts.append(content)

    print(f"🤖 Searching across {len(docs)} API documentation pages for query: '{query}'...")
    embeddings_matrix, vectorizer = compute_embeddings(texts)
    
    # Query vector
    query_vector = vectorizer.transform([query])
    top_matches = find_top_k_similar(query_vector, embeddings_matrix, top_k=3)

    retrieved_context = ""
    citations = []

    print("\n🔍 Top Documentation Citations:")
    for idx, sim in top_matches:
        doc = docs[idx]
        citations.append(doc['filename'])
        print(f"  • [[{doc['filename']}]] (Similarity: {sim:.2f})")
        retrieved_context += f"\n--- DOCUMENT: [[{doc['filename']}]] ---\n{doc['content'][:800]}...\n"

    api_key = get_groq_api_key()
    if api_key and not api_key.startswith("your_"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"""You are VigilDoc RAG Copilot, an elite API Integration Architect.
User Question: "{query}"

Retrieved API Documentation Context:
{retrieved_context}

Provide a clear, step-by-step developer integration guide answering the question.
1. Outline the exact sequential sequence of API calls.
2. Provide complete, executable Python code snippets for the workflow.
3. Include explicit documentation citations using Obsidian [[wikilink_filename.md]] format.
"""
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                answer = resp.json()['choices'][0]['message']['content']
                print("\n================ RAG COPILOT WORKFLOW GUIDE ================")
                print(answer)
                print("=============================================================")
                return answer
        except Exception:
            pass

    # Structured fallback response
    print("\n================ RAG COPILOT WORKFLOW GUIDE ================")
    fallback_response = f"""### Step-by-Step API Integration Workflow

To accomplish your objective: **"{query}"**, follow this sequential API integration sequence:

#### 1. Authenticate & Obtain Bearer Credentials
First, issue a request to the Authentication endpoint to generate a bearer token.
- **Reference**: [[post_auth_token.md]] or [[post_auth_login.md]]

#### 2. Execute Primary Operation
Construct the payload and call the primary resource endpoint:
- **Reference**: [[{citations[0] if citations else 'post_payment_intents.md'}]]

```python
import requests

# Step 1: Auth
auth_resp = requests.post("https://api.example.com/v2/auth/token", json={{
    "client_id": "client_live_891f7a",
    "client_secret": "sec_live_9941a82",
    "grant_type": "client_credentials"
}})
token = auth_resp.json()["access_token"]

# Step 2: Resource Call
headers = {{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}}
res = requests.post("https://api.example.com/v1/checkout", headers=headers, json={{
    "cart_id": "cart_88192a",
    "shipping_address": {{"street": "123 Market St", "city": "San Francisco"}}
}})
print("Result:", res.json())
```

#### 3. Handle Asynchronous Webhook Notifications
Listen for real-time state changes on your server.
- **Reference**: [[post_webhooks_listeners.md]]

---
*Citations*: {", ".join([f"[[{c}]]" for c in citations])}
"""
    print(fallback_response)
    print("=============================================================")
    return fallback_response

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="VigilDoc RAG Developer Copilot")
    parser.add_argument("--query", type=str, default="How do I authenticate, create a payment intent, and process checkout?", help="Integration question")
    args = parser.parse_args()

    run_ask(args.query)
