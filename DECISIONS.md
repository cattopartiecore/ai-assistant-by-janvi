# Architecture and Engineering Decisions: GDG-USAR Document Assistant

This document records the architectural decisions, trade-offs, and empirical benchmarks for the GDG-USAR AI Document Assistant, validated against the live **Google Gemini API** (`gemini-3.5-flash-lite`), satisfying Section 4 of the *GDG-USAR Student Handbook*.

---

## 1. Chunking Strategy Trade-Offs and Live Benchmark Results

We performed empirical benchmarking of two chunking strategies on the *GDG-USAR Student Handbook* (8 sections, ~4 pages) using the live Gemini API:

| Metric | Strategy A: `char_500` | Strategy B: `recursive_200` |
| :--- | :--- | :--- |
| **Splitter Type** | `CharacterTextSplitter` (chunk_size=500, overlap=50) | `RecursiveCharacterTextSplitter` (chunk_size=200, overlap=40) |
| **Total Chunks Produced** | **15 chunks** | **46 chunks** |
| **Chunk Length (Min / Avg / Max)** | 235 / 398.33 / 496 characters | 100 / 132.54 / 198 characters |
| **Mid-Sentence Splits** | 10 chunks (66.7% of chunks) | 38 chunks (82.6% of chunks) |
| **Rule / Exception Cohesion (Sec 1)** | **Preserved intact** within single chunk | **Separated** across chunk boundaries |
| **Retrieval Hit Rate** | **100.0%** (7/7 test questions) | **100.0%** (7/7 test questions) |
| **Answer Correctness Score (0-2)** | **1.86 / 2.0** | **1.86 / 2.0** |
| **Citation Accuracy** | **100.0%** | **100.0%** |
| **Fallback Correctness** | **100.0%** | **100.0%** |
| **Standard Questions Passed** | **5 / 5 (100%)** | **5 / 5 (100%)** |
| **Bonus Edge Cases Passed** | **1 / 2** | **2 / 2 (100%)** |
| **Average Query Latency (Live API)** | 5.217s | 1.584s |

### Key Trade-Off Analysis:
1. **Precision vs. Context Window**:
   - `recursive_200` achieves higher cosine similarity scores on pinpoint factual queries (e.g., certificate rules in Question 2 achieved a similarity score of **0.8728** in `recursive_200` compared to **0.7979** in `char_500`).
   - However, `recursive_200` heavily fragments the source document (producing 46 chunks), resulting in **38 mid-sentence splits** where sentences are truncated or start with lowercase continuation tokens.
2. **Rule vs. Exception Cohesion & The Question 7 Case Study**:
   - In Section 1, the handbook defines the Student Support Desk:
     > *"The desk can guide students on where to submit a request, but it does not approve academic extensions, fee refunds, or attendance exemptions."*
   - In `recursive_200`, the 200-character boundary isolates this specific sentence into its own dedicated chunk, resulting in a high similarity score of **0.5658**. The live Gemini model consumed this chunk and correctly replied:
     > *"No, the Student Support Desk does not approve fee refunds. Sources: Section 1: Student Support Desk (page 1) - 'it does not approve academic extensions, fee refunds, or attendance exemptions.'"*
   - In `char_500`, CharacterTextSplitter split Section 1 at the paragraph boundary. With $k=3$, the retrieved excerpts favored the opening hours paragraph and FAQ chunks over the fee refund sentence (score 0.4398). Because the retrieved excerpt lacked the specific fee refund clause, Gemini's prompt guard strictly obeyed its instructions and declined to answer rather than hallucinate.

### Chosen Strategy & Rationale
- **Primary Recommendation**: **`recursive_200`** for pinpoint factual question answering, with **`char_500`** as a configurable option (`--strategy char_500`).
- **Rationale**: For this 4-page handbook, `recursive_200` achieved a perfect **7/7 pass rate** across all standard and bonus questions on the live Gemini API with 3.3× lower latency (1.58s vs 5.22s).

