# GDG On Campus USAR — Knowledge Assistant

An intelligent, grounded multi-document Retrieval-Augmented Generation (RAG) assistant for **GDG On Campus USAR**. Built with LangChain, ChromaDB, HuggingFace embeddings (`all-MiniLM-L6-v2`), Google Gemini API (`gemini-3.5-flash-lite`), and Streamlit with custom Google-inspired theming.

The system delivers verified, self-contained answers strictly from official campus documents, equipped with a rigorous **two-layer zero-hallucination defense** and traceable citations.

> [!CAUTION]
> **CRITICAL SECURITY NOTE**: Never commit or upload `.env` or `.venv/` to GitHub. Your `.env` contains your personal API keys, and `.venv/` contains local binaries. Both are ignored in `.gitignore`.

---

## ✨ Features

- **Multi-Document Knowledge Base**: Ingests and searches PDF, Markdown, and text files from `data/` (official handbook, 2026 events calendar, executive team roster, and project guidelines).
- **Zero-Hallucination & Strict Grounding**: Two-layer out-of-scope defense (similarity threshold guard $\tau = 0.40$ + prompt-level constraints). Returns exactly *"This information is not available in the handbook."* when facts are absent.
- **Handbook Priority Rule**: Resolves conflicts between sources by always prioritizing the official handbook.
- **Dual Chunking Strategies**: Compares Character-based (`char_500`, 500 chars / 50 overlap) with Recursive Character-based (`recursive_200`, 200 chars / 30 overlap) chunking.
- **Search Scope Selector**: Toggle between querying *All documents* or restricting queries strictly to the *Handbook only*.
- **Polished Streamlit Web UI**:
  - Google palette accents (Blue `#4285F4`, Red `#EA4335`, Yellow `#FBBC04`, Green `#34A853`) on dark `#121212` background.
  - Native Dark / Light mode toggle.
  - 6 starter question cards in a 2×3 grid with hover lift and glow.
  - Typing effect for streaming responses and a soft shimmer skeleton during thinking states.
  - Structured event schedule cards for `events_calendar_2026.md`.
  - Confidence badges (High / Moderate / Low).
  - Collapsible source citations with matched query keywords highlighted.
  - Answer toolbar: Copy to clipboard, helpful/unhelpful rating capture (`feedback.json`), and answer regeneration.
  - Sidebar file uploader and index rebuild tool.
  - Export chat history as Markdown.

---

## 📁 Project Structure

```text
Ja.antigravity/
├── .streamlit/
│   └── config.toml          # Dark theme settings, server headless=false & watcher config
├── app/
│   ├── __init__.py          # App package marker
│   ├── app.py               # Streamlit web application entry point
│   └── styles.py            # Centralized CSS variables, themes, and Google palette
├── data/
│   ├── GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf  # Primary Task 3 handbook
│   ├── events_calendar_2026.md                          # Annual events & hackathons
│   ├── community_teams_and_leads.txt                    # Executive board & wings
│   └── project_showcase_guidelines.pdf                  # Submission criteria
├── eval/
│   ├── test_questions.json  # 12 test questions (5 core + 2 bonus + 4 extended + 1 unanswerable)
│   ├── run_tests.py         # Automated test runner with zero-hallucination checks
│   ├── compare_chunking.py  # Benchmark script comparing char_500 vs recursive_200
│   ├── results.json         # Evaluation results & retrieval metrics
│   └── results.md           # Benchmark report & analysis
├── src/
│   ├── __init__.py
│   ├── config.py            # Global paths, model configs, thresholds & constants
│   ├── loader.py            # Multi-format document loader with rich metadata schema
│   ├── chunker.py           # Strategy implementations (char_500, recursive_200)
│   ├── indexer.py           # Persistent ChromaDB vector indexer with auto-rebuild hash checks
│   ├── retriever.py         # Cosine similarity retrieval with search scope filtering
│   └── qa_chain.py          # Grounded QA chain, prompts, citations, and fallback logic
├── .env.example             # Template for API keys and configuration
├── .gitignore               # Ignores .env, .venv/, chroma_db/, caches, etc.
├── requirements.txt         # Pinned project dependencies
├── run.bat                  # One-click Windows launch script
└── README.md                # Project documentation
```

---

## 🚀 Setup on Windows (Command Prompt)

Follow these steps to set up the project on Windows using `cmd.exe`:

### 1. Clone the Repository
```cmd
git clone https://github.com/your-username/gdg-usar-knowledge-assistant.git
cd gdg-usar-knowledge-assistant
```

### 2. Create and Activate a Virtual Environment
```cmd
python -m venv .venv
call .venv\Scripts\activate.bat
```
*(You should see `(.venv)` appear at the beginning of your command prompt).*

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file to `.env`:
```cmd
copy .env.example .env
```
Open `.env` in Notepad:
```cmd
notepad .env
```
Set your API key:
- **`GOOGLE_API_KEY`** *(Recommended)*: Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
- **`GROQ_API_KEY`** *(Optional)*: If using Groq as an alternative LLM provider, obtain a key from [Groq Console](https://console.groq.com/).

```ini
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_actual_google_api_key_here
```
*(No quotes needed. Save and close Notepad).*

---

## 💻 How to Run

### Option 1: One-Click Launcher (Recommended)
Simply double-click `run.bat` in the project root folder, or execute it in CMD:
```cmd
run.bat
```
This script verifies your virtual environment, activates it, starts Streamlit, and automatically opens the app in your default browser at `http://localhost:8501`.

### Option 2: Command Line
From the project root with your environment activated:
```cmd
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

---

## 🛠️ Troubleshooting

### 1. `[ERROR] Virtual environment (.venv) was not found!`
- **Cause**: The `.venv` directory hasn't been created yet.
- **Fix**: Run:
  ```cmd
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
  ```

### 2. `Missing API Key` or `429 Quota Exceeded`
- **Missing Key**: Ensure you copied `.env.example` to `.env` and set `GOOGLE_API_KEY=your_key_here`. The app will warn you if `.env` or the key is absent.
- **429 Rate Limit**: The Google Gemini free tier allows 15 requests per minute. If you hit this limit during heavy querying, wait 15–30 seconds and retry. The app includes friendly retry alerts.

### 3. `Port 8501 is already in use`
- **Cause**: Another Streamlit instance is currently running on port 8501.
- **Fix**: Streamlit will automatically increment to port 8502 or 8503. Alternatively, close the other command prompt window running Streamlit, or kill the process on port 8501:
  ```cmd
  for /f "tokens=5" %a in ('netstat -aon ^| findstr :8501') do taskkill /f /pid %a
  ```

### 4. `ModuleNotFoundError`
- **Cause**: Trying to run with global Python instead of the virtual environment.
- **Fix**: Always run using `run.bat` or prefix commands with `.\.venv\Scripts\python.exe`.

---

## 🛡️ Security & Git Hygiene

- `.env` contains confidential credentials and is explicitly excluded by `.gitignore`.
- `.venv/` contains local architecture binaries and is excluded by `.gitignore`.
- `chroma_db/` contains local vector embeddings generated from your files and will be regenerated automatically if absent.
- **Never push secrets to GitHub**. Always use `.env.example` as a template for other contributors.
