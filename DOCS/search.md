# Hybrid Search

## Overview (`app/search.py`)

Combines semantic vector search with keyword-based BM25 search using Reciprocal Rank Fusion (RRF).

## Why Hybrid?

| Method | Strengths | Weaknesses |
|--------|-----------|------------|
| **Vector Search** | Finds semantic similarity ("car" → "automobile") | Misses exact technical terms |
| **BM25** | Finds exact keyword matches | No semantic understanding |
| **Hybrid (RRF)** | Best of both worlds | Slightly more computation |

## Architecture

```
              Query
                │
        ┌───────┴───────┐
        ▼               ▼
  Vector Search     BM25 Search
  (embedding)      (keyword match)
        │               │
   [results]        [results]
        │               │
        └───────┬───────┘
                ▼
        Reciprocal Rank Fusion
                │
           [merged results]
                │
           Top-K results
```

## Components

### 1. Vector Search (`get_vector_scores()`)

```python
table.search(query_embedding).limit(top_k * 2).to_list()
```

- Generates embedding for query using same model as ingestion
- Returns top 2*K results (to give RRF more candidates)

### 2. BM25 Search (`get_bm25_scores()`)

```python
bm25_index = BM25Okapi(tokenized_corpus)
scores = bm25_index.get_scores(tokenized_query)
```

- Uses `rank_bm25` library
- Builds index from all documents in LanceDB (cached)
- Returns top results with non-zero scores

### 3. Reciprocal Rank Fusion (`reciprocal_rank_fusion()`)

```python
rrf_score = k / (rank + k)  # k=60 by default
```

- Ranks documents from both sources
- Assigns score based on position, not raw similarity
- Merges by summing scores across sources
- Deduplicates by text content

**Why k=60?** Standard RRF value - balances weight between top-ranked and lower-ranked results.

## Caching

BM25 index is built once and cached in module-level variables:
- `bm25_index` - The BM25Okapi object
- `bm25_corpus` - All document texts
- `bm25_filenames` - All document filenames

## Key Functions

| Function | Purpose |
|----------|---------|
| `search(query, top_k)` | Main entry point |
| `get_vector_scores(query, top_k)` | Semantic search |
| `get_bm25_scores(query, top_k)` | Keyword search |
| `reciprocal_rank_fusion(v, b, k)` | Merge results |
| `build_bm25_index()` | Build/cache BM25 index |
