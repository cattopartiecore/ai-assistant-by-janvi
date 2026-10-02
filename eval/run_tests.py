"""
Test execution script for GDG-USAR AI Document Assistant.
Executes the test suite defined in eval/test_questions.json against both chunking strategies,
validates retrieval accuracy, citation compliance, fallback triggering, and outputs PASS/FAIL status.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from tabulate import tabulate

from src.config import EVAL_DIR, FALLBACK_RESPONSE
from src.qa_chain import answer_question, get_llm


TEST_FILE = EVAL_DIR / "test_questions.json"


def evaluate_response(q_item: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the QA result against ground truth expectations.

    Scoring:
    - retrieval_hit: True if any top-k chunk is from expected_sections
    - fallback_correct: True if unanswerable got fallback, or answerable did NOT get fallback
    - citation_correct: True if cited section is in expected_sections
    - correctness_score:
        2: Fully accurate answer containing all key facts
        1: Partially accurate
        0: Inaccurate or hallucinated
    - pass_fail: PASS or FAIL
    """
    expected_sections = q_item.get("expected_sections", [])
    q_type = q_item.get("type", "answerable")
    answer = result.get("answer", "")
    sources = result.get("sources")
    retrieved_chunks = result.get("retrieved_chunks", [])
    guard = result.get("guard_triggered")

    # 1. Retrieval Hit
    retrieved_sections = [c.get("section_number") for c in retrieved_chunks]
    retrieval_hit = any(s in expected_sections for s in retrieved_sections)

    # 2. Fallback correctness
    is_fallback = FALLBACK_RESPONSE.lower() in answer.lower()
    if q_type == "unanswerable":
        fallback_correct = is_fallback
    else:
        fallback_correct = not is_fallback

    # 3. Citation accuracy
    citation_correct = False
    if q_type == "unanswerable":
        citation_correct = (sources is None or sources == "")
    else:
        if sources:
            for s in expected_sections:
                if f"Section {s}" in sources:
                    citation_correct = True
                    break

    # 4. Correctness Score (0 - 2)
    score = 0
    if q_type == "unanswerable":
        score = 2 if is_fallback else 0
    else:
        if is_fallback:
            score = 0
        else:
            key_facts = q_item.get("key_facts", [])
            matches = sum(1 for k in key_facts if k.lower() in answer.lower())
            if len(key_facts) > 0:
                match_ratio = matches / len(key_facts)
                if match_ratio >= 0.7:
                    score = 2
                elif match_ratio >= 0.3:
                    score = 1
                else:
                    score = 0
            else:
                score = 2 if retrieval_hit else 0

    # 5. PASS / FAIL determination
    if q_type == "unanswerable":
        passed = fallback_correct
    else:
        passed = (not is_fallback) and (score >= 1) and retrieval_hit

    return {
        "retrieval_hit": retrieval_hit,
        "fallback_correct": fallback_correct,
        "citation_correct": citation_correct,
        "correctness_score": score,
        "passed": passed,
        "retrieved_sections": retrieved_sections,
    }


def run_tests_for_strategy(strategy: str, questions: List[Dict[str, Any]], llm: Any = None) -> List[Dict[str, Any]]:
    """Runs all test questions for a single strategy using live LLM."""
    results = []
    for q in questions:
        res = answer_question(
            question=q["question"],
            strategy=strategy,
            llm=llm,
            allow_mock_fallback=False,
        )
        import time
        time.sleep(2.0)
        eval_metrics = evaluate_response(q, res)
        results.append({
            "test_id": q["id"],
            "category": q["category"],
            "type": q["type"],
            "question": q["question"],
            "expected_sections": q["expected_sections"],
            "expected_answer": q["expected_answer"],
            "actual_answer": res["answer"],
            "sources": res["sources"],
            "best_score": res["best_score"],
            "retrieved_chunks": res["retrieved_chunks"],
            "guard_triggered": res.get("guard_triggered"),
            "latency_s": res["latency_s"],
            "eval": eval_metrics,
        })
    return results


def print_test_results(strategy: str, results: List[Dict[str, Any]]):
    """Prints formatted test execution report."""
    print("\n" + "=" * 80)
    print(f"TEST EXECUTION REPORT - STRATEGY: {strategy}")
    print("=" * 80)

    for item in results:
        status_str = "[PASS]" if item["eval"]["passed"] else "[FAIL]"
        print(f"\nQuestion #{item['test_id']} ({item['category'].upper()} | {item['type'].upper()}): {status_str}")
        print(f"Query: {item['question']}")
        print("-" * 80)
        print(f"Output Answer:\n{item['actual_answer']}")
        print("-" * 80)
        print(f"Metrics:")
        print(f"  • Best Similarity Score: {item['best_score']}")
        print(f"  • Retrieved Sections: {item['eval']['retrieved_sections']} (Expected: {item['expected_sections']})")
        print(f"  • Retrieval Hit: {'YES' if item['eval']['retrieval_hit'] else 'NO'}")
        print(f"  • Citation Accuracy: {'YES' if item['eval']['citation_correct'] else 'NO'}")
        print(f"  • Correctness Score (0-2): {item['eval']['correctness_score']} / 2")
        print(f"  • Guard Triggered: {item['guard_triggered'] or 'None'}")
        print(f"  • Latency: {item['latency_s']}s")
        print(f"  • Final Status: {status_str}")
        print("-" * 80)


def main():
    if not TEST_FILE.exists():
        print(f"Error: Test file not found at {TEST_FILE}")
        sys.exit(1)

    with open(TEST_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Initialize live LLM (strict, no mock fallback)
    try:
        llm = get_llm(allow_mock_fallback=False)
        print(f"Using live LLM provider: {os.getenv('LLM_PROVIDER', 'gemini')} ({os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')})")
    except Exception as e:
        print(f"\n[Fatal Error]: Live LLM initialization failed: {e}")
        print("Please ensure GOOGLE_API_KEY is saved in .env and valid.")
        sys.exit(1)

    strategies = ["char_500", "recursive_200"]
    all_summary = {}

    for strat in strategies:
        strat_results = run_tests_for_strategy(strat, questions, llm=llm)
        print_test_results(strat, strat_results)

        standard = [r for r in strat_results if r["category"] == "standard"]
        bonus = [r for r in strat_results if r["category"] == "bonus"]

        std_passes = sum(1 for r in standard if r["eval"]["passed"])
        bonus_passes = sum(1 for r in bonus if r["eval"]["passed"])

        all_summary[strat] = {
            "standard_passed": f"{std_passes}/{len(standard)}",
            "bonus_passed": f"{bonus_passes}/{len(bonus)}",
            "avg_latency": round(sum(r["latency_s"] for r in strat_results) / len(strat_results), 3),
        }

    print("\n" + "=" * 60)
    print("OVERALL SUMMARY ACROSS STRATEGIES:")
    print("=" * 60)
    for strat, summ in all_summary.items():
        print(f"  Strategy: {strat}")
        print(f"    • Standard Questions Passed: {summ['standard_passed']}")
        print(f"    • Bonus Edge Cases Passed:   {summ['bonus_passed']}")
        print(f"    • Avg Latency:               {summ['avg_latency']}s")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
