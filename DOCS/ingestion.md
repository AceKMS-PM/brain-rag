# Ingestion Pipeline

## Overview (`app/ingest.py`)

Transforms documents from the vault into searchable vector embeddings stored in LanceDB.

## Pipeline Steps

```
Vault Files → Read Content → Semantic Chunking → Embedding → LanceDB
```

### 1. File Discovery

- Scans all `KNOWLEDGE_SOURCES` paths recursively
- Filters by `INDEXABLE_EXTENSIONS` (.md, .txt, .pdf)
- Excludes paths matching `IGNORE_DIRS`

### 2. Content Extraction

**Markdown/Text**: Read directly with UTF-8 encoding.

**PDF**: Uses `pypdf.PdfReader` to extract text from each page.

### 3. Semantic Chunking (`semantic_chunk_text()`)

Chunks are split at markdown header boundaries, not fixed sizes:

```
# Document Title          ← Section 1
Some intro text...

## Section 1              ← Section 2  
Detailed content here...

### Subsection             ← Section 3
More details...
```

**Algorithm**:
1. Find all markdown headers (`#` through `######`)
2. Each header defines a section boundary
3. Sections >= `min_chunk_size` (100 chars) become chunks
4. Small sections merge with previous chunk if they fit
5. Oversized chunks split further by lines

**Fallback**: If no headers found, uses `simple_chunk()` with fixed-size window + overlap.

### 4. Embedding Generation

Uses `llama-cpp-python` with the embedding model:

```python
model = Llama(model_path=EMBEDDING_MODEL_PATH, embedding=True, n_ctx=512)
embedding = model.embed(chunk_text)
```

### 5. LanceDB Storage

Each record contains:

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | string | Unique: `{source}_{filename}_{index}` |
| `filename` | string | Original file name |
| `source` | string | Knowledge source name |
| `chunk_index` | int | Position in document |
| `text` | string | Chunk content |
| `embedding` | vector | 1024-dim embedding |

**Behavior**: Drops existing `documents` table before re-ingestion (full rebuild).

## Key Functions

| Function | Purpose |
|----------|---------|
| `ingest_documents()` | Full pipeline entry point |
| `process_document(path, source)` | Process single file → records |
| `semantic_chunk_text(text)` | Header-based chunking |
| `get_embedding(text)` | Generate vector for text |
| `get_db()` | Lazy LanceDB connection |
| `get_embedding_model()` | Lazy embedding model load |

## Performance Notes

- Embedding model loads once (lazy singleton)
- Each chunk requires one forward pass through embedding model
- LanceDB schema auto-inferred from first insert
- Ingestion is synchronous and blocks during indexing
