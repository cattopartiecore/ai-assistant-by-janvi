"""
Indexer module for GDG-USAR AI Document Assistant.
Builds and manages persistent ChromaDB vector stores with HuggingFace embeddings
(sentence-transformers/all-MiniLM-L6-v2) for each chunking strategy.
"""

from pathlib import Path
from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import (
    CHROMA_PERSIST_DIR,
    CHUNK_STRATEGIES,
    DEFAULT_STRATEGY,
    EMBEDDING_MODEL_NAME,
)
from src.loader import load_and_parse_handbook
from src.chunker import chunk_documents


_embedding_instance: Optional[HuggingFaceEmbeddings] = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Returns a cached instance of HuggingFaceEmbeddings.
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_instance


def get_vector_store(strategy: str = DEFAULT_STRATEGY) -> Chroma:
    """
    Returns the persistent Chroma vector store for the specified strategy.
    Configured with cosine distance ('hnsw:space': 'cosine').
    """
    cfg = CHUNK_STRATEGIES.get(strategy)
    if not cfg:
        raise ValueError(f"Unknown strategy: {strategy}")

    embeddings = get_embedding_model()
    persist_path = Path(CHROMA_PERSIST_DIR)
    persist_path.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma(
        collection_name=cfg["collection_name"],
        embedding_function=embeddings,
        persist_directory=str(persist_path),
        collection_metadata={"hnsw:space": "cosine"},
    )
    return vector_store


def build_index(
    strategy: str = DEFAULT_STRATEGY,
    force_rebuild: bool = False,
    pdf_path: Optional[Path] = None,
) -> Chroma:
    """
    Builds the vector store index for the given chunking strategy.
    If the index already exists and force_rebuild is False, it loads the existing index.

    Args:
        strategy: 'char_500' or 'recursive_200'.
        force_rebuild: If True, clears existing collection and re-indexes.
        pdf_path: Optional custom path to PDF.

    Returns:
        Populated Chroma vector store.
    """
    cfg = CHUNK_STRATEGIES.get(strategy)
    if not cfg:
        raise ValueError(f"Unknown strategy: {strategy}")

    vector_store = get_vector_store(strategy)

    # Check if collection is already populated
    existing_count = vector_store._collection.count()
    if existing_count > 0 and not force_rebuild:
        print(f"[{strategy}] Index already contains {existing_count} chunks. Skipping rebuild.")
        return vector_store

    if force_rebuild and existing_count > 0:
        print(f"[{strategy}] Force rebuild requested. Clearing {existing_count} existing chunks.")
        vector_store.delete_collection()
        vector_store = get_vector_store(strategy)

    print(f"[{strategy}] Loading document and generating chunks...")
    docs = load_and_parse_handbook(pdf_path=pdf_path, print_detected_sections=False)
    chunks = chunk_documents(docs, strategy=strategy)

    print(f"[{strategy}] Embedding and indexing {len(chunks)} chunks into ChromaDB ({cfg['collection_name']})...")
    vector_store.add_documents(chunks)

    final_count = vector_store._collection.count()
    print(f"[{strategy}] Successfully indexed {final_count} chunks into '{cfg['collection_name']}'.")
    return vector_store


def build_all_indices(force_rebuild: bool = False, pdf_path: Optional[Path] = None):
    """
    Builds indices for all configured strategies.
    """
    for strat in CHUNK_STRATEGIES:
        build_index(strategy=strat, force_rebuild=force_rebuild, pdf_path=pdf_path)


if __name__ == "__main__":
    print("Building indices for both chunking strategies...")
    build_all_indices(force_rebuild=True)
    print("Indexing complete.")
