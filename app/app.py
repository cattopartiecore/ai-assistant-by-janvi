"""
GDG-USAR Knowledge Base Assistant - Advanced Streamlit Web Application.
Multi-document RAG interface with Google Developer Group theming, interactive starter chips,
file management, search scope control, streaming-style answers, feedback capture,
rich citation cards, chat export, and session analytics.
"""

# Streamlit Community Cloud SQLite3 compatibility fix for ChromaDB (Linux)
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except (ImportError, KeyError):
    pass

import os
import sys
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st

# Ensure project root and app directory are in sys.path
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

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

try:
    from styles import get_app_css, GOOGLE_BLUE, GOOGLE_RED, GOOGLE_YELLOW, GOOGLE_GREEN
except (ModuleNotFoundError, ImportError):
    from app.styles import get_app_css, GOOGLE_BLUE, GOOGLE_RED, GOOGLE_YELLOW, GOOGLE_GREEN

FEEDBACK_FILE = ROOT_DIR / "feedback.json"

DID_YOU_KNOW_FACTS = [
    "📍 **Room 104, Admin Block**: The Student Support Desk is open Monday through Friday, 09:00 to 17:00 (closed during 13:00–14:00 lunch).",
    "🚀 **HackUSAR 2026**: A 24-hour hackathon scheduled for Nov 14–15, 2026 focusing on AI and Sustainable Cities.",
    "📜 **Workshop Certificates**: Attendance does NOT automatically grant a certificate; explicit criteria and project evaluation must be met.",
    "📁 **Project Deliverables**: All project submissions require a `README.md`, `DECISIONS.md`, and `AI_USAGE.md` (if AI tools were used).",
    "👤 **Community Leadership**: Aarav Sharma is the GDG On Campus USAR Community Lead for the 2026–2027 term.",
    "🏛️ **Faculty Advisor**: Dr. Neha Verma (Associate Professor, Dept of AI & Data Science) serves as the faculty sponsor.",
    "🎟️ **Free Registration**: Tickets for all GDG USAR technical events are free for registered USAR students but strictly non-transferable.",
    "💬 **Discord Community**: All official announcements, study jam voice lounges, and mentor Q&A channels are hosted on the club Discord.",
]

# ---------------------------------------------------------------------------
# Page Configuration & Theming
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GDG On Campus USAR — Knowledge Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
        st.session_state.theme_mode = "Dark"
    if "session_stats" not in st.session_state:
        st.session_state.session_stats = {
            "queries_count": 0,
            "total_confidence": 0.0,
            "fallback_count": 0,
            "total_latency": 0.0,
        }
    if "current_fact_idx" not in st.session_state:
        st.session_state.current_fact_idx = 0


