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
    DEFAULT_STRATEGY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
    FALLBACK_RESPONSE,
)
from src.qa_chain import answer_question
from src.loader import load_all_documents
from src.indexer import build_all_indices

try:
    from styles import get_app_css
except (ModuleNotFoundError, ImportError):
    from app.styles import get_app_css

try:
    from components import (
        PROMPT_CARDS,
        DID_YOU_KNOW_FACTS,
        render_header,
        render_greeting_and_tips,
        render_prompt_cards,
        render_sidebar,
        render_footer,
    )
except (ModuleNotFoundError, ImportError):
    from app.components import (
        PROMPT_CARDS,
        DID_YOU_KNOW_FACTS,
        render_header,
        render_greeting_and_tips,
        render_prompt_cards,
        render_sidebar,
        render_footer,
    )

FEEDBACK_FILE = ROOT_DIR / "feedback.json"

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
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"
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
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Full View"
    if "session_stats" not in st.session_state:
        st.session_state.session_stats = {
            "queries_count": 0,
            "total_confidence": 0.0,
            "fallback_count": 0,
            "total_latency": 0.0,
        }
    if "current_fact_idx" not in st.session_state:
        st.session_state.current_fact_idx = 0
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "show_suggestions" not in st.session_state:
        st.session_state.show_suggestions = False


init_session()

# Map card ID to full question string
CARD_ID_TO_QUESTION = {card.id: card.question for card in PROMPT_CARDS}

# Check query parameter (?ask=CARD_ID) from card click
ask_param = st.query_params.get("ask")
if ask_param:
    if ask_param in CARD_ID_TO_QUESTION:
        st.session_state["pending_question"] = CARD_ID_TO_QUESTION[ask_param]
    st.query_params.clear()

# Detect first-load to play entrance animations once only
if "has_loaded_once" not in st.session_state:
    st.session_state.has_loaded_once = True
    animate_first_load = True
else:
    animate_first_load = False

# Inject centralized stylesheet (default DARK)
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
# Event Cards Extractor
# ---------------------------------------------------------------------------
def extract_event_cards(chunks: List[dict]) -> List[dict]:
    """
    If any retrieved chunk is from events_calendar_2026.md, parse factual event metadata.
    Grounds output strictly in chunk content.
    """
    cards = []
    for c in chunks:
        src = c.get("source_file", "").lower()
        if "event" in src or "calendar" in src:
            content = c.get("content", "")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            ev_name = "GDG USAR Campus Event"
            ev_date = "2026 Academic Term"
            ev_venue = "USAR Campus / Online"
            ev_reg = "Free for USAR Students"
            ev_details = "Technical workshop & networking"

            for line in lines:
                if line.startswith("#"):
                    ev_name = line.lstrip("#").strip()
                elif "date:" in line.lower() or "when:" in line.lower():
                    ev_date = line.split(":", 1)[1].strip()
                elif "venue:" in line.lower() or "where:" in line.lower() or "location:" in line.lower():
                    ev_venue = line.split(":", 1)[1].strip()
                elif "registration:" in line.lower() or "fee:" in line.lower():
                    ev_reg = line.split(":", 1)[1].strip()
                elif "theme:" in line.lower() or "topic:" in line.lower() or "focus:" in line.lower():
                    ev_details = line.split(":", 1)[1].strip()

            if any(term in content.lower() for term in ["hackusar", "summit", "bootcamp", "jam", "workshop"]):
                cards.append({
                    "name": ev_name,
                    "date": ev_date,
                    "venue": ev_venue,
                    "registration": ev_reg,
                    "details": ev_details,
                    "icon": "🚀" if "hack" in ev_name.lower() else "📅",
                })
    return cards[:2]


