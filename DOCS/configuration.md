# Configuration

## Central Config (`app/config.py`)

All system parameters are defined in a single file.

### Path Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MEMORY_PATH` | `~/memory` | Root folder for all brain data |
| `DOCUMENTS_PATH` | `~/memory/documents` | Legacy document path |
| `INDEX_PATH` | `~/memory/_index` | LanceDB vector storage |
| `MODELS_PATH` | `~/models` | GGUF model files |

### Model Configuration

| Parameter | Model | Size | Purpose |
|-----------|-------|------|---------|
| `LLM_MODEL_TECHNICAL` | `Qwen3.5-2B.Q4_K_M.gguf` | ~1.5GB | Default, balanced |
| `LLM_MODEL_CONVERSATIONAL` | `Llama-3.2-1B-Instruct-Q4_K_M.gguf` | ~1GB | Fast, lightweight |
| `LLM_MODEL_COMPLEX` | `gemma-3-4b-it-Q4_K_M.gguf` | ~2.5GB | More capable |
| `EMBEDDING_MODEL_PATH` | `Qwen3-Embedding-0.6B-f16.gguf` | ~1.1GB | Text → vectors |

### Processing Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `EMBEDDING_N_CTX` | 512 | Embedding context window |
| `LLM_N_CTX` | 2048 | LLM context window |
| `LLM_N_THREADS` | 2 | CPU threads for inference |
| `CHUNK_SIZE` | 512 | Max chunk size (characters) |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `TOP_K` | 5 | Results returned per query |

### Knowledge Sources

Documents are indexed from multiple vault locations:

```python
KNOWLEDGE_SOURCES = [
    {"name": "notes_documents", "path": "~/memory/vault/notes/documents"},
    {"name": "pixelmart", "path": "~/memory/vault/projects/pixelmart"},
    {"name": "moneroo-tools", "path": "~/memory/vault/projects/moneroo-tools"},
    {"name": "daily-bread", "path": "~/memory/vault/projects/daily-bread"},
    {"name": "zeat", "path": "~/memory/vault/projects/zeat"},
]
```

### Ignore Rules

Folders in `IGNORE_DIRS` are skipped during indexing:
`.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `.env`, `.next`, `dist`, `build`, `.cache`, `vendor`, `.idea`, `.vscode`, `target`, `bin`, `obj`

Only `.md`, `.txt`, `.pdf` files are indexed.

### External API Keys

| Variable | Source |
|----------|--------|
| `TAVILY_API_KEY` | Environment variable |
