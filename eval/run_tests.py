"""
Test execution script for GDG-USAR AI Document Assistant.
Executes the test suite defined in eval/test_questions.json against both chunking strategies:
- Standard (Questions 1-5) and Bonus (Questions 6-7) under 'handbook' search scope.
- Extended (Questions 8-12) under 'all' search scope.
Validates retrieval accuracy, citation compliance, fallback triggering, and outputs PASS/FAIL status.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from tabulate import tabulate

from src.config import EVAL_DIR, FALLBACK_RESPONSE
from src.qa_chain import answer_question, get_llm


TEST_FILE = EVAL_DIR / "test_questions.json"


def evaluate_response(q_item: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the QA result against ground truth expectations.
    """
    expected_sections = q_item.get("expected_sections", [])
    expected_source_file = q_item.get("expected_source_file")
    q_type = q_item.get("type", "answerable")
    answer = result.get("answer", "")
    sources = result.get("sources")
    retrieved_chunks = result.get("retrieved_chunks", [])
    guard = result.get("guard_triggered")

    # 1. Retrieval Hit
    retrieved_sections = [c.get("section_number") for c in retrieved_chunks]
    retrieved_files = [c.get("source_file") for c in retrieved_chunks]

    if q_type == "unanswerable":
        retrieval_hit = True
    else:
        sec_hit = any(s in expected_sections for s in retrieved_sections) if expected_sections else False
        file_hit = (expected_source_file in retrieved_files) if expected_source_file else False
        retrieval_hit = sec_hit or file_hit

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
            # Check if expected source file or expected section appears in sources
            if expected_source_file and expected_source_file.lower() in sources.lower():
                citation_correct = True
            elif expected_sections:
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
                if match_ratio >= 0.6:
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
        "retrieved_files": retrieved_files,
    }


def load_all_questions() -> List[Dict[str, Any]]:
    """Loads combined standard and extended questions."""
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    all_q = []
    if "standard" in data:
        all_q.extend(data["standard"])
    if "extended" in data:
        all_q.extend(data["extended"])
    return all_q


def run_tests_for_strategy(strategy: str, questions: List[Dict[str, Any]], llm: Any = None) -> List[Dict[str, Any]]:
    """Runs all test questions for a single strategy using live LLM with pacing."""
    results = []
    for q in questions:
        q_scope = q.get("scope", "all")
        res = answer_question(
            question=q["question"],
            strategy=strategy,
            scope=q_scope,
            llm=llm,
            allow_mock_fallback=False,
        )
        # Pacing pause to respect Gemini free tier RPM
        time.sleep(2.0)
        eval_metrics = evaluate_response(q, res)
        results.append({
            "test_id": q["id"],
            "category": q["category"],
            "type": q["type"],
            "scope": q_scope,
            "question": q["question"],
            "expected_sections": q.get("expected_sections", []),
            "expected_source_file": q.get("expected_source_file"),
            "expected_answer": q["expected_answer"],
            "actual_answer": res["answer"],
            "sources": res.get("sources"),
            "best_score": res["best_score"],
            "guard_triggered": res.get("guard_triggered"),
            "latency_s": res["latency_s"],
            "eval": eval_metrics,
        })
    return results


def print_strategy_report(strategy: str, results: List[Dict[str, Any]]):
    """Prints formatted test results table for a given strategy."""
    table_data = []
    for r in results:
        ev = r["eval"]
        status = "PASS" if ev["passed"] else "FAIL"
        ans_preview = r["actual_answer"][:80].replace("\n", " ") + "..." if len(r["actual_answer"]) > 80 else r["actual_answer"].replace("\n", " ")
        table_data.append([
            r["test_id"],
            r["category"].capitalize(),
            r["scope"],
            r["type"][:6],
            r["question"][:35] + "...",
            r["best_score"],
            ev["correctness_score"],
            "Y" if ev["citation_correct"] else "N",
            status,
        ])

    headers = ["ID", "Category", "Scope", "Type", "Question", "Score", "Corr(0-2)", "Cite", "Status"]
    print("\n" + "=" * 80)
    print(f"TEST EXECUTION REPORT - STRATEGY: {strategy}")
    print("=" * 80)
    print(tabulate(table_data, headers=headers, tablefmt="github"))
    print("=" * 80)


def main():
    questions = load_all_questions()
    print(f"Loaded {len(questions)} total test questions ({sum(1 for q in questions if q['category'] == 'standard')} standard, {sum(1 for q in questions if q['category'] == 'bonus')} bonus, {sum(1 for q in questions if q['category'] == 'extended')} extended).")

    # Strictly initialize live LLM
    try:
        llm = get_llm(allow_mock_fallback=False)
        print(f"Using live LLM for evaluation: {os.getenv('LLM_PROVIDER', 'gemini')} ({os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')})")
    except Exception as e:
        print(f"\n[Fatal Error]: Live LLM initialization failed: {e}")
        sys.exit(1)

    all_summary = {}

    for strat in ["char_500", "recursive_200"]:
        print(f"\n>>> Running Test Suite for Strategy: '{strat}'...")
        strat_results = run_tests_for_strategy(strat, questions, llm=llm)
        print_strategy_report(strat, strat_results)

        standard = [r for r in strat_results if r["category"] == "standard"]
        bonus = [r for r in strat_results if r["category"] == "bonus"]
        extended = [r for r in strat_results if r["category"] == "extended"]

        std_passes = sum(1 for r in standard if r["eval"]["passed"])
        bonus_passes = sum(1 for r in bonus if r["eval"]["passed"])
        ext_passes = sum(1 for r in extended if r["eval"]["passed"])

        all_summary[strat] = {
            "standard_passed": f"{std_passes}/{len(standard)}",
            "bonus_passed": f"{bonus_passes}/{len(bonus)}",
            "extended_passed": f"{ext_passes}/{len(extended)}",
            "total_passed": f"{std_passes + bonus_passes + ext_passes}/{len(strat_results)}",
            "avg_latency": round(sum(r["latency_s"] for r in strat_results) / len(strat_results), 3),
        }

    print("\n" + "=" * 65)
    print("OVERALL SUMMARY ACROSS STRATEGIES:")
    print("=" * 65)
    for strat, summ in all_summary.items():
        print(f"  Strategy: {strat}")
        print(f"    • Standard (Handbook Only) Passed: {summ['standard_passed']}")
        print(f"    • Bonus Edge Cases Passed:         {summ['bonus_passed']}")
        print(f"    • Extended Multi-Document Passed:  {summ['extended_passed']}")
        print(f"    • Total Test Suite Passed:         {summ['total_passed']}")
        print(f"    • Avg Latency:                     {summ['avg_latency']}s")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