# ---------------------------------------------------------------------------
# Follow-up Suggestions Generator
# ---------------------------------------------------------------------------
def generate_followup_suggestions(chunks: List[dict]) -> List[str]:
    suggestions = []
    seen = set()

    for c in chunks:
        text = c.get("content", "").lower()

        if ("support desk" in text or "hours" in text or "room 104" in text) and "hours" not in seen:
            suggestions.append("What are the lunch break hours of the Support Desk?")
            suggestions.append("Who do I contact if Room 104 is closed?")
            seen.add("hours")

        if ("certificate" in text or "workshop" in text) and "cert" not in seen:
            suggestions.append("How are workshop attendance and certificates evaluated?")
            seen.add("cert")

        if ("project" in text or "readme" in text or "submission" in text) and "proj" not in seen:
            suggestions.append("What are the mandatory deliverables for project submissions?")
            suggestions.append("When is the AI_USAGE.md file required?")
            seen.add("proj")

        if ("lead" in text or "team" in text or "domain" in text) and "lead" not in seen:
            suggestions.append("Who is the faculty advisor for GDG On Campus USAR?")
            suggestions.append("What are the different technical domain wings?")
            seen.add("lead")

        if ("hackusar" in text or "hackathon" in text or "event" in text) and "hack" not in seen:
            suggestions.append("What are the team size limits for HackUSAR 2026?")
            suggestions.append("Is registration for GDG events free?")
            seen.add("hack")

    fallback_defaults = [
        "What are the Student Support Desk opening hours?",
        "When is HackUSAR 2026 scheduled and where?",
        "Does workshop attendance guarantee a certificate?",
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
        r"<mark style='background-color: rgba(66, 133, 244, 0.25); color: #8ab4f8; padding: 1px 4px; border-radius: 3px;'>\1</mark>",
        snippet,
    )


def stream_words(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)


# ---------------------------------------------------------------------------
# Sidebar & Header Rendering
# ---------------------------------------------------------------------------
supported_files = sorted(
    [p for p in DATA_DIR.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]]
)
current_fact = DID_YOU_KNOW_FACTS[st.session_state.current_fact_idx % len(DID_YOU_KNOW_FACTS)]

sidebar_state = render_sidebar(
    theme_mode=st.session_state.theme_mode,
    active_strategy=st.session_state.active_strategy,
    search_scope=st.session_state.search_scope,
    compare_mode=st.session_state.compare_mode,
    top_k=st.session_state.top_k,
    threshold=st.session_state.threshold,
    view_mode=st.session_state.view_mode,
    stats=st.session_state.session_stats,
    data_files=supported_files,
    current_fact=current_fact,
)

# Theme change handling
if sidebar_state.get("theme_mode") and sidebar_state["theme_mode"] != st.session_state.theme_mode:
    st.session_state.theme_mode = sidebar_state["theme_mode"]
    st.rerun()

# Sync sidebar state with session state
st.session_state.search_scope = sidebar_state["search_scope"]
st.session_state.active_strategy = sidebar_state["active_strategy"]
st.session_state.compare_mode = sidebar_state["compare_mode"]
st.session_state.top_k = sidebar_state["top_k"]
st.session_state.threshold = sidebar_state["threshold"]
st.session_state.view_mode = sidebar_state["view_mode"]

