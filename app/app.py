"""
GDG-USAR Knowledge Base Assistant - Advanced Streamlit Web Application.
Multi-document RAG interface with Google Developer Group theming, interactive starter chips,
file management, search scope control, streaming-style answers, feedback capture,
rich citation cards, chat export, and session analytics.
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import (
    DATA_DIR,
    CHUNK_STRATEGIES,
    DEFAULT_STRATEGY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
    FALLBACK_RESPONSE,
    LLM_PROVIDER,
    GEMINI_MODEL,
    EVAL_DIR,
)
from src.qa_chain import answer_question
from src.loader import load_all_documents
from src.indexer import build_all_indices, get_stored_manifest, compute_data_hash


FEEDBACK_FILE = ROOT_DIR / "feedback.json"


# ---------------------------------------------------------------------------
# Page Configuration & Theming
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GDG-USAR Handbook & Knowledge Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_theme_css(theme_mode: str) -> str:
    is_dark = theme_mode == "Dark"
    bg_color = "#121212" if is_dark else "#FFFFFF"
    card_bg = "#1E1E1E" if is_dark else "#F8F9FA"
    text_color = "#E0E0E0" if is_dark else "#202124"
    border_color = "#333333" if is_dark else "#E0E0E0"
    code_bg = "#2A2A2A" if is_dark else "#F1F3F4"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .gdg-accent-bar {{
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #4285F4 0%, #EA4335 33%, #FBBC04 66%, #34A853 100%);
        border-radius: 2px;
        margin-bottom: 1.2rem;
    }}

    .header-container {{
        padding: 0.3rem 0 1.0rem 0;
    }}
    .header-title {{
        font-size: 2.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.2rem;
    }}
    .header-subtitle {{
        font-size: 0.98rem;
        color: #5f6368;
        margin-bottom: 0.6rem;
    }}

    /* Confidence Badges */
    .badge-high {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: #E6F4EA;
        color: #137333;
        border: 1px solid #CEEAD6;
    }}
    .badge-medium {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: #FEF7E0;
        color: #B06000;
        border: 1px solid #FEEFC3;
    }}
    .badge-low {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: #FCE8E6;
        color: #C5221F;
        border: 1px solid #FAD2CF;
    }}

    /* Fallback Card */
    .fallback-card {{
        background-color: #FFF9E6;
        border: 1px solid #FFE082;
        border-left: 5px solid #FBBC04;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin: 0.8rem 0;
        color: #374151;
    }}
    .fallback-title {{
        font-weight: 700;
        color: #92400E;
        font-size: 1.0rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.45rem;
    }}
    .fallback-hint {{
        font-size: 0.88rem;
        color: #78350F;
        line-height: 1.5;
    }}

    /* Source Cards */
    .source-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.15s ease-in-out;
    }}
    .source-card:hover {{
        transform: translateY(-1px);
        border-color: #4285F4;
    }}
    .source-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }}
    .source-tag {{
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #E8F0FE;
        color: #1967D2;
        margin-right: 0.4rem;
    }}
    .source-snippet {{
        font-size: 0.85rem;
        font-style: italic;
        padding: 0.5rem 0.7rem;
        background: {code_bg};
        border-radius: 8px;
        border-left: 3px solid #4285F4;
        line-height: 1.45;
        margin-top: 0.3rem;
    }}

    /* Mobile Responsive tweaks */
    @media (max-width: 768px) {{
        .header-title {{ font-size: 1.5rem; }}
        .source-header {{ flex-direction: column; align-items: flex-start; gap: 0.2rem; }}
    }}

    /* Skeleton Loader */
    @keyframes pulse {{
        0% {{ opacity: 0.6; }}
        50% {{ opacity: 1.0; }}
        100% {{ opacity: 0.6; }}
    }}
    .skeleton-box {{
        height: 1.2rem;
        background: #E0E0E0;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        animation: pulse 1.5s infinite ease-in-out;
    }}
    </style>
    """


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_strategy" not in st.session_state:
        st.session_state.active_strategy = DEFAULT_STRATEGY
    if "search_scope" not in st.session_state:
        st.session_state.search_scope = "all"
    if "compare_mode" not in st.session_state:
        st.session_state.compare_mode = False
    if "top_k" not in st.session_state:
        st.session_state.top_k = DEFAULT_TOP_K
    if "threshold" not in st.session_state:
        st.session_state.threshold = SIMILARITY_THRESHOLD
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Light"
    if "session_stats" not in st.session_state:
        st.session_state.session_stats = {
            "queries_count": 0,
            "total_confidence": 0.0,
            "fallback_count": 0,
            "total_latency": 0.0,
        }


