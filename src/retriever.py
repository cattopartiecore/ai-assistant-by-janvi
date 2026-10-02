"""
Retriever module for GDG-USAR AI Document Assistant.
Executes top-k semantic similarity search against the chosen Chroma collection,
converts distance to normalized cosine similarity scores, and implements
the Layer-A Retrieval Guard against out-of-scope queries.
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from src.config import (
    DEFAULT_STRATEGY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
)
from src.indexer import get_vector_store, build_index


def retrieve_relevant_chunks(
    query: str,
    strategy: str = DEFAULT_STRATEGY,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Performs similarity search with scores for a given user query.

    Args:
        query: User's question or search query.
        strategy: 'char_500' or 'recursive_200'.
        top_k: Number of relevant chunks to retrieve.
        threshold: Minimum cosine similarity score required to pass retrieval guard.

    Returns:
        Dict containing:
            - 'query': original query
            - 'strategy': strategy used
            - 'top_k': k requested
            - 'results': list of dicts with doc, content, metadata, similarity_score, distance
            - 'best_score': highest similarity score among retrieved chunks
            - 'passes_retrieval_guard': boolean flag indicating whether best_score >= threshold
    """
    vector_store = get_vector_store(strategy)

    # Ensure index exists; build if empty
    if vector_store._collection.count() == 0:
        build_index(strategy=strategy)

    # Similarity search with raw cosine distance
    raw_results = vector_store.similarity_search_with_score(query, k=top_k)

    processed_results = []
    best_score = 0.0

    for doc, distance in raw_results:
        # Cosine distance in Chroma with 'hnsw:space': 'cosine' is in [0, 2]
        # Cosine similarity = 1.0 - distance
        similarity = float(max(0.0, min(1.0, 1.0 - distance)))
        similarity_rounded = round(similarity, 4)

        if similarity_rounded > best_score:
            best_score = similarity_rounded

        processed_results.append({
            "document": doc,
            "content": doc.page_content,
            "metadata": doc.metadata,
            "section_number": doc.metadata.get("section_number"),
            "section_title": doc.metadata.get("section_title"),
            "page": doc.metadata.get("page"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "similarity_score": similarity_rounded,
            "distance": round(float(distance), 4),
        })

    passes_guard = best_score >= threshold and len(processed_results) > 0

    return {
        "query": query,
        "strategy": strategy,
        "top_k": top_k,
        "threshold": threshold,
        "results": processed_results,
        "best_score": best_score,
        "passes_retrieval_guard": passes_guard,
    }


if __name__ == "__main__":
    test_queries = [
        "What are the Student Support Desk's opening hours?",
        "Who is the current community lead of GDG On Campus USAR?",
        "What is the airspeed velocity of an unladen swallow?",
    ]

    for q in test_queries:
        print("\n" + "=" * 60)
        print(f"Query: {q}")
        print("=" * 60)
        res = retrieve_relevant_chunks(q, strategy="char_500", top_k=3)
        print(f"Best Similarity Score: {res['best_score']}")
        print(f"Passes Retrieval Guard (Threshold={res['threshold']}): {res['passes_retrieval_guard']}")
        for idx, item in enumerate(res["results"]):
            print(f"  [{idx+1}] Score: {item['similarity_score']} | Sec {item['section_number']}: {item['section_title']} (p. {item['page']})")
            print(f"      Snippet: {item['content'][:90]}...")
