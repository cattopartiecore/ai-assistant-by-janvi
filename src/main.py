"""
CLI entry point for Airaa — GDG On Campus USAR Document Assistant.
Provides interactive chat loop and single-query execution with configurable chunking strategy.
"""

import argparse
import sys
from src.config import DEFAULT_STRATEGY, CHUNK_STRATEGIES, SIMILARITY_THRESHOLD, DEFAULT_TOP_K
from src.indexer import build_all_indices, build_index
from src.qa_chain import answer_question


def display_result(result: dict):
    """Formats and prints the QA result to the console."""
    print("\n" + "=" * 70)
    print(f"QUESTION: {result['question']}")
    print("-" * 70)
    print(f"ANSWER:\n{result['answer']}")
    print("-" * 70)
    print(f"METRICS & TRACE:")
    print(f"  • Best Similarity Score: {result['best_score']}")
    print(f"  • Latency: {result['latency_s']}s")
    if result.get("guard_triggered"):
        print(f"  • Guard Triggered: {result['guard_triggered']}")
    for idx, c in enumerate(result.get("retrieved_chunks", []), 1):
        src_file = c.get("source_file", "unknown")
        d_type = c.get("doc_type", "doc")
        sec_num = c.get("section_number", "?")
        sec_title = c.get("section_title", "")
        page = c.get("page", 1)
        print(f"    [{idx}] [{d_type}] {src_file} | Sec {sec_num}: {sec_title} (p. {page}) | Score: {c.get('similarity_score')}")
    print("=" * 70 + "\n")


def interactive_chat_loop(strategy: str, top_k: int, threshold: float):
    """Runs interactive terminal chat loop."""
    print("\n" + "=" * 70)
    print(f"  Airaa — GDG On Campus USAR Assistant (Strategy: {strategy})")
    print("  Grounded strictly in GDG-USAR Student Handbook.")
    print("  Type 'exit' or 'quit' to end the session.")
    print("=" * 70 + "\n")

    while True:
        try:
            user_input = input("Handbook Question > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Airaa. Goodbye!")
                break

            result = answer_question(
                question=user_input,
                strategy=strategy,
                top_k=top_k,
                threshold=threshold,
                allow_mock_fallback=True,
            )
            display_result(result)

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\n[Error]: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Airaa — GDG On Campus USAR Document Assistant (RAG)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--strategy",
        choices=list(CHUNK_STRATEGIES.keys()),
        default=DEFAULT_STRATEGY,
        help="Chunking strategy to use: 'char_500' or 'recursive_200'.",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Single question to ask. If omitted, starts interactive chat loop.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuilding the vector store indices from the PDF.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of chunks to retrieve.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Minimum similarity score threshold for retrieval guard.",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "handbook"],
        default="all",
        help="Search scope: 'all' (all documents) or 'handbook' (official handbook only).",
    )

    args = parser.parse_args()

    if args.rebuild:
        print("Forced rebuild requested...")
        build_all_indices(force_rebuild=True)

    if args.question:
        result = answer_question(
            question=args.question,
            strategy=args.strategy,
            top_k=args.top_k,
            threshold=args.threshold,
            scope=args.scope,
            allow_mock_fallback=True,
        )
        display_result(result)
    else:
        interactive_chat_loop(
            strategy=args.strategy,
            top_k=args.top_k,
            threshold=args.threshold,
        )


if __name__ == "__main__":
    main()
