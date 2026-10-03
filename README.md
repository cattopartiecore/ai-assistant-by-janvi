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

### Running the Streamlit Web UI
Launch the interactive web assistant with the Google Developer Group custom theme:
```bash
streamlit run app/app.py --server.fileWatcherType none
```
*(Tip: Using `--server.fileWatcherType none` prevents unnecessary server reloads when vector stores update in the background).*

This opens the upgraded web interface featuring:
- **Google Developer Group Brand Aesthetic**: Clean UI with `#4285F4`, `#EA4335`, `#FBBC04`, `#34A853` accents, Inter typography, soft shadows, and light/dark theme switch.
- **6 Topic-Grouped Starter Chips**: Instant FAQ queries covering Support Desk, Events & Hackathons, Workshops, Project Submissions, Leadership, and Out-of-Scope Fallback.
- **Search Scope Control**: Toggle between **All documents** (handbook + supplemental files) and **Handbook only** (strictly official Task 3 handbook).
- **In-App Document Management**: Sidebar panel displaying all loaded files with chunk counts, a manual **"Rebuild Vector Index"** button, and an active drag-and-drop file uploader for `.txt`, `.md`, and `.pdf` files.
- **Side-by-Side Compare Mode**: Real-time side-by-side comparison between `char_500` and `recursive_200`.
- **Dynamic Confidence Badges**: High (🟢), Moderate (🟡), and Low (🔴) badges computed from cosine similarity scores.
- **Amber Fallback Card**: Distinct warning card with helpful navigation hints and dynamic topics built from indexed document titles.
- **Source Cards with Highlighting**: File name badge, section, page, cosine similarity score, and matched query word highlighting.
- **Chat Tools & Feedback**: Thumbs up / down feedback logging to `feedback.json`, Markdown chat transcript export, and one-click answer download.
- **Session Analytics Drawer**: Real-time tracking of questions asked, average confidence, fallback trigger rate, and latency.

### How to Add Documents
1. **Via Web UI**: Drop any `.pdf`, `.txt`, or `.md` file into the sidebar uploader in the Streamlit app. It is immediately copied to `data/` and indexed.
2. **Via Filesystem**: Place your files into the `data/` directory and run:
   ```bash
   python -m src.indexer --rebuild
   ```
   The indexer calculates a composite directory hash (`data_manifest.json`) and automatically rebuilds the vector store if files are added, modified, or removed.

### Indexing the Knowledge Base
To pre-build or force a rebuild from all source documents in `data/`:
```bash
python -m src.indexer --rebuild
```

### Interactive CLI Chat Loop
Start an interactive Q&A session:
```bash
# Run with default strategy (recursive_200) across all documents
python -m src.main --scope all

# Restrict query to handbook only
python -m src.main --scope handbook --strategy recursive_200
```
Type `exit` or `quit` to end the session.

### Single Question Query Mode
Query directly from the command line:
```bash
python -m src.main --question "Who is the current community lead of GDG On Campus USAR?" --scope all
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
├── app/
│   └── app.py                 # Streamlit web UI with GDG styling & compare mode
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