init_session()
st.markdown(get_app_css(st.session_state.theme_mode), unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def ensure_knowledge_base_ready():
    """
    Automatically builds and verifies ChromaDB collections on first startup
    (e.g. on Streamlit Community Cloud where chroma_db is not committed).
    Cached via st.cache_resource so it only executes once per session/runtime.
    """
    from src.indexer import get_vector_store, build_all_indices, is_index_outdated

    needs_build = False
    try:
        vs_char = get_vector_store("char_500")
        vs_rec = get_vector_store("recursive_200")
        if vs_char._collection.count() == 0 or vs_rec._collection.count() == 0 or is_index_outdated():
            needs_build = True
    except Exception:
        needs_build = True

    if needs_build:
        with st.spinner("🚀 Setting up knowledge base... (Indexing documents for the first time)"):
            build_all_indices(force_rebuild=True)
    return True


ensure_knowledge_base_ready()


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
# Sidebar: Clean Grouped Layout with Compact Spacing
# ---------------------------------------------------------------------------
with st.sidebar:
    # 1. Appearance & Scope Group
    st.markdown("### 🎨 Appearance & Scope")
    col_t1, col_t2 = st.columns([0.45, 0.55])
    with col_t1:
        theme_choice = st.radio(
            "Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.theme_mode == "Dark" else 1,
            horizontal=True,
            label_visibility="collapsed",
            help="Toggle between Dark (#121212) and Light theme.",
        )
        if theme_choice != st.session_state.theme_mode:
            st.session_state.theme_mode = theme_choice
            st.rerun()

    with col_t2:
        scope_choice = st.selectbox(
            "Search Scope",
            options=["All documents", "Handbook only"],
            index=0 if st.session_state.search_scope == "all" else 1,
            label_visibility="collapsed",
            help="Choose 'All documents' for supplemental data or 'Handbook only' for Task 3 official handbook.",
        )
        st.session_state.search_scope = "all" if scope_choice == "All documents" else "handbook"

    st.markdown("---")

    # 2. Pipeline Settings Group
    st.markdown("### ⚙️ Pipeline Configuration")
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
        help="Queries both chunking strategies simultaneously and displays results side by side.",
    )
    st.session_state.compare_mode = compare_toggle

    col_k, col_thresh = st.columns(2)
    with col_k:
        top_k_val = st.slider(
            "Top K Chunks",
            min_value=1,
            max_value=5,
            value=st.session_state.top_k,
            help="Number of most similar passages to retrieve.",
        )
        st.session_state.top_k = top_k_val
    with col_thresh:
        thresh_val = st.slider(
            "Min Match Score",
            min_value=0.20,
            max_value=0.70,
            value=st.session_state.threshold,
            step=0.05,
            help="Cosine similarity threshold. Below this triggers fallback.",
        )
        st.session_state.threshold = thresh_val

    st.markdown("---")

    # 3. Knowledge Base Documents Group
    with st.expander("📚 Knowledge Base Documents", expanded=False):
        st.caption("Indexed files in `data/` directory:")
        supported_files = sorted(
            [p for p in DATA_DIR.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]]
        )
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

        st.markdown("##### ➕ Upload Document")
        uploaded_file = st.file_uploader(
            "Add .txt, .md, or .pdf",
            type=["txt", "md", "pdf"],
            help="Uploaded documents are stored in data/ and indexed immediately.",
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

    # 4. "Did You Know?" Fact Strip
    st.markdown("### 💡 Quick Fact")
    fact_text = DID_YOU_KNOW_FACTS[st.session_state.current_fact_idx % len(DID_YOU_KNOW_FACTS)]
    st.markdown(
        f"""
        <div class="did-you-know-card">
            <div class="did-you-know-header">✨ Verified Fact from Docs</div>
            <div class="did-you-know-body">{fact_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🎲 Next Fact", key="btn_next_fact", use_container_width=True):
        st.session_state.current_fact_idx = (st.session_state.current_fact_idx + 1) % len(DID_YOU_KNOW_FACTS)
        st.rerun()

    st.markdown("---")

    # 5. Pipeline & Analytics Group
    with st.expander("ℹ️ How It Works (RAG Architecture)", expanded=False):
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
# Main Header Layout (Inline colored G-D-G on single line, subtitle below)
# ---------------------------------------------------------------------------
st.markdown('<div class="gdg-accent-bar"></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="main-header">
        <div class="brand-title">
            <span class="brand-g">G</span><span class="brand-d">D</span><span class="brand-g2">G</span>&nbsp;<span class="brand-campus">On Campus USAR</span>
        </div>
        <div class="brand-subtitle">
            Grounded multi-document knowledge base with strict zero-hallucination defense and verifiable citations.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helper: Event Card Extraction from events_calendar_2026.md
# ---------------------------------------------------------------------------
def extract_event_cards(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract structured event card if retrieved chunks contain events_calendar_2026.md."""
    event_chunks = [c for c in chunks if "events_calendar" in c.get("source_file", "").lower()]
    if not event_chunks:
        return []

    combined = "\n".join(c.get("content", "") for c in event_chunks)
    cards = []

    if "HackUSAR" in combined:
        cards.append({
            "name": "HackUSAR 2026 (Annual Hackathon)",
            "date": "November 14–15, 2026",
            "venue": "Main Campus USAR Auditorium & IoT Labs",
            "registration": "Free via official community portal (opens 2 weeks prior)",
            "details": "24-hour hackathon on AI & Sustainable Cities. Teams of 2–4.",
            "icon": "🚀",
        })
    elif "AI Bootcamp" in combined or "Vision Workshop" in combined:
        cards.append({
            "name": "AI Bootcamp & Vision Workshop",
            "date": "September 18, 2026",
            "venue": "Computer Center Lab 201",
            "registration": "Free via official community portal (opens 2 weeks prior)",
            "details": "Hands-on computer vision and multimodal agent development.",
            "icon": "🤖",
        })
    elif "Cloud Study Jam" in combined:
        cards.append({
            "name": "Cloud Study Jam",
            "date": "October 5, 2026",
            "venue": "Virtual on Google Meet",
            "registration": "Free via official community portal (opens 2 weeks prior)",
            "details": "Google Cloud Platform fundamentals and Vertex AI credits.",
            "icon": "☁️",
        })
    elif "events calendar" in combined.lower() or "registration" in combined.lower():
        cards.append({
            "name": "GDG USAR Academic Events 2026",
            "date": "Throughout 2026 Academic Year",
            "venue": "USAR Campus / Virtual",
            "registration": "Opens 2 weeks before event date via chapter portal",
            "details": "Free and non-transferable tickets for registered USAR students.",
            "icon": "📅",
        })
    return cards


# ---------------------------------------------------------------------------
# Helper: Follow-up Suggestions & Matched Words Highlighter
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
        elif "Executive" in sec or "Team" in sec or "teams" in f_name.lower():
            suggestions.append("Who leads the Technical and Media wings of GDG USAR?")
            seen.add("team")
        elif "Event" in sec or "Hackathon" in sec or "events" in f_name.lower():
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


def highlight_matched_words(snippet: str, query: str) -> str:
    words = [re.escape(w) for w in query.split() if len(w) > 3]
    if not words:
        return snippet
    pattern = re.compile(rf"(\b(?:{'|'.join(words)})\b)", re.IGNORECASE)
    return pattern.sub(
        r"<mark style='background-color: #5A4500; color: #FFF176; padding: 1px 3px; border-radius: 3px;'>\1</mark>",
        snippet,
    )


def stream_words(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)


# ---------------------------------------------------------------------------
# Hero Welcome Screen: Equal Height Cards & Aligned Buttons
# ---------------------------------------------------------------------------
if len(st.session_state.messages) == 0:
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-badge">✨ Grounded Multi-Document Knowledge Assistant</div>
            <h1 class="hero-title">How can we help you today?</h1>
            <p class="hero-tagline">Ask questions about our official handbook, technical workshops, 2026 events, executive leads, and project guidelines.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    starter_cards = [
        {
            "icon": "🏢",
            "category": "Support Desk",
            "question": "What are the Student Support Desk's opening hours?",
            "desc": "Room 104 hours, lunch breaks & emergency contacts",
        },
        {
            "icon": "📅",
            "category": "Events & Hackathons",
            "question": "When is HackUSAR 2026 scheduled and where is the venue?",
            "desc": "Date, venue, theme, team sizes, and registration",
        },
        {
            "icon": "🎓",
            "category": "Workshops",
            "question": "Does attending a workshop automatically give me a certificate?",
            "desc": "Official certification eligibility & evaluation policies",
        },
        {
            "icon": "📁",
            "category": "Project Showcase",
            "question": "What files should a project submission include, and what should the README cover?",
            "desc": "Deliverables (README, DECISIONS, AI_USAGE) & rules",
        },
        {
            "icon": "👥",
            "category": "About GDG USAR",
            "question": "Who is the current community lead of GDG On Campus USAR?",
            "desc": "Executive board, leads, faculty advisor, and wings",
        },
        {
            "icon": "🛡️",
            "category": "Try me (Unanswerable)",
            "question": "What is the total annual funding budget allocated to GDG USAR for 2027?",
            "desc": "Test out-of-scope fallback & zero-hallucination defense",
        },
    ]

    selected_starter = None

    # Render in 2 rows of 3 columns (Equal height cards + seamlessly aligned buttons)
    for row_start in [0, 3]:
        cols = st.columns(3)
        for i in range(3):
            idx = row_start + i
            card = starter_cards[idx]
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="suggestion-card-box">
                        <div class="suggestion-card-top">
                            <span class="suggestion-icon">{card['icon']}</span>
                            <span class="suggestion-cat">{card['category']}</span>
                        </div>
                        <div class="suggestion-q">{card['question']}</div>
                        <div class="suggestion-desc">{card['desc']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="card-btn-container">', unsafe_allow_html=True)
                if st.button("Ask Question →", key=f"btn_card_{idx}", use_container_width=True):
                    selected_starter = card["question"]
                st.markdown('</div>', unsafe_allow_html=True)

    if selected_starter:
        st.session_state.triggered_starter = selected_starter
        st.rerun()


# ---------------------------------------------------------------------------
# Assistant Response Renderer
# ---------------------------------------------------------------------------
def render_assistant_response(msg_idx: Any, result: dict, query_context: str = "", is_new: bool = False):
    ans_text = result.get("answer", "")
    score = result.get("best_score", 0.0)
    latency = result.get("latency_s", 0.0)
    chunks = result.get("retrieved_chunks", [])
    guard = result.get("guard_triggered")
    error_msg = result.get("error")

    # 1. Error / Rate Limit Handling
    if error_msg:
        if "429" in error_msg or "quota" in error_msg.lower() or "exhausted" in error_msg.lower():
            st.warning(
                "⏳ **Free Tier Rate Limit Exceeded**: Google Gemini free-tier rate limits were momentarily reached. Please wait ~15–30 seconds and retry your question.",
                icon="⚠️",
            )
            return
        st.error(f"Error executing query: {error_msg}")
        return

    # 2. Check Fallback Status
    is_fallback = FALLBACK_RESPONSE.lower() in ans_text.lower() or guard in ["retrieval_guard", "prompt_guard"]

    # Header with confidence badge (Google palette)
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            {badge_html}
            <span style="font-size: 0.8rem; color: var(--text-muted);">⏱️ {latency}s | Match score: {score:.3f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Render Event Cards if events_calendar_2026.md was retrieved
    if not is_fallback and chunks:
        event_cards = extract_event_cards(chunks)
        for ev in event_cards:
            st.markdown(
                f"""
                <div class="event-banner-card">
                    <div class="event-banner-header">
                        <span class="event-badge">{ev['icon']} OFFICIAL EVENT SCHEDULE</span>
                    </div>
                    <div class="event-title">{ev['name']}</div>
                    <div class="event-grid">
                        <div class="event-item"><span class="event-label">📅 Date:</span><span class="event-val">{ev['date']}</span></div>
                        <div class="event-item"><span class="event-label">📍 Venue:</span><span class="event-val">{ev['venue']}</span></div>
                        <div class="event-item"><span class="event-label">🎟️ Registration:</span><span class="event-val">{ev['registration']}</span></div>
                        <div class="event-item"><span class="event-label">💡 Focus:</span><span class="event-val">{ev['details']}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Fallback Card vs Normal Answer Prose
    if is_fallback:
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
        # Separate main answer from sources if present in raw text
        if "Sources:" in ans_text:
            prose, _ = ans_text.split("Sources:", 1)
        else:
            prose = ans_text

        # Typing effect on freshly generated message vs instant render
        if is_new:
            st.write_stream(stream_words(prose.strip()))
        else:
            st.markdown(prose.strip())

        # Expandable Source Cards (collapsed by default)
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

    # 5. Answer Toolbar: Copy, Thumbs Up/Down, Regenerate
    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([0.16, 0.12, 0.12, 0.22, 0.38])
    with t_col1:
        if st.button("📋 Copy", key=f"btn_cp_{msg_idx}", help="View copyable text"):
            st.session_state[f"show_code_{msg_idx}"] = not st.session_state.get(f"show_code_{msg_idx}", False)
    with t_col2:
        if st.button("👍", key=f"thumb_up_{msg_idx}", help="Helpful"):
            save_user_feedback(
                query_context,
                ans_text,
                "positive",
                st.session_state.active_strategy,
                st.session_state.search_scope,
                score,
            )
            st.toast("Thank you! Feedback recorded 👍", icon="✅")
    with t_col3:
        if st.button("👎", key=f"thumb_down_{msg_idx}", help="Not helpful"):
            save_user_feedback(
                query_context,
                ans_text,
                "negative",
                st.session_state.active_strategy,
                st.session_state.search_scope,
                score,
            )
            st.toast("Feedback recorded. We will improve! 👎", icon="📝")
    with t_col4:
        if st.button("🔄 Regenerate", key=f"btn_regen_{msg_idx}", help="Re-run this question"):
            if isinstance(msg_idx, int) and msg_idx > 0 and st.session_state.messages[msg_idx - 1]["role"] == "user":
                prev_q = st.session_state.messages[msg_idx - 1]["content"]
                st.session_state.messages.pop(msg_idx)
                st.session_state.messages.pop(msg_idx - 1)
                st.session_state.triggered_starter = prev_q
                st.rerun()

    # Show copyable code block if toggled
    if st.session_state.get(f"show_code_{msg_idx}", False):
        st.code(ans_text, language="markdown")

    # 6. Contextual Follow-up Suggestions Chips
    if not is_fallback and chunks:
        followups = generate_followup_suggestions(chunks)
        if followups:
            st.markdown(
                "<span style='font-size:0.8rem; color:var(--text-muted);'>💡 Related Follow-up Questions:</span>",
                unsafe_allow_html=True,
            )
            f_cols = st.columns(len(followups))
            for f_idx, f_query in enumerate(followups):
                with f_cols[f_idx]:
                    if st.button(f"🔍 {f_query}", key=f"fu_{msg_idx}_{f_idx}", use_container_width=True):
                        st.session_state.triggered_starter = f_query
                        st.rerun()


# ---------------------------------------------------------------------------
# Query Execution Engine
# ---------------------------------------------------------------------------
def execute_query(query: str):
    if not query.strip():
        return

    st.session_state.messages.append({"role": "user", "content": query})

    if st.session_state.compare_mode:
        with st.chat_message("assistant", avatar="⚖️"):
            thinking_ph = st.empty()
            thinking_ph.markdown(
                """
                <div class="thinking-container">
                    <div class="thinking-title">⚖️ <strong>Comparing Strategies...</strong> Searching handbook with both <code>char_500</code> & <code>recursive_200</code></div>
                    <div class="skeleton-shimmer">
                        <div class="skeleton-line full"></div>
                        <div class="skeleton-line long"></div>
                        <div class="skeleton-line medium"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
            thinking_ph.empty()

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
        with st.chat_message("assistant", avatar="🎓"):
            thinking_ph = st.empty()
            thinking_ph.markdown(
                """
                <div class="thinking-container">
                    <div class="thinking-title">🔍 <strong>Reading the handbook...</strong> Verifying grounded facts from knowledge base</div>
                    <div class="skeleton-shimmer">
                        <div class="skeleton-line full"></div>
                        <div class="skeleton-line long"></div>
                        <div class="skeleton-line medium"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            res = answer_question(
                question=query,
                strategy=st.session_state.active_strategy,
                top_k=st.session_state.top_k,
                threshold=st.session_state.threshold,
                scope=st.session_state.search_scope,
                allow_mock_fallback=True,
            )
            thinking_ph.empty()

        st.session_state.messages.append({
            "role": "assistant",
            "result": res,
            "strategy": st.session_state.active_strategy,
            "scope": st.session_state.search_scope,
            "is_new": True,
        })

        # Update Session Analytics
        st.session_state.session_stats["queries_count"] += 1
        st.session_state.session_stats["total_confidence"] += res["best_score"]
        st.session_state.session_stats["total_latency"] += res["latency_s"]
        if FALLBACK_RESPONSE.lower() in res["answer"].lower():
            st.session_state.session_stats["fallback_count"] += 1


# Trigger chip question if queued
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
        is_fresh = msg.get("is_new", False)
        with st.chat_message("assistant", avatar="🎓"):
            st.caption(f"Strategy: `{msg.get('strategy', 'default')}` | Scope: `{msg.get('scope', 'all')}`")
            render_assistant_response(idx, msg["result"], query_context=user_query, is_new=is_fresh)
            if is_fresh:
                msg["is_new"] = False

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
# Chat Tools Toolbar (Clear Chat, Export, Download)
# ---------------------------------------------------------------------------
if len(st.session_state.messages) > 0:
    st.markdown("---")
    tool_col1, tool_col2, tool_col3 = st.columns([0.3, 0.4, 0.3])

    with tool_col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, help="Reset conversation history"):
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


# ---------------------------------------------------------------------------
# Footer Layout
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="app-footer">
        <div class="footer-brand">
            <span style="color:#4285F4;font-weight:800;">G</span><span style="color:#EA4335;font-weight:800;">D</span><span style="color:#FBBC04;font-weight:800;">G</span>
            <span>On Campus USAR &bull; Knowledge Assistant</span>
        </div>
        <div class="footer-note">
            Strict zero-hallucination defense &bull; Multi-document grounded RAG &bull; Google Developer Student Clubs USAR
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
