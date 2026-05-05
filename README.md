# Brain RAG - Second Brain Local

Local Retrieval-Augmented Generation system with hybrid search, multi-model LLM, and desktop UI.

## Quick Start

```bash
cd ~/brain/rag-service
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 or run the Tauri desktop app.

## Documentation

Detailed docs in `/DOCS/`:

| File | Covers |
|------|--------|
| [Architecture](DOCS/architecture.md) | System design, layers, data flow |
| [Configuration](DOCS/configuration.md) | All settings, models, paths |
| [Ingestion](DOCS/ingestion.md) | Document pipeline, chunking, embeddings |
| [Search](DOCS/search.md) | Hybrid search (vector + BM25 + RRF) |
| [LLM](DOCS/llm.md) | Model management, prompt templates |
| [API](DOCS/api.md) | REST endpoints, OpenAI compatibility |
| [UI](DOCS/ui.md) | Web UI and Tauri desktop app |

## Features

- **Hybrid Search**: Semantic (vector) + keyword (BM25) with RRF fusion
- **3 Local Models**: Llama 3.2-1B, Qwen 3.5-2B, Gemma 3-4B (GGUF, CPU)
- **Multi-source Vault**: Indexes from notes, projects, documents
- **File Types**: Markdown, text, PDF
- **OpenAI Compatible**: `/v1/chat/completions` endpoint for external tools
- **Desktop App**: Tauri wrapper (Rust + WebKit)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Tauri/UI   │────▶│   FastAPI    │────▶│    LLM      │
│  (Browser)  │     │   Backend    │     │  (GGUF/CPU) │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    ▼              ▼
              ┌──────────┐  ┌──────────┐
              │ LanceDB  │  │  BM25    │
              │ (vectors)│  │ (keywords)│
              └──────────┘  └──────────┘
```

## Commands

| Command | Description |
|---------|-------------|
| `curl localhost:8000/health` | Health check |
| `curl -X POST localhost:8000/ingest` | Reindex documents |
| `curl -X POST localhost:8000/query -H "Content-Type: application/json" -d '{"question":"..."}'` | Ask a question |
| `cargo run --manifest-path src-tauri/Cargo.toml` | Launch desktop app |

## Project Structure

```
~/brain/rag-service/
├── app/                    # Python backend
│   ├── config.py          # Central configuration
│   ├── ingest.py          # Document ingestion
│   ├── search.py          # Hybrid search
│   ├── llm.py             # LLM inference
│   ├── main.py            # FastAPI routes
│   ├── webui.py           # UI setup
│   └── websearch.py       # Web search (optional)
├── templates/             # Web UI files
│   └── index.html         # Single-page app
├── src-tauri/             # Tauri desktop app
│   ├── src/main.rs        # Rust entry point
│   ├── tauri.conf.json    # App config
│   └── capabilities/      # Permissions
├── DOCS/                  # Detailed documentation
├── requirements.txt       # Python dependencies
├── package.json           # Node/Tauri scripts
└── brain-ai               # CLI helper script
```

## TODO

### High Priority
- [ ] Streaming responses (SSE / WebSocket)
- [ ] Session memory (remember context across queries)
- [ ] Document management UI (add/remove/reindex)
- [ ] Better error handling and retry logic
- [ ] Resolve CORS issues between Tauri and FastAPI
- [ ] Optimize model loading to prevent OOM crashes on 4GB RAM

### Medium Priority
- [ ] Web search integration (SearXNG or Tavily)
- [ ] Model hot-swapping without restart
- [ ] Conversation export (markdown, PDF)
- [ ] Search result highlighting
- [ ] Response feedback system
- [ ] Implement unified lifecycle management ( backend management within Rust process)

### Low Priority
- [ ] Docker packaging for easy deployment
- [ ] Mobile-responsive UI
- [ ] Voice input
- [ ] Knowledge graph visualization
- [ ] Auto-tagging of documents

### Done
- [x] Hybrid search (BM25 + vector + RRF)
- [x] Multi-model support (3 models)
- [x] OpenAI-compatible API endpoint
- [x] PDF support in ingestion
- [x] Tauri desktop app shell
- [x] Semantic chunking by headers
- [x] Multi-source vault indexing
- [x] Markdown rendering in UI
- [x] Model selector in UI
