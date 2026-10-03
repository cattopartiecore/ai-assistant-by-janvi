"""
Indexer module for GDG-USAR AI Document Assistant.
Builds and manages persistent ChromaDB vector stores with HuggingFace embeddings
(sentence-transformers/all-MiniLM-L6-v2) for each chunking strategy.
Supports automatic index rebuilding via data directory hash check and CLI --rebuild flag.
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import (
    DATA_DIR,
    CHROMA_PERSIST_DIR,
    CHUNK_STRATEGIES,
    DEFAULT_STRATEGY,
    EMBEDDING_MODEL_NAME,
)
from src.loader import load_all_documents, load_and_parse_handbook
from src.chunker import chunk_documents


_embedding_instance: Optional[HuggingFaceEmbeddings] = None
MANIFEST_FILE = Path(CHROMA_PERSIST_DIR) / "data_manifest.json"


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


def compute_data_hash(data_dir: Optional[Path] = None) -> str:
    """
    Computes a composite MD5 hash of all supported files in data/
    based on filename, size, and last modified time.
    """
    target_dir = Path(data_dir) if data_dir else DATA_DIR
    if not target_dir.exists():
        return ""

    files = sorted(
        [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]],
        key=lambda p: p.name
    )

    hasher = hashlib.md5()
    for f in files:
        stat = f.stat()
        file_desc = f"{f.name}:{stat.st_size}:{stat.st_mtime}"
        hasher.update(file_desc.encode("utf-8"))

    return hasher.hexdigest()


def get_stored_manifest() -> Dict[str, Any]:
    """
    Reads the stored manifest containing the previous data hash.
    """
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_manifest(data_hash: str, file_count: int, chunk_counts: Dict[str, int]):
    """
    Persists data hash and indexing metadata to the manifest.
    """
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "data_hash": data_hash,
        "file_count": file_count,
        "chunk_counts": chunk_counts,
        "strategies": list(CHUNK_STRATEGIES.keys()),
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def is_index_outdated() -> bool:
    """
    Checks if files in data/ have changed since the last build.
    """
    current_hash = compute_data_hash()
    stored_manifest = get_stored_manifest()
    stored_hash = stored_manifest.get("data_hash")
    return current_hash != stored_hash


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
    data_dir: Optional[Path] = None,
) -> Chroma:
    """
    Builds the vector store index for the given chunking strategy across all documents.
    If the index already exists and force_rebuild is False and data has not changed,
    it loads the existing index.
    """
    cfg = CHUNK_STRATEGIES.get(strategy)
    if not cfg:
        raise ValueError(f"Unknown strategy: {strategy}")

    vector_store = get_vector_store(strategy)
    existing_count = vector_store._collection.count()
    needs_rebuild = force_rebuild or is_index_outdated() or (existing_count == 0)

    if not needs_rebuild and existing_count > 0:
        return vector_store

    if existing_count > 0:
        print(f"[{strategy}] Clearing {existing_count} existing chunks from collection '{cfg['collection_name']}'...")
        try:
            vector_store.delete_collection()
        except Exception:
            pass
        vector_store = get_vector_store(strategy)

    print(f"[{strategy}] Loading all documents from data/ and generating chunks...")
    docs = load_all_documents(data_dir=data_dir, print_detected_sections=False)
    chunks = chunk_documents(docs, strategy=strategy)

    print(f"[{strategy}] Indexing {len(chunks)} chunks into ChromaDB ({cfg['collection_name']})...")
    vector_store.add_documents(chunks)

    final_count = vector_store._collection.count()
    print(f"[{strategy}] Successfully indexed {final_count} chunks into '{cfg['collection_name']}'.")
    return vector_store


def build_all_indices(force_rebuild: bool = False, data_dir: Optional[Path] = None):
    """
    Builds indices for all configured strategies and updates the manifest hash.
    """
    chunk_counts = {}
    current_hash = compute_data_hash(data_dir=data_dir)
    target_dir = Path(data_dir) if data_dir else DATA_DIR
    supported_files = [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]]

    for strat in CHUNK_STRATEGIES:
        vs = build_index(strategy=strat, force_rebuild=force_rebuild, data_dir=data_dir)
        chunk_counts[strat] = vs._collection.count()

    save_manifest(current_hash, len(supported_files), chunk_counts)
    print(f"[indexer] Manifest updated. Stored hash: {current_hash} ({len(supported_files)} files).")


def ensure_indices_up_to_date():
    """
    Utility called before queries: if data files changed, triggers automatic rebuild.
    """
    if is_index_outdated():
        print("[indexer] Detected changes in data/ directory. Triggering automatic index rebuild...")
        build_all_indices(force_rebuild=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GDG-USAR Document Knowledge Base Indexer")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force complete rebuild of vector collections even if hash matches.",
    )
    args = parser.parse_args()

    print(f"Executing index build (force_rebuild={args.rebuild})...")
    build_all_indices(force_rebuild=args.rebuild)
    print("Indexing complete.")