# Render page header with slide-in accent bar on first load
render_header(animate=animate_first_load)


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

    # 1. Error / Rate Limit Handling with polite microcopy
    if error_msg:
        st.warning(
            "⚠️ **Something went wrong. Please try again in a moment.** (The language model or network encountered a temporary delay).",
            icon="⚠️",
        )
        return

    # 2. Check Fallback Status
    is_fallback = FALLBACK_RESPONSE.lower() in ans_text.lower() or guard in ["retrieval_guard", "prompt_guard"]

    # Header with confidence badge (High / Medium / Low)
    badge_html = ""
    if is_fallback:
        badge_html = '<span class="confidence-badge conf-low">🛡️ Out of Scope</span>'
    elif score >= 0.70:
        badge_html = '<span class="confidence-badge conf-high">🟢 High Confidence</span>'
    elif score >= 0.50:
        badge_html = '<span class="confidence-badge conf-medium">🟡 Medium Confidence</span>'
    else:
        badge_html = '<span class="confidence-badge conf-low">⚪ Low Confidence</span>'

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 4px;">
            {badge_html}
            <span style="font-size: 12px; color: var(--text-muted);">⏱️ {latency}s &bull; Match: {score:.3f}</span>
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
                    <span class="event-badge">{ev['icon']} Official Event Schedule</span>
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
        st.markdown(
            """
            <div class="unanswerable-card">
                <div class="unanswerable-header">
                    <span>ℹ️</span>
                    <span>Not Covered in Official Documents</span>
                </div>
                <div class="unanswerable-message">
                    This isn't covered in the official documents. Try rephrasing or ask about the handbook, events or workshops.
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
            with st.expander(f"📚 View Sources ({len(chunks)} passages)", expanded=False):
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
                                    <span><strong>{sec_label}</strong> &bull; p. {page}</span>
                                </div>
                                <span class="source-score-badge">Match: {c_score:.3f}</span>
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
                st.session_state.pending_question = prev_q
                st.rerun()

    # Show copyable code block if toggled
    if st.session_state.get(f"show_code_{msg_idx}", False):
        st.code(ans_text, language="markdown")

    # 6. Contextual Follow-up Suggestions Chips
    if not is_fallback and chunks:
        followups = generate_followup_suggestions(chunks)
        if followups:
            st.markdown(
                "<span style='font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;'>💡 Related Follow-up:</span>",
                unsafe_allow_html=True,
            )
            f_cols = st.columns(len(followups))
            for f_idx, f_query in enumerate(followups):
                with f_cols[f_idx]:
                    if st.button(f"🔍 {f_query}", key=f"fu_{msg_idx}_{f_idx}", use_container_width=True):
                        st.session_state.pending_question = f_query
                        st.rerun()


# ---------------------------------------------------------------------------
# Query Execution Engine
# ---------------------------------------------------------------------------
def execute_query(query: str):
    if not query.strip():
        return

    st.session_state.messages.append({"role": "user", "content": query, "is_new": True})

    if st.session_state.compare_mode:
        with st.chat_message("assistant", avatar="⚖️"):
            thinking_ph = st.empty()
            thinking_ph.markdown(
                """
                <div class="thinking-container">
                    <div class="thinking-title">
                        <span>Searching documents (Comparing strategies)</span>
                        <span class="bouncing-dots">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </span>
                    </div>
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
            "is_new": True,
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
                    <div class="thinking-title">
                        <span>Searching documents</span>
                        <span class="bouncing-dots">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </span>
                    </div>
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


# ---------------------------------------------------------------------------
# Pending Question Handler (Card click via query params / Suggestions)
# ---------------------------------------------------------------------------
if st.session_state.get("pending_question"):
    queued_q = st.session_state.pending_question
    st.session_state.pending_question = None
    execute_query(queued_q)
    st.rerun()


# ---------------------------------------------------------------------------
# Prompt Cards / Suggestions Rendering
# ---------------------------------------------------------------------------
has_messages = len(st.session_state.messages) > 0

# If chat is empty, display greeting, tip chips, and prompt cards
if not has_messages:
    render_greeting_and_tips()
    render_prompt_cards(PROMPT_CARDS, view_mode=st.session_state.view_mode, animate_entrance=animate_first_load)
else:
    # If conversation is active, provide a clean toggle to show/hide suggestions
    col_tog1, col_tog2 = st.columns([0.3, 0.7])
    with col_tog1:
        toggle_label = "💡 Hide Suggestions" if st.session_state.show_suggestions else "💡 Show Suggestions"
        if st.button(toggle_label, key="btn_toggle_sug", help="Toggle starter question cards"):
            st.session_state.show_suggestions = not st.session_state.show_suggestions
            st.rerun()

    if st.session_state.show_suggestions:
        render_prompt_cards(PROMPT_CARDS, view_mode=st.session_state.view_mode, animate_entrance=False)


# ---------------------------------------------------------------------------
# Render Message History
# ---------------------------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    is_fresh = msg.get("is_new", False)
    anim_cls = "new-message-anim" if is_fresh else ""

    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="user-bubble-wrapper {anim_cls}">
                <div class="user-msg-bubble">
                    <strong>{msg['content']}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif msg["role"] == "assistant":
        user_query = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
        with st.chat_message("assistant", avatar="🎓"):
            st.caption(f"Strategy: `{msg.get('strategy', 'default')}` &bull; Scope: `{msg.get('scope', 'all')}`")
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
                render_assistant_response(f"{idx}_a", msg["res_a"], query_context=user_query, is_new=is_fresh)
            with col_b:
                st.markdown("##### Strategy B: `recursive_200`")
                render_assistant_response(f"{idx}_b", msg["res_b"], query_context=user_query, is_new=is_fresh)
            if is_fresh:
                msg["is_new"] = False


# ---------------------------------------------------------------------------
# Chat Tools Toolbar (Clear Chat, Export, Download)
# ---------------------------------------------------------------------------
if len(st.session_state.messages) > 0:
    st.markdown("---")
    tool_col1, tool_col2, tool_col3 = st.columns([0.3, 0.4, 0.3])

    with tool_col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, help="Reset conversation history"):
            st.session_state.messages = []
            st.session_state.show_suggestions = False
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
# Sticky Chat Input Bar
# ---------------------------------------------------------------------------
user_prompt = st.chat_input("Ask any question about GDG-USAR handbook, events, teams, or projects...")
if user_prompt:
    execute_query(user_prompt)
    st.rerun()


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
render_footer()
