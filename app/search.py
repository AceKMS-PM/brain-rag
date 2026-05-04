import logging
from rank_bm25 import BM25Okapi
from app import config
from app.ingest import get_db, get_embedding_model

logger = logging.getLogger(__name__)

# Cache for BM25 index
bm25_index = None
bm25_corpus = None
bm25_filenames = None

def build_bm25_index():
    """Build BM25 index from LanceDB documents"""
    global bm25_index, bm25_corpus, bm25_filenames
    
    if bm25_index is not None:
        return
    
    db = get_db()
    if "documents" not in db.table_names():
        return
    
    table = db.open_table("documents")
    
    # Get all documents - use to_pandas() or limit high number
    try:
        all_docs = table.to_pandas().to_dict('records')
    except:
        # Fallback: search with high limit
        all_docs = table.search([0]*1024).limit(1000).to_list()
    
    if not all_docs:
        return
    
    # Extract text and filenames
    bm25_corpus = [doc["text"] for doc in all_docs]
    bm25_filenames = [doc["filename"] for doc in all_docs]
    
    # Tokenize corpus
    tokenized_corpus = [doc.lower().split() for doc in bm25_corpus]
    bm25_index = BM25Okapi(tokenized_corpus)
    logger.info(f"BM25 index built with {len(bm25_corpus)} documents")

def get_bm25_scores(query: str, top_k: int = 10):
    """Get BM25 scores for query"""
    build_bm25_index()
    
    if bm25_index is None:
        return []
    
    tokenized_query = query.lower().split()
    scores = bm25_index.get_scores(tokenized_query)
    
    # Get top results with scores
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "filename": bm25_filenames[idx],
                "text": bm25_corpus[idx],
                "bm25_score": scores[idx]
            })
    
    return results

def get_vector_scores(query: str, top_k: int = 10):
    """Get vector search results"""
    db = get_db()
    
    if "documents" not in db.table_names():
        return []
    
    table = db.open_table("documents")
    query_embedding = get_embedding_model().embed(query)
    
    results = table.search(query_embedding).limit(top_k * 2).to_list()
    
    return [{
        "filename": r["filename"],
        "text": r["text"],
        "vector_score": r.get("_score", 0)
    } for r in results]

def reciprocal_rank_fusion(vector_results: list, bm25_results: list, k: int = 60):
    """Combine vector and BM25 results using RRF"""
    rrf_scores = {}
    
    # Process vector results
    for rank, r in enumerate(vector_results):
        key = r["filename"] + "||" + r["text"][:50]
        rrf_scores[key] = rrf_scores.get(key, 0) + (k / (rank + 1))
    
    # Process BM25 results
    for rank, r in enumerate(bm25_results):
        key = r["filename"] + "||" + r["text"][:50]
        rrf_scores[key] = rrf_scores.get(key, 0) + (k / (rank + 1))
    
    # Sort by RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Reconstruct results
    fused = []
    seen_texts = set()
    
    for key, score in sorted_results:
        filename, text_prefix = key.split("||", 1)
        
        # Find original text
        for r in vector_results + bm25_results:
            if r["filename"] == filename and r["text"].startswith(text_prefix):
                if r["text"] not in seen_texts:
                    fused.append({
                        "filename": r["filename"],
                        "text": r["text"],
                        "rrf_score": score
                    })
                    seen_texts.add(r["text"])
                    break
    
    return fused

def search(query: str, top_k: int = config.TOP_K):
    # Get both vector and BM25 results
    vector_results = get_vector_scores(query, top_k * 2)
    bm25_results = get_bm25_scores(query, top_k * 2)
    
    # Combine using RRF
    combined_results = reciprocal_rank_fusion(vector_results, bm25_results)
    
    # Return top k
    final_results = combined_results[:top_k]
    
    logger.info(f"Hybrid search: {len(vector_results)} vector + {len(bm25_results)} BM25 -> {len(final_results)} final")
    
    return {
        "query": query,
        "results": [{"filename": r["filename"], "text": r["text"], "score": r.get("rrf_score", 0)} for r in final_results],
        "total": len(final_results)
    }