"""
Chunking module for GDG-USAR Student Handbook.
Implements CharacterTextSplitter (500/50) and RecursiveCharacterTextSplitter (200/40),
ensuring that section and page metadata are strictly preserved across all chunks.
"""

from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

from src.config import CHUNK_STRATEGIES, DEFAULT_STRATEGY
from src.loader import load_and_parse_handbook


def get_text_splitter(strategy: str):
    """
    Returns the appropriate LangChain text splitter configured for the strategy.
    """
    cfg = CHUNK_STRATEGIES.get(strategy)
    if not cfg:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(CHUNK_STRATEGIES.keys())}")

    if cfg["type"] == "character":
        return CharacterTextSplitter(
            separator="\n",
            chunk_size=cfg["chunk_size"],
            chunk_overlap=cfg["chunk_overlap"],
            keep_separator=True,
        )
    elif cfg["type"] == "recursive":
        return RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],
            chunk_size=cfg["chunk_size"],
            chunk_overlap=cfg["chunk_overlap"],
            keep_separator=True,
        )
    else:
        raise ValueError(f"Unsupported splitter type: {cfg['type']}")


def chunk_documents(documents: List[Document], strategy: str = DEFAULT_STRATEGY) -> List[Document]:
    """
    Splits section-level documents into chunks while preserving section and page metadata.

    Args:
        documents: List of section-level Document objects from loader.
        strategy: 'char_500' or 'recursive_200'.

    Returns:
        List of chunked Document objects with metadata:
        - source
        - page
        - section_number
        - section_title
        - chunk_id
        - strategy
    """
    splitter = get_text_splitter(strategy)
    chunked_docs: List[Document] = []
    chunk_counter = 0

    for doc in documents:
        # Split text of this section
        raw_chunks = splitter.split_text(doc.page_content)
        for i, text in enumerate(raw_chunks):
            text_clean = text.strip()
            if not text_clean:
                continue
            chunk_id = f"sec{doc.metadata.get('section_number', 0)}_chunk{i+1}"
            metadata = dict(doc.metadata)
            metadata["chunk_id"] = chunk_id
            metadata["strategy"] = strategy
            metadata["chunk_index"] = chunk_counter
            chunked_docs.append(Document(page_content=text_clean, metadata=metadata))
            chunk_counter += 1

    return chunked_docs


def analyze_chunking_quality(chunks: List[Document]) -> Dict[str, Any]:
    """
    Analyzes structural quality of chunks:
    - Total chunks
    - Min, max, average character length
    - Mid-sentence split count
    - Rule-vs-exception separation: whether the Support Desk's
      'guides on where to submit' and 'does not approve' statements are separated.
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0,
            "mid_sentence_splits": 0,
            "rule_exception_separated": False,
        }

    lengths = [len(c.page_content) for c in chunks]
    total_chunks = len(chunks)
    avg_len = sum(lengths) / total_chunks
    min_len = min(lengths)
    max_len = max(lengths)

    # Detect mid-sentence split: chunk doesn't end in sentence terminator or begins with lowercase
    mid_sentence_count = 0
    for c in chunks:
        txt = c.page_content.strip()
        ends_sentence = txt.endswith((".", "!", "?", '"', "'"))
        starts_lower = len(txt) > 0 and txt[0].islower()
        if (not ends_sentence) or starts_lower:
            mid_sentence_count += 1

    # Check rule-vs-exception preservation in Section 1:
    # Rule: "guide students on where to submit"
    # Exception: "does not approve" (academic extensions, fee refunds, etc.)
    has_rule_only = False
    has_exception_only = False
    has_both_together = False

    for c in chunks:
        txt = c.page_content.lower()
        contains_rule = "guide" in txt and "submit" in txt
        contains_exception = "does not approve" in txt or "not approve" in txt
        if contains_rule and contains_exception:
            has_both_together = True
        elif contains_rule and not contains_exception:
            has_rule_only = True
        elif contains_exception and not contains_rule:
            has_exception_only = True

    # Rule and exception are separated if any chunk has one without the other
    rule_exception_separated = has_rule_only or has_exception_only

    return {
        "total_chunks": total_chunks,
        "avg_length": round(avg_len, 2),
        "min_length": min_len,
        "max_length": max_len,
        "mid_sentence_splits": mid_sentence_count,
        "rule_exception_separated": rule_exception_separated,
        "has_both_together": has_both_together,
        "has_rule_only": has_rule_only,
        "has_exception_only": has_exception_only,
    }


if __name__ == "__main__":
    docs = load_and_parse_handbook(print_detected_sections=False)
    for strat in ["char_500", "recursive_200"]:
        chunks = chunk_documents(docs, strategy=strat)
        stats = analyze_chunking_quality(chunks)
        print(f"=== Strategy: {strat} ===")
        print(f"Total Chunks: {stats['total_chunks']}")
        print(f"Length (min/avg/max): {stats['min_length']} / {stats['avg_length']} / {stats['max_length']}")
        print(f"Mid-sentence splits: {stats['mid_sentence_splits']}")
        print(f"Rule/Exception Separated: {stats['rule_exception_separated']} (both in same chunk: {stats['has_both_together']})")
        print()
