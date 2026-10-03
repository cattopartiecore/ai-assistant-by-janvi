# AI Tools Usage Documentation (AI_USAGE.md)

In compliance with Section 4 of the *GDG-USAR Student Handbook*, this document records the use of artificial intelligence tools during the development and live validation of the Task 3 AI-Powered Document Assistant.

---

## 1. AI Tools Utilized

- **Google Antigravity**: Agentic programming environment utilized for project scaffolding, directory creation, dependency management, automated testing orchestration, and terminal command execution.
- **Google Gemini (Gemini 3.5 Flash Lite)**: Active foundation language model connected via the user's `GOOGLE_API_KEY` for live response generation, grounded retrieval-augmented generation (RAG), and zero-hallucination verification.

---

## 2. Allocation of Work: AI-Generated vs. Human-Reviewed

| Component / Task | AI Contribution | Human Engineer Review & Modification Janvi Samantray |
| :--- | :--- | :--- |
| **PDF Extraction & Quirk Handling** | Formulated regular expressions to identify section headings and resolve merged text strings (e.g., `...announcement.4. Project Submissions`). | Inspected extracted section breaks against the PDF to verify that all 8 sections (0 to 7) and page numbers mapped correctly.  |acterTextSplitter` (`char_500`) and `RecursiveCharacterTextSplitter` (`recursive_200`) with metadata preservation. | Measured chunk length distributions, analyzed mid-sentence splits, and audited Section 1 rule-exception cohesion. signed by: Engineer Janvi Samantray 
| **Vector Store & Embeddings** | Implemented persistent ChromaDB indexing using `all-MiniLM-L6-v2` and configured the cosine distance metric. | Validated mathematical conversion from cosine distance to similarity ($1 - \text{distance}$).  |
| **Retrieval Guard Calibration** | Implemented Layer-A hreshold filtering and Layer-B prompt guard fallback logic. | Identified that an initial threshold of 0.45 caused a false rejection of Question 7 on `char_500`; recalibrated threshold to 0.40 signed by Engineer: Janvi Samantray |
| **Live Model & API Diagnostics** | Diagnosed 2026 model version migrations (migrated from legacy 1.5/2.5 endpoints to `gemini-3.5-flash-lite`) and handled list-type content response payloads. | Configured `GOOGLE_API_KEY` in `.env` and validated API response latency under free tier quotas. signed by Engineer: Janvi Samantray |
| **Test Suite & Benchmarking** | Generated test runners (`run_tests.py`, `compare_chunking.py`), markdown tables, and JSON result serialization. | Audited ground truth questions, expected sections, and pass/fail thresholds against the handbook source. [signed by engineer: Janvi Samantray] |
| **CLI & User Interface** | Created `main.py` CLI supporting interactive loop and single-query execution. | Ran interactive CLI commands and confirmed source citation formatting. [signed by engineer: Janvi Samantray] |
| **Streamlit Web UI (`app/app.py`)** | Generated modern web chat interface using Streamlit, Google Developer Group theme styling (#4285F4, #EA4335, #FBBC04, #34A853), starter chips, dynamic confidence badges, side-by-side strategy comparison, amber fallback card, and handbook section browser. | Reviewed layout, mobile responsiveness, color contrast, and custom CSS styling. Verified that core logic in `src/` remained untouched and imported cleanly. signed by engineer: Janvi Samantray |
| **Multi-Document Knowledge Base & Auto-Rebuild** | Extended `src/loader.py` to parse `.pdf`, `.txt`, `.md`, standardized rich metadata schema, implemented directory hashing in `src/indexer.py` (`data_manifest.json`), and added search scope filtering (`all` vs `handbook`) in `src/retriever.py`. | Validated metadata tagging across all 4 document formats, tested automated hash re-indexing upon file modification, and audited conflict resolution rules. signed by engineer: Janvi Samantray |
| **UI/UX Upgrade & Session Tools** | Added 6 topic-grouped starter chips, in-app drag-and-drop document uploader, dynamic follow-up suggestions, thumbs up/down feedback logging to `feedback.json`, Markdown chat transcript export, and session analytics drawer. | Tested user feedback writing, verified no personal data collection, validated mobile layout, and checked streaming-style text transitions. signed by engineer: Janvi Samantray |

---

## 3. Verification & Validation Procedures

To ensure code integrity and prevent artificial hallucinations:
1. **Live Gemini API Test Execution**: Executed `eval/run_tests.py` using live Gemini API calls across both chunking strategies for all 12 test questions (5 standard, 2 bonus, 5 extended multi-document), achieving a 100% pass rate on Strategy B (`recursive_200`, 12/12) and 11/12 on Strategy A (`char_500`).
2. **Empirical Benchmarking**: Executed `eval/compare_chunking.py` against live Gemini endpoints, logging real character distributions, split counts, and retrieval latencies (15.77s for `char_500`, 3.38s for `recursive_200`) to `eval/results.json` and `eval/results.md`.
3. **Out-of-Scope Defense Verification**:
   - Tested unrelated queries (e.g., "What is the airspeed velocity of an unladen swallow?") to verify that Layer A (Retrieval Guard) intercepts queries scoring < 0.40 without calling the LLM.
   - Tested unanswerable handbook queries (e.g., Question 5: "Who is the current community lead?") to verify that Layer B (Prompt Guard) accurately recognizes Section 7 and outputs the exact required string: `"This information is not available in the handbook."`
4. **API Quota Management**: Implemented intelligent retry backoff with pacing pauses to ensure stable operation under Google Gemini free-tier rate limits.

---

## 4. Engineering Reflection

Agentic AI tools proved highly effective at accelerating boilerplate setup and identifying upstream model migration targets. However, automated generation required careful human oversight:
- **Upstream Model Evolution**: The Gemini API in late 2025/2026 transitioned legacy endpoints to modern release families (`gemini-3.5-flash-lite`, `gemini-3.8-flash`), and structured `GenerateContentResponse` payloads shifted from raw strings to content block lists. Catching and resolving these nuances ensured reliable live API communication.
- **Dilution in Larger Chunks**: In `char_500`, a 500-character chunk diluted dense sentence-level matches, lowering Question 7 similarity to 0.4398. Without human analysis, an arbitrary 0.45 threshold would have produced a false-negative failure.

---
*Signed by Engineer*: Janvi Samantray
