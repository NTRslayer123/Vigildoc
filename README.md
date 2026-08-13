# VigilDoc — Autonomous Multi-Format Technical & API Documentation Generator

> Ingest multi-repository codebases, OpenAPI/Swagger specifications, and Git commit histories, autonomously generate live interactive documentation with usage examples and diagram specs, auto-link schema dependencies via vector similarity, and host a RAG developer assistance portal.

---

## 🏅 Weekly Badges & Progress

- [x] 🏅 **The Collector** (Phase 0 & 1): Ingest raw source code, OpenAPI specs, and commit diff payloads into `raw/`.
- [x] 🏅 **The Tech Writer** (Phase 2 & 3): LLM documentation generation, API schema classification, and cross-endpoint vector auto-linking into `wiki/`.
- [x] 🏅 **The Publisher** (Phase 4): Interactive API schema topology visualizer and dynamic docs portal.
- [x] 🏅 **The Assistant** (Phase 5 & 6): RAG developer copilot for live API Q&A and interactive web portal.

---

## 📂 System Pipeline & Architecture

```
Ingest Source Code, OpenAPI Specs & Commit Logs (`docs/`)
 ↓
Docstring & Schema Ingestion Engine (`capture.py`) -> `raw/<timestamp_id>/`
 ↓
LLM Technical Documentation & Multi-Language Snippet Generator (`classify.py`) -> `wiki/`
 ↓
Vector Embedding & Endpoint Dependency Auto-Linker (`link.py`) -> `embeddings.npy` & `[[wikilinks]]`
 ↓
Interactive API Map & Developer Web Portal (`app.py` & `build_graph.py`) -> `graph.json`
 ↓
RAG Developer Copilot (`ask.py`)
```

---

## 🚀 Quickstart & Pipeline Commands

### 1. Ingest API Specs & Source Code
```bash
python capture.py
```
*Parses OpenAPI 3.0 YAML/JSON specs and FastAPI Python route definitions in `docs/` into structured JSON schemas stored under `raw/<timestamp_id>/` (32 total endpoints captured).*

### 2. Generate Technical Documentation & Multi-Language Code Snippets
```bash
python classify.py
```
*Prompts LLM / template engine to write comprehensive Markdown documentation articles categorized into **Authentication**, **Core Endpoints**, **Webhooks**, and **Data Schemas** under `wiki/`, complete with code snippets in Python, cURL, JavaScript, and Go.*

### 3. Vector Embedding & Schema Auto-Linking
```bash
python link.py
```
*Computes dense TF-IDF vector embeddings over endpoint payload models and descriptions, calculates correlation matrix, auto-links shared schema models with `[[wikilinks]]`, and saves `embeddings.npy`.*

### 4. Build API Topology Graph Network
```bash
python build_graph.py
```
*Exports `graph.json` topology dataset containing 42 nodes (Endpoints, Category Hubs, Data Models) and 103 edges (Dependencies, Wikilinks, Vector Links).*

### 5. Query RAG Developer Copilot (CLI)
```bash
python ask.py --query "How do I authenticate, create a payment intent, and process checkout?"
```
*Indexes documentation wiki via dense vector retrieval and synthesizes step-by-step multi-language code integration guides with exact citations.*

### 6. Launch Interactive Web Portal & Topology Visualizer
```bash
streamlit run app.py
```
*Opens modern web application featuring an interactive force-directed topology map, live API docs reader with multi-language code tabs, interactive RAG copilot, and schema registry.*

---

## 🛠️ Tech Stack & Requirements

- **Language**: Python 3.12+
- **Web UI**: Streamlit, PyVis (HTML5 Force Graph Visualizer)
- **Vector Engine**: Pure Python & NumPy TF-IDF Vectorizer (Zero C-DLL dependency issues)
- **LLM Engine**: Groq API (`llama-3.1-8b-instant`) with structured offline fallback
- **Supported Input Formats**: OpenAPI 3.0 (YAML/JSON), Swagger, FastAPI / Express code routes

---

## 📄 Repository Structure

```
vigildoc/
├── .agents/              # Master rules mirror
├── .env                  # Environment keys (GROQ_API_KEY)
├── .env.example          # Environment template
├── .gitignore            # Git ignore configuration
├── requirements.txt      # Python dependencies
├── capture.py            # Phase 1: Spec & Code Ingestion Engine
├── classify.py           # Phase 2: LLM Documentation Generator
├── link.py               # Phase 3: Vector Schema Auto-Linker
├── build_graph.py        # Phase 4: API Network Exporter
├── ask.py                # Phase 5: RAG Developer Copilot CLI
├── app.py                # Interactive Streamlit Web Application
├── docs/                 # Raw API specifications (YAML, JSON, Python)
├── lib/                  # Helper modules (parser, llm, vector)
├── raw/                  # Captured endpoint JSON schemas
├── wiki/                 # Generated Markdown documentation articles
└── README.md             # System documentation
```