init_session()
st.markdown(get_theme_css(st.session_state.theme_mode), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Feedback Persistence
# ---------------------------------------------------------------------------
def save_user_feedback(question: str, answer: str, rating: str, strategy: str, scope: str, score: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "rating": rating,
        "strategy": strategy,
        "scope": scope,
        "confidence_score": score,
        "answer_preview": answer[:150],
    }
    existing = []
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.append(entry)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


# ---------------------------------------------------------------------------
# Header & Rainbow Bar
# ---------------------------------------------------------------------------
st.markdown('<div class="gdg-accent-bar"></div>', unsafe_allow_html=True)

col_title, col_theme = st.columns([0.82, 0.18])
with col_title:
    st.markdown(
        """
        <div class="header-container">
            <div class="header-title">
                <span style="color:#4285F4">G</span><span style="color:#EA4335">D</span><span style="color:#FBBC04">G</span>
                <span>On Campus USAR — Document Assistant</span>
            </div>
            <div class="header-subtitle">
                Grounded multi-document knowledge base with strict zero-hallucination defense and verifiable citations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_theme:
    current_theme = st.radio(
        "Theme",
        options=["Light", "Dark"],
        horizontal=True,
        index=0 if st.session_state.theme_mode == "Light" else 1,
        label_visibility="collapsed",
    )
    if current_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = current_theme
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar: Knowledge Base & Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🗂️ Search & Knowledge Scope")

    scope_choice = st.radio(
        "Search Scope",
        options=["All documents", "Handbook only"],
        index=0 if st.session_state.search_scope == "all" else 1,
        help="All documents queries handbook + supplemental docs. Handbook only restricts strictly to Task 3 handbook.",
    )
    st.session_state.search_scope = "all" if scope_choice == "All documents" else "handbook"

    st.markdown("---")
    st.markdown("### ⚙️ Pipeline Settings")

    strategy_options = list(CHUNK_STRATEGIES.keys())
    selected_strategy = st.selectbox(
        "Chunking Strategy",
        options=strategy_options,
        index=strategy_options.index(st.session_state.active_strategy),
        help="Strategy A (Character 500) or Strategy B (Recursive 200).",
    )
    st.session_state.active_strategy = selected_strategy

    compare_toggle = st.toggle(
        "⚖️ Compare Mode (Side-by-Side)",
        value=st.session_state.compare_mode,
        help="Queries both strategies simultaneously.",
    )
    st.session_state.compare_mode = compare_toggle

    col_k, col_thresh = st.columns(2)
    with col_k:
        top_k_val = st.slider("Top K", min_value=1, max_value=5, value=st.session_state.top_k)
        st.session_state.top_k = top_k_val
    with col_thresh:
        thresh_val = st.slider("Min Threshold", min_value=0.20, max_value=0.70, value=st.session_state.threshold, step=0.05)
        st.session_state.threshold = thresh_val

    st.markdown("---")

    # Documents Panel
    with st.expander("📚 Knowledge Base Documents", expanded=True):
        st.caption("Indexed files in `data/` directory:")
        supported_files = sorted([p for p in DATA_DIR.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]])
        for f in supported_files:
            is_hb = "task3" in f.name.lower() or "handbook" in f.name.lower()
            badge = "📘 [HANDBOOK]" if is_hb else "📄 [EXTRA]"
            size_kb = round(f.stat().st_size / 1024, 1)
            st.markdown(f"**{badge}** `{f.name}` ({size_kb} KB)")

        st.markdown("")
        if st.button("🔄 Rebuild Vector Index", use_container_width=True):
            with st.spinner("Rebuilding ChromaDB collections for all documents..."):
                build_all_indices(force_rebuild=True)
            st.success("Vector index successfully rebuilt!")
            st.rerun()

        # File Uploader
        st.markdown("##### ➕ Upload New Document")
        uploaded_file = st.file_uploader(
            "Add .txt, .md, or .pdf to knowledge base",
            type=["txt", "md", "pdf"],
            help="Uploaded documents are stored in data/ and immediately indexed.",
        )
        if uploaded_file is not None:
            dest_path = DATA_DIR / uploaded_file.name
            if not dest_path.exists():
                with open(dest_path, "wb") as f_out:
                    f_out.write(uploaded_file.getbuffer())
                with st.spinner(f"Indexing new document `{uploaded_file.name}`..."):
                    build_all_indices(force_rebuild=True)
                st.success(f"Added and indexed `{uploaded_file.name}`!")
                st.rerun()

    # How it Works Expander
    with st.expander("ℹ️ How It Works (RAG Pipeline)", expanded=False):
        st.markdown(
            """
            ```
            ┌─────────────────┐
            │  User Question  │
            └────────┬────────┘
                     ▼
            ┌──────────────────────────────────┐
            │ Embedding (all-MiniLM-L6-v2)     │
            │ Top-k Cosine Similarity Search   │
            │ Scope Filter (All vs Handbook)   │
            └────────┬─────────────────────────┘
                     ▼
            ┌──────────────────────────────────┐
            │ Layer A: Retrieval Guard         │
            │ Score < 0.40  ──► Fallback Card  │
            └────────┬─────────────────────────┘
                     ▼
            ┌──────────────────────────────────┐
            │ Layer B: Grounded LLM Prompt     │
            │ (Strict facts + Conflict Rules)  │
            │ Section 7 Unlisted ──► Fallback  │
            └────────┬─────────────────────────┘
                     ▼
            ┌──────────────────────────────────┐
            │ Verified Answer with Citations   │
            │ Sources: [File] Sec N (p. P)     │
            └──────────────────────────────────┘
            ```
            """
        )

    # Analytics Tab
    with st.expander("📈 Session Analytics", expanded=False):
        stats = st.session_state.session_stats
        q_count = stats["queries_count"]
        avg_conf = (stats["total_confidence"] / q_count) if q_count > 0 else 0.0
        fb_rate = ((stats["fallback_count"] / q_count) * 100) if q_count > 0 else 0.0
        avg_lat = (stats["total_latency"] / q_count) if q_count > 0 else 0.0

        st.metric("Questions Asked", q_count)
        st.metric("Avg Match Confidence", f"{avg_conf:.3f}")
        st.metric("Fallback Rate", f"{fb_rate:.1f}%")
        st.metric("Avg Latency", f"{avg_lat:.2f}s")


# ---------------------------------------------------------------------------
# Welcome Screen & 6 Topic-Grouped Starter Chips
# ---------------------------------------------------------------------------
if len(st.session_state.messages) == 0:
    st.markdown("#### 💡 Welcome! Select a starter question to explore:")
    
    col1, col2, col3 = st.columns(3)
    starter_selected = None

    with col1:
        st.markdown("**🏢 Support Desk**")
        if st.button("🕒 Opening hours & holidays", use_container_width=True, key="chip_desk"):
            starter_selected = "What are the Student Support Desk's opening hours?"
        st.markdown("**📅 Events & Hackathons**")
        if st.button("🚀 HackUSAR 2026 date & venue", use_container_width=True, key="chip_events"):
            starter_selected = "When is HackUSAR 2026 scheduled and where is the venue?"

    with col2:
        st.markdown("**🎓 Workshops**")
        if st.button("📜 Certificate eligibility rule", use_container_width=True, key="chip_cert"):
            starter_selected = "Does attending a workshop automatically give me a certificate?"
        st.markdown("**📁 Projects & Showcases**")
        if st.button("📦 Submission files & README", use_container_width=True, key="chip_proj"):
            starter_selected = "What files should a project submission include, and what should the README cover?"

    with col3:
        st.markdown("**👥 About GDG USAR**")
        if st.button("👤 Current community lead", use_container_width=True, key="chip_lead"):
            starter_selected = "Who is the current community lead of GDG On Campus USAR?"
        st.markdown("**🛡️ Out-of-Scope (Unanswerable)**")
        if st.button("💰 2027 annual club budget", use_container_width=True, key="chip_unanswerable"):
            starter_selected = "What is the total annual funding budget allocated to GDG USAR for the 2027 academic term?"

    if starter_selected:
        st.session_state.triggered_starter = starter_selected
        st.rerun()


# ---------------------------------------------------------------------------
# Helper: Extract Follow-Up Suggestions
# ---------------------------------------------------------------------------
def generate_followup_suggestions(retrieved_chunks: List[Dict[str, Any]]) -> List[str]:
    """Generates 3 contextual follow-up questions strictly from retrieved context."""
    suggestions = []
    seen = set()
    for c in retrieved_chunks:
        sec = c.get("section_title", "")
        f_name = c.get("source_file", "")
        if "Support Desk" in sec and "hours" not in seen:
            suggestions.append("Where is the Student Support Desk located on campus?")
            seen.add("hours")
        elif "Workshop" in sec and "workshops" not in seen:
            suggestions.append("What are the prerequisites for attending technical workshops?")
            seen.add("workshops")
        elif "Project" in sec and "projects" not in seen:
            suggestions.append("What is required in the DECISIONS.md file?")
            seen.add("projects")
        elif "Executive" in sec or "Team" in sec:
            suggestions.append("Who leads the Technical and Media wings of GDG USAR?")
            seen.add("team")
        elif "Event" in sec or "Hackathon" in sec:
            suggestions.append("What is the registration procedure for GDG USAR events?")
            seen.add("events")

    fallback_defaults = [
        "What are the Student Support Desk's opening hours?",
        "What files should a project submission include?",
        "When is HackUSAR 2026 scheduled to take place?",
    ]
    for fb in fallback_defaults:
        if len(suggestions) < 3 and fb not in suggestions:
            suggestions.append(fb)

    return suggestions[:3]


# ---------------------------------------------------------------------------
# Helper: Highlight Matched Words
# ---------------------------------------------------------------------------
def highlight_matched_words(snippet: str, query: str) -> str:
    words = [re.escape(w) for w in query.split() if len(w) > 3]
    if not words:
        return snippet
    pattern = re.compile(rf"(\b(?:{'|'.join(words)})\b)", re.IGNORECASE)
    return pattern.sub(r"<mark style='background-color: #FFF176; padding: 1px 3px; border-radius: 3px;'>\1</mark>", snippet)


# ---------------------------------------------------------------------------
# Render Single Assistant Response
# ---------------------------------------------------------------------------
def render_assistant_response(msg_idx: int, result: dict, query_context: str = ""):
    ans_text = result.get("answer", "")
    score = result.get("best_score", 0.0)
    latency = result.get("latency_s", 0.0)
    chunks = result.get("retrieved_chunks", [])
    guard = result.get("guard_triggered")
    error_msg = result.get("error")

    # 1. Error / Rate limit handling
    if error_msg:
        if "429" in error_msg or "quota" in error_msg.lower() or "exhausted" in error_msg.lower():
            st.warning("⏳ **Free Tier Rate Limit Exceeded**: Google Gemini free-tier rate limits were momentarily reached. Please wait ~15–30 seconds and retry your question.", icon="⚠️")
            return
        st.error(f"Error executing query: {error_msg}")
        return

    # 2. Check Fallback status
    is_fallback = FALLBACK_RESPONSE.lower() in ans_text.lower() or guard in ["retrieval_guard", "prompt_guard"]

    # Header with confidence badge
    badge_html = ""
    if is_fallback:
        badge_html = '<span class="badge-low">🛡️ Out of Scope / Fallback</span>'
    elif score >= 0.70:
        badge_html = f'<span class="badge-high">🟢 High Confidence ({score:.2f})</span>'
    elif score >= 0.45:
        badge_html = f'<span class="badge-medium">🟡 Moderate Confidence ({score:.2f})</span>'
    else:
        badge_html = f'<span class="badge-low">🔴 Low Match ({score:.2f})</span>'

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            {badge_html}
            <span style="font-size: 0.8rem; color: #70757a;">⏱️ {latency}s | Best score: {score:.3f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_fallback:
        # Dynamic topic suggestions from loaded docs
        loaded_titles = []
        for p in DATA_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]:
                loaded_titles.append(p.stem.replace("_", " ").title())
        topics_str = ", ".join(loaded_titles[:4])

        st.markdown(
            f"""
            <div class="fallback-card">
                <div class="fallback-title">
                    ⚠️ {FALLBACK_RESPONSE}
                </div>
                <div class="fallback-hint">
                    <strong>Topics Covered in Knowledge Base:</strong><br>
                    Information is currently indexed for: <em>{topics_str}</em>.<br>
                    Try asking about <strong>Student Support Desk hours</strong>, <strong>HackUSAR 2026 schedule</strong>, 
                    <strong>Project Submission deliverables</strong>, or <strong>Community Leads</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Separate main answer from sources if present
        if "Sources:" in ans_text:
            prose, _ = ans_text.split("Sources:", 1)
        else:
            prose = ans_text

        st.markdown(prose.strip())

        # Expandable Source Cards
        if chunks:
            with st.expander(f"📚 View Retrieved Sources ({len(chunks)} passages)", expanded=False):
                for idx, c in enumerate(chunks, 1):
                    src_file = c.get("source_file", "document")
                    sec_label = c.get("section", "Section")
                    page = c.get("page", 1)
                    c_score = c.get("similarity_score", 0.0)
                    content = c.get("content", "").strip()

                    highlighted = highlight_matched_words(content, query_context)

                    st.markdown(
                        f"""
                        <div class="source-card">
                            <div class="source-header">
                                <div>
                                    <span class="source-tag">📄 {src_file}</span>
                                    <strong>{sec_label}</strong> (p. {page})
                                </div>
                                <span style="font-weight: 600; color: #4285F4;">Cosine Sim: {c_score:.3f}</span>
                            </div>
                            <div class="source-snippet">"{highlighted}"</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Feedback and Follow-up Row
    col_fb1, col_fb2, col_space = st.columns([0.06, 0.06, 0.88])
    with col_fb1:
        if st.button("👍", key=f"thumb_up_{msg_idx}", help="Helpful"):
            save_user_feedback(query_context, ans_text, "positive", st.session_state.active_strategy, st.session_state.search_scope, score)
            st.toast("Thank you for your feedback! 👍", icon="✅")
    with col_fb2:
        if st.button("👎", key=f"thumb_down_{msg_idx}", help="Not helpful"):
            save_user_feedback(query_context, ans_text, "negative", st.session_state.active_strategy, st.session_state.search_scope, score)
            st.toast("Feedback recorded. We'll improve! 👎", icon="📝")

    # Follow-up Suggestions Chips
    if not is_fallback and chunks:
        followups = generate_followup_suggestions(chunks)
        if followups:
            st.markdown("<span style='font-size:0.8rem; color:#5f6368;'>💡 Related Follow-up Questions:</span>", unsafe_allow_html=True)
            f_cols = st.columns(len(followups))
            for f_idx, f_query in enumerate(followups):
                with f_cols[f_idx]:
                    if st.button(f"🔍 {f_query}", key=f"fu_{msg_idx}_{f_idx}", use_container_width=True):
                        st.session_state.triggered_starter = f_query
                        st.rerun()


# ---------------------------------------------------------------------------
# Chat Query Processor
# ---------------------------------------------------------------------------
def execute_query(query: str):
    if not query.strip():
        return

    st.session_state.messages.append({"role": "user", "content": query})

    if st.session_state.compare_mode:
        with st.spinner("Querying both chunking strategies..."):
            res_a = answer_question(
                question=query,
                strategy="char_500",
                top_k=st.session_state.top_k,
                threshold=st.session_state.threshold,
                scope=st.session_state.search_scope,
                allow_mock_fallback=True,
            )
            res_b = answer_question(
                question=query,
                strategy="recursive_200",
                top_k=st.session_state.top_k,
                threshold=st.session_state.threshold,
                scope=st.session_state.search_scope,
                allow_mock_fallback=True,
            )

        st.session_state.messages.append({
            "role": "assistant_compare",
            "res_a": res_a,
            "res_b": res_b,
        })

        # Update Session Analytics
        st.session_state.session_stats["queries_count"] += 1
        st.session_state.session_stats["total_confidence"] += (res_a["best_score"] + res_b["best_score"]) / 2
        st.session_state.session_stats["total_latency"] += (res_a["latency_s"] + res_b["latency_s"]) / 2
        if FALLBACK_RESPONSE.lower() in res_b["answer"].lower():
            st.session_state.session_stats["fallback_count"] += 1

    else:
        with st.spinner(f"Searching knowledge base via '{st.session_state.active_strategy}'..."):
            res = answer_question(
                question=query,
                strategy=st.session_state.active_strategy,
                top_k=st.session_state.top_k,
                threshold=st.session_state.threshold,
                scope=st.session_state.search_scope,
                allow_mock_fallback=True,
            )

        st.session_state.messages.append({
            "role": "assistant",
            "result": res,
            "strategy": st.session_state.active_strategy,
            "scope": st.session_state.search_scope,
        })

        # Update Session Analytics
        st.session_state.session_stats["queries_count"] += 1
        st.session_state.session_stats["total_confidence"] += res["best_score"]
        st.session_state.session_stats["total_latency"] += res["latency_s"]
        if FALLBACK_RESPONSE.lower() in res["answer"].lower():
            st.session_state.session_stats["fallback_count"] += 1


# Check triggered query from chips
if "triggered_starter" in st.session_state and st.session_state.triggered_starter:
    t_query = st.session_state.triggered_starter
    st.session_state.triggered_starter = None
    execute_query(t_query)
    st.rerun()


# ---------------------------------------------------------------------------
# Render Message History
# ---------------------------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{msg['content']}**")

    elif msg["role"] == "assistant":
        user_query = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
        with st.chat_message("assistant", avatar="🎓"):
            st.caption(f"Strategy: `{msg.get('strategy', 'default')}` | Scope: `{msg.get('scope', 'all')}`")
            render_assistant_response(idx, msg["result"], query_context=user_query)

    elif msg["role"] == "assistant_compare":
        user_query = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown("#### Side-by-Side Strategy Comparison")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("##### Strategy A: `char_500`")
                render_assistant_response(f"{idx}_a", msg["res_a"], query_context=user_query)
            with col_b:
                st.markdown("##### Strategy B: `recursive_200`")
                render_assistant_response(f"{idx}_b", msg["res_b"], query_context=user_query)


# ---------------------------------------------------------------------------
# Chat Tools Toolbar (Clear, Export, Copy)
# ---------------------------------------------------------------------------
if len(st.session_state.messages) > 0:
    st.markdown("---")
    tool_col1, tool_col2, tool_col3 = st.columns([0.3, 0.4, 0.3])

    with tool_col1:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    with tool_col2:
        # Build Markdown Export
        md_transcript = "# GDG-USAR Document Assistant - Chat Transcript\n\n"
        md_transcript += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for m in st.session_state.messages:
            if m["role"] == "user":
                md_transcript += f"### User\n{m['content']}\n\n"
            elif m["role"] == "assistant":
                res = m["result"]
                md_transcript += f"### Assistant ({m.get('strategy')} | {m.get('scope')})\n{res.get('answer')}\n\n"
                md_transcript += f"*Score: {res.get('best_score')} | Latency: {res.get('latency_s')}s*\n\n---\n\n"

        st.download_button(
            label="💾 Export Chat as Markdown",
            data=md_transcript,
            file_name=f"gdg_usar_chat_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with tool_col3:
        last_answer = ""
        for m in reversed(st.session_state.messages):
            if m["role"] == "assistant":
                last_answer = m["result"].get("answer", "")
                break
        if last_answer:
            st.download_button(
                label="📋 Download Latest Answer",
                data=last_answer,
                file_name="latest_answer.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Chat Input Bar
# ---------------------------------------------------------------------------
user_prompt = st.chat_input("Ask any question about GDG-USAR handbook, events, teams, or projects...")
if user_prompt:
    execute_query(user_prompt)
    st.rerun()
