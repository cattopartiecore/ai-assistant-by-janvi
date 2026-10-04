"""
Retriever module for Airaa — GDG On Campus USAR Document Assistant.
Executes top-k semantic similarity search against the chosen Chroma collection,
converts distance to normalized cosine similarity scores, supports search scope
filtering ('all' vs 'handbook'), and implements the Layer-A Retrieval Guard.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_core.documents import Document

from src.config import (
    DEFAULT_STRATEGY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
)
from src.indexer import get_vector_store, build_index, ensure_indices_up_to_date


def retrieve_relevant_chunks(
    query: str,
    strategy: str = DEFAULT_STRATEGY,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = SIMILARITY_THRESHOLD,
    scope: str = "all",
) -> Dict[str, Any]:
    """
    Performs similarity search with scores for a given user query.

    Args:
        query: User's question or search query.
        strategy: 'char_500' or 'recursive_200'.
        top_k: Number of relevant chunks to retrieve.
        threshold: Minimum cosine similarity score required to pass retrieval guard.
        scope: 'all' (all indexed documents) or 'handbook' (official handbook only).

    Returns:
        Dict containing query, strategy, top_k, scope, threshold, results, best_score, passes_retrieval_guard.
    """
    # Auto-rebuild if data directory files changed
    ensure_indices_up_to_date()

    vector_store = get_vector_store(strategy)

    if vector_store._collection.count() == 0:
        build_index(strategy=strategy)

    # Apply search scope filter
    filter_dict = None
    if scope.lower() in ["handbook", "handbook_only", "official"]:
        filter_dict = {"doc_type": "handbook"}

    if filter_dict:
        raw_results = vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
    else:
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

        meta = doc.metadata or {}
        src_path = meta.get("source", "")
        source_file = meta.get("source_file") or (Path(src_path).name if src_path else "handbook.pdf")
        doc_title = meta.get("doc_title") or source_file
        doc_type = meta.get("doc_type", "extra")
        sec_label = meta.get("section") or f"Section {meta.get('section_number', '?')}: {meta.get('section_title', '')}"

        processed_results.append({
            "document": doc,
            "content": doc.page_content,
            "metadata": meta,
            "source_file": source_file,
            "doc_title": doc_title,
            "doc_type": doc_type,
            "section": sec_label,
            "section_number": meta.get("section_number"),
            "section_title": meta.get("section_title"),
            "page": meta.get("page", 1),
            "chunk_id": meta.get("chunk_id"),
            "similarity_score": similarity_rounded,
            "distance": round(float(distance), 4),
        })

    passes_guard = best_score >= threshold and len(processed_results) > 0

    return {
        "query": query,
        "strategy": strategy,
        "top_k": top_k,
        "scope": scope,
        "threshold": threshold,
        "results": processed_results,
        "best_score": best_score,
        "passes_retrieval_guard": passes_guard,
    }


if __name__ == "__main__":
    print("Testing retrieve_relevant_chunks across scopes:")
    q = "Who is the current community lead of GDG On Campus USAR?"
    
    print("\n--- Scope: Handbook only ---")
    res_hb = retrieve_relevant_chunks(q, strategy="recursive_200", scope="handbook")
    print(f"Best score: {res_hb['best_score']}")
    for r in res_hb['results']:
        print(f"  [{r['doc_type']}] {r['source_file']} | {r['section']} | Score: {r['similarity_score']}")

    print("\n--- Scope: All documents ---")
    res_all = retrieve_relevant_chunks(q, strategy="recursive_200", scope="all")
    print(f"Best score: {res_all['best_score']}")
    for r in res_all['results']:
        print(f"  [{r['doc_type']}] {r['source_file']} | {r['section']} | Score: {r['similarity_score']}")