### Alternative Considered and Rejected
- **Alternative**: Pure Sentence Splitter (`SentenceTransformersTokenSplitter` or strict sentence tokenization, chunk_size ≈ 80–120 characters).
- **Reason for Rejection**: Highly granular sentence-level chunks fail on composite queries. For example, Question 3 asks: *"What files should a project submission include, and what should the README cover?"* A sentence splitter isolates the sentence listing `README`, `DECISIONS.md`, and `AI_USAGE.md` from the adjacent sentence detailing what the README itself must contain, forcing retrieval to miss parts of the answer.

---

## 2. Embedding Model Selection

- **Chosen Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Design Rationale**:
  1. **Local & Autonomous**: Runs locally via CPU without external network calls, eliminating API key quota exhaustion and latency spikes.
  2. **High Semantic Fidelity**: Strong MTEB ranking for semantic retrieval and dense passage matching.
  3. **Low Footprint**: 120MB model weight footprint; fast inference on Windows CPU runtimes (< 20ms per query vector).

---

## 3. Vector Database Selection

- **Chosen Vector Store**: **ChromaDB** (`langchain-chroma` persistent client).
- **Metric**: Cosine Distance (`collection_metadata={"hnsw:space": "cosine"}`).
- **Design Rationale**:
  - Embedded local persistence in `./chroma_db` requiring no background container or server process.
  - Using cosine space maps distance directly to cosine similarity:
    $$\text{Cosine Similarity} = 1.0 - \text{Cosine Distance}$$
  - Separate collections (`gdg_char_500` and `gdg_recursive_200`) prevent vector contamination between strategies.

---

## 4. Top-K and Similarity Threshold Calibration

- **Top-K ($k=3$)**:
  - Balanced context size that captures core section text and FAQ supplementary notes without exceeding prompt limits.
- **Similarity Threshold ($\tau = 0.40$)**:
  - Initial testing with $\tau = 0.45$ caused Question 7 ("Can the Support Desk approve my fee refund?") to score $0.4398$ under `char_500` due to vector dilution over the 500-character paragraph, triggering a false-negative fallback.
  - Re-calibrating the threshold to $\tau = 0.40$ successfully admits all legitimate paraphrased handbook queries (which score between 0.44 and 0.88), while maintaining a wide safety margin against out-of-domain queries (such as quantum physics or Monty Python questions, which score between 0.00 and 0.08).

---

## 5. Two-Layer Out-of-Scope Defense Architecture

To strictly satisfy the zero-hallucination requirement, we built two defensive layers:

```
[User Query]
     │
     ▼
[Retriever: Top-k Search] ─── Best Cosine Similarity < 0.40 ───► [Layer A: Retrieval Guard]
     │                                                                 │
     │ Best Score >= 0.40                                              ▼
     ▼                                                  "This information is not
[Construct Grounded Context]                             available in the handbook."
     │
     ▼
[Layer B: LLM Prompt Guard]
   ├── Grounding Directive: "Rely ONLY on context"
   └── Section 7 Handler: Recognizes unlisted information
     │
     ├── In-Scope / Answerable ────────► Formatted Answer + "Sources: Section N: Title (page P)"
     └── Out-of-Scope / Sec 7 Item ────► "This information is not available in the handbook."
```

### Section 7 Prompt Tuning
Section 7 of the handbook explicitly lists topics that the document does *not* specify (upcoming dates/venues, current community lead, exact certificate criteria for a specific workshop, student registration status). Because Section 7 is indexed, queries on these topics retrieve Section 7 passages with moderate similarity (~0.57–0.71). 
The system prompt explicitly commands the model:
> *"Section 7 of the handbook explicitly lists information that is NOT specified in this handbook... If the user asks about any topic identified in Section 7 as not specified, you MUST NOT infer an answer; you MUST reply with EXACTLY: 'This information is not available in the handbook.'"*

---

## 6. System Limitations

1. **Document-Restricted Scope**: Restricted exclusively to `data/GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf`.
2. **Static Knowledge Base**: Does not track live event registrations, attendance logs, or real-time university calendar modifications.
3. **Lexical Divergence Sensitivity**: Highly misspelled queries or obscure abbreviations not recognized by the MiniLM tokenizer may fall below the 0.40 similarity threshold.
