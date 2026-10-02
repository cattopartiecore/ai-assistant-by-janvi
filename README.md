# GDG-USAR AI-Powered Document Assistant (Task 3)

An intelligent, grounded Retrieval-Augmented Generation (RAG) assistant for the *GDG-USAR Student Handbook*, built with LangChain, ChromaDB, HuggingFace embeddings, and Google Gemini / Groq LLMs.

---

## 1. Goal

The goal of this project is to provide accurate, strictly grounded answers to student queries regarding GDG-USAR club activities, student support desks, workshop participation, event registration, and project submissions. 

Key architectural goals include:
1. **Zero Hallucination / Strict Grounding**: The assistant answers strictly from retrieved handbook passages.
2. **Explicit Citations**: Every answer provides verified citations formatted as:
   `Sources: Section N: Title (page P) - "supporting quotation under 25 words"`.
3. **Two-Layer Out-of-Scope Defense**:
   - **Layer A (Retrieval Guard)**: Queries with best cosine similarity score below $\tau = 0.40$ are intercepted immediately without calling the LLM.
   - **Layer B (Prompt Guard)**: If retrieved context lacks the answer or addresses Section 7 ("Information Not Specified Here"), the LLM returns exactly:
     `This information is not available in the handbook.`
4. **Empirical Chunking Comparison**: Benchmarks `char_500` (CharacterTextSplitter) against `recursive_200` (RecursiveCharacterTextSplitter).

---

## 2. Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Git (recommended)

### Installation
1. Clone the repository and navigate to the project root:
   ```bash
   cd Ja.antigravity
   ```
2. Create and activate a virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy the example `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and configure your API key:
   ```ini
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your_gemini_api_key_here
   # Optional: GROQ_API_KEY=your_groq_api_key_here
   ```
   *(Note: The system supports offline fallback mode if no API key is immediately supplied).*

---

## 3. How to Run

### Indexing the Handbook
The vector indices build automatically on first query. To pre-build or force a rebuild from the source PDF:
```bash
python -m src.indexer
```

### Interactive CLI Chat Loop
Start an interactive Q&A session:
```bash
# Run with default strategy (recursive_200)
python -m src.main

# Run with character 500 strategy
python -m src.main --strategy char_500
```
Type `exit` or `quit` to end the session.

### Single Question Query Mode
Query directly from the command line:
```bash
python -m src.main --question "What are the Student Support Desk's opening hours?" --strategy char_500
```

### Running Test Suite
Execute all standard and bonus test questions against both chunking strategies:
```bash
python -m eval.run_tests
```

### Running Chunking Strategy Comparison
Generate quantitative comparison tables, side-by-side retrieved chunk examples, and save `eval/results.json` and `eval/results.md`:
```bash
python -m eval.compare_chunking
```

---

## 4. Limitations

1. **Static Document Scope**: The assistant is strictly restricted to `data/GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf`. It does not retrieve live university announcements or database records.
2. **Section 7 Intentional Boundaries**: Questions regarding upcoming event dates/venues, current community leadership, workshop-specific certificate thresholds, and individual student registration statuses are explicitly unanswerable per handbook Section 7.
3. **Lexical Semantic Divergence**: Highly fragmented queries or obscure non-standard abbreviations not covered by the `all-MiniLM-L6-v2` embedding vocabulary may experience reduced retrieval similarity scores.

---

## 5. Example Output

### Example 1: Answerable Query (Support Desk Opening Hours)
```text
======================================================================
QUESTION: What are the Student Support Desk's opening hours?
----------------------------------------------------------------------
ANSWER:
The Student Support Desk is open Monday to Friday, from 10:00 AM to 4:00 PM. It is closed on weekends and declared university holidays.

Sources:
Section 1: Student Support Desk (page 1) - "The desk is open Monday to Friday, from 10:00 AM to 4:00 PM."
----------------------------------------------------------------------
METRICS & TRACE:
  • Best Similarity Score: 0.7315
  • Latency: 0.045s
  • Top-k Chunks Retrieved: 3
    [1] Sec 1: Student Support Desk (p. 1) | Score: 0.7315
    [2] Sec 6: Frequently Asked Questions (p. 2) | Score: 0.4623
    [3] Sec 1: Student Support Desk (p. 1) | Score: 0.3732
======================================================================
```

### Example 2: Unanswerable Query (Section 7 Trigger)
```text
======================================================================
QUESTION: Who is the current community lead of GDG On Campus USAR?
----------------------------------------------------------------------
ANSWER:
This information is not available in the handbook.
----------------------------------------------------------------------
METRICS & TRACE:
  • Best Similarity Score: 0.7100
  • Latency: 0.033s
  • Guard Triggered: prompt_guard
======================================================================
```

### Example 3: Completely Out-of-Scope Query (Retrieval Guard Trigger)
```text
======================================================================
QUESTION: What is the airspeed velocity of an unladen swallow?
----------------------------------------------------------------------
ANSWER:
This information is not available in the handbook.
----------------------------------------------------------------------
METRICS & TRACE:
  • Best Similarity Score: 0.0339
  • Latency: 0.012s
  • Guard Triggered: retrieval_guard
======================================================================
```

---

## Project Structure
```
├── data/
│   └── GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf  # Fictional Handbook (~4 pages)
├── src/
│   ├── config.py              # Centralized configuration & thresholds
│   ├── loader.py              # PDF parser & merged heading normalization
│   ├── chunker.py             # Strategies (char_500, recursive_200) & split analysis
│   ├── indexer.py             # Embeddings & persistent Chroma collections
│   ├── retriever.py           # Top-k search & retrieval guard check
│   ├── qa_chain.py            # Strict prompt, two-layer guard, citations & retry
│   └── main.py                # Interactive CLI and single query runner
├── eval/
│   ├── test_questions.json    # Standard & bonus test suites
│   ├── compare_chunking.py    # Benchmark script & side-by-side chunk reporter
│   ├── run_tests.py           # Automated test execution & verification
│   ├── results.json           # Raw benchmark metrics
│   └── results.md             # Markdown comparison report
├── DECISIONS.md               # Real results, chunking trade-offs, architecture decisions
├── AI_USAGE.md                # AI tools disclosure, review verification & reflection
├── README.md                  # Goal, Setup, How to Run, Limitations, Example Output
├── requirements.txt           # Python package dependencies
└── .env.example               # Environment variables template
```
