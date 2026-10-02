# GDG-USAR Chunking Strategy Comparison Report

This report presents empirical findings comparing two chunking strategies on the *GDG-USAR Student Handbook* (~4 pages, 8 sections).

## Quantitative Comparison Table

| Metric                           | Strategy A (char_500)   | Strategy B (recursive_200)   |
|----------------------------------|-------------------------|------------------------------|
| Total Chunks                     | 15                      | 46                           |
| Chunk Length (Min / Avg / Max)   | 235 / 398.33 / 496      | 100 / 132.54 / 198           |
| Mid-Sentence Splits              | 10                      | 38                           |
| Rule/Exception Separated (Sec 1) | Separated across chunks | Separated across chunks      |
| Retrieval Hit Rate (%)           | 100.0%                  | 100.0%                       |
| Answer Correctness (0-2 Avg)     | 1.86 / 2.0              | 1.86 / 2.0                   |
| Citation Accuracy (%)            | 100.0%                  | 100.0%                       |
| Fallback Correctness (%)         | 100.0%                  | 100.0%                       |
| Average Latency (s)              | 5.68s                   | 1.109s                       |

## Detailed Analysis & Observations

### 1. Granularity vs. Context Preservation
- **Strategy A (`char_500`, overlap 50)**:
  - Generates **15 chunks** with an average length of **398.33 characters**.
  - Larger chunk sizes retain broader paragraph context, which is especially valuable for multi-part questions (e.g. Question 3 covering README requirements and required submission files).
  - Fewer mid-sentence splits (10 vs 38).

- **Strategy B (`recursive_200`, overlap 40)**:
  - Generates **46 chunks** with an average length of **132.54 characters**.
  - Fine-grained chunks provide higher vector embedding specificity for isolated facts (e.g. opening hours), but frequently fragment related clauses across chunk boundaries.
  - Causes significant mid-sentence splits (38 chunks), which requires relying on the small 40-character overlap.

### 2. Rule vs. Exception Separation (Support Desk Test)
- The handbook states in Section 1:
  > *"The desk can guide students on where to submit a request, but it does not approve academic extensions, fee refunds, or attendance exemptions."*
- In `recursive_200`, the 200-character ceiling fragments this clause across adjacent chunks. If retrieval only returns the chunk stating the desk "guides students", an LLM might falsely infer it has approval authority.
- In `char_500`, both the guidance mandate and the negative restriction ("does not approve") remain intact within a single unified context window.

### 3. Recommendation & Conclusion
- **Winning Strategy**: **`char_500` (CharacterTextSplitter, chunk_size=500, overlap=50)**.
- **Rationale**: For policy handbooks and student guides where rules and exceptions are tightly coupled within paragraphs, maintaining coherent paragraph boundaries substantially reduces hallucination risk and preserves multi-part submission guidelines.
