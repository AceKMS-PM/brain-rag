# Architecture Overview

## System Design

Brain RAG is a local Retrieval-Augmented Generation system with three core layers:

```
┌─────────────────────────────────────────────────────┐
│                  Tauri Desktop App                   │
│              (Rust + WebKit WebView)                 │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   FastAPI Backend                    │
│  ┌─────────┐  ┌────────┐  ┌────────┐  ┌─────────┐  │
│  │  main   │─▶│ search │─▶│  llm   │  │ webui   │  │
│  │  .py    │  │  .py   │  │  .py   │  │  .py    │  │
│  └────┬────┘  └───┬────┘  └───┬────┘  └─────────┘  │
│       │           │           │                     │
│       ▼           ▼           ▼                     │
│  ┌─────────┐  ┌────────┐  ┌────────┐               │
│  │ ingest  │  │  BM25  │  │ llama  │               │
│  │  .py    │  │ (rank) │  │  .cpp  │               │
│  └────┬────┘  └────────┘  └────────┘               │
│       │                                            │
└───────┼────────────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐
│   LanceDB     │     │   GGUF Models │
│  (vector DB)  │     │  (CPU infer)  │
└───────────────┘     └───────────────┘
```

## Layer Breakdown

### 1. Presentation Layer
- **`templates/index.html`** - Web UI (HTML/CSS/JS)
- **`src-tauri/`** - Tauri desktop wrapper (Rust + WebKit)
- **`app/webui.py`** - FastAPI static file serving

### 2. API Layer
- **`app/main.py`** - FastAPI routes, OpenAI-compatible endpoint

### 3. Core Logic Layer
- **`app/search.py`** - Hybrid search (vector + BM25 + RRF)
- **`app/llm.py`** - LLM inference with 3 models
- **`app/ingest.py`** - Document ingestion pipeline

### 4. Data Layer
- **LanceDB** - Vector storage at `~/memory/_index/`
- **GGUF Models** - Local AI models at `~/models/`

## Data Flow

### Query Path
1. User asks question via UI
2. FastAPI receives `/query` request
3. Search layer runs hybrid search (vector + BM25 → RRF fusion)
4. Top-K results form context
5. LLM generates answer with context
6. Response returned to UI

### Ingestion Path
1. Documents in vault scanned for `.md`, `.txt`, `.pdf`
2. Semantic chunking by markdown headers
3. Embedding model generates vectors
4. LanceDB stores text + vectors + metadata
