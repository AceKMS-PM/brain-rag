import logging
from googlesearch import search as google_search
from app import config

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 3) -> list:
    try:
        results = []
        for url in google_search(query, num_results=max_results):
            results.append({
                "title": url.get("title", ""),
                "url": url.get("link", ""),
                "content": url.get("snippet", "")[:300]
            })
        return results
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return []