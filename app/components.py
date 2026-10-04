"""
Modular UI Components for Airaa — GDG On Campus USAR Knowledge Assistant.
Production-grade dark theme default with single CSS grid container for 100% uniform card heights.
Contains:
1. Structured prompt cards dataclass and data registry.
2. render_header(): Accent line, title, and "Grounded in official documents" status chip.
3. render_greeting_and_tips(): First-load welcome banner and 3 starter tips.
4. render_prompt_cards(): Single HTML CSS grid with grid-auto-rows: 1fr and ?ask=CARD_ID links.
5. render_sidebar(): Dark surface with small uppercase section headings, theme switcher, and controls.
6. render_footer(): Clean GDG USAR branding footer.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import streamlit as st

from src.config import (
    CHUNK_STRATEGIES,
    DATA_DIR,
    DEFAULT_STRATEGY,
)
from src.indexer import build_all_indices

# Verified Document Facts for Sidebar
DID_YOU_KNOW_FACTS = [
    "📍 **Room 104, Admin Block**: The Student Support Desk is open Monday through Friday, 10:00 AM to 4:00 PM.",
    "🚀 **HackUSAR 2026**: A 24-hour hackathon scheduled for Nov 14–15, 2026 focusing on AI and Sustainable Cities.",
    "📜 **Workshop Certificates**: Attendance does NOT automatically grant a certificate; evaluation criteria must be met.",
    "📁 **Project Deliverables**: All project submissions require a `README.md`, `DECISIONS.md`, and `AI_USAGE.md` (if AI tools were used).",
    "👤 **Community Leadership**: Aarav Sharma is the GDG On Campus USAR Community Lead for the 2026–2027 term.",
    "🏛️ **Faculty Advisor**: Dr. Neha Verma (Associate Professor, Dept of AI & Data Science) serves as the faculty sponsor.",
    "🎟️ **Free Registration**: Tickets for all GDG USAR technical events are free for registered USAR students but non-transferable.",
    "💬 **Discord Community**: All official announcements, study jam voice lounges, and mentor Q&A channels are on Discord.",
]


@dataclass
class PromptCard:
    """Structured representation of starter question cards."""
    id: str
    category: str
    icon: str
    question: str
    short_q: str
    description: str
    accent: str
    badge_class: str


# 6 Prompt cards grouped by category with one calm color per category
PROMPT_CARDS: List[PromptCard] = [
    PromptCard(
        id="desk",
        category="SUPPORT DESK",
        icon="🏢",
        question="What are the Student Support Desk's opening hours?",
        short_q="Desk hours & Room 104",
        description="Room 104 hours, lunch breaks, and holiday closure policies.",
        accent="#4285F4",
        badge_class="badge-blue",
    ),
    PromptCard(
        id="events",
        category="EVENTS",
        icon="🚀",
        question="When is HackUSAR 2026 scheduled and where is the venue?",
        short_q="HackUSAR dates & venue",
        description="Event dates, venue, themes, team sizes, and registration steps.",
        accent="#34A853",
        badge_class="badge-green",
    ),
    PromptCard(
        id="workshops",
        category="WORKSHOPS",
        icon="📜",
        question="Does attending a workshop automatically give me a certificate?",
        short_q="Certificate eligibility rule",
        description="Official criteria for certification, attendance tracking, and evaluation.",
        accent="#FBBC04",
        badge_class="badge-amber",
    ),
    PromptCard(
        id="projects",
        category="PROJECTS",
        icon="📁",
        question="What files should a project submission include, and what should the README cover?",
        short_q="Required files & structure",
        description="Required files (README, DECISIONS, AI_USAGE) and structure rules.",
        accent="#A855F7",
        badge_class="badge-purple",
    ),
    PromptCard(
        id="about",
        category="ABOUT GDG",
        icon="👥",
        question="Who is the current community lead of GDG On Campus USAR?",
        short_q="Community leadership lead",
        description="Executive team roster, domain wings, and faculty advisor.",
        accent="#14B8A6",
        badge_class="badge-teal",
    ),
    PromptCard(
        id="unanswerable",
        category="UNANSWERABLE",
        icon="🛡️",
        question="What is the total annual funding budget allocated to GDG USAR for 2027?",
        short_q="2027 annual club budget",
        description="Test strict out-of-scope fallback & zero-hallucination defense.",
        accent="#9AA0A6",
        badge_class="badge-grey",
    ),
]


def render_header(animate: bool = False):
    """Renders the top rainbow accent line, branding mark, and status badge."""
    accent_bar_class = "gdg-accent-bar animate-slide-in" if animate else "gdg-accent-bar"
    st.markdown(f'<div class="{accent_bar_class}"></div>', unsafe_allow_html=True)
    header_html = (
        '<div class="main-header">'
        '<div class="header-top-row">'
        '<div class="page-title">'
        '<span class="brand-g">G</span><span class="brand-d">D</span><span class="brand-g2">G</span>&nbsp;<span class="brand-campus">On Campus USAR &mdash; Airaa</span>'
        '</div>'
        '<div class="status-chip">'
        '<span class="status-dot"></span>'
        '<span>Grounded in official documents</span>'
        '</div>'
        '</div>'
        '<div class="page-subtitle">'
        'Ask questions about our official handbook, technical workshops, 2026 events, executive leads, and project guidelines.'
        '</div>'
        '<div class="header-divider"></div>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def render_greeting_and_tips():
    """Renders the empty-state greeting banner and 3 helpful tip chips."""
    greeting_html = (
        '<div class="greeting-banner">'
        '<div class="greeting-title">👋 Welcome to Airaa — your GDG On Campus USAR Knowledge Assistant</div>'
        '<div class="greeting-desc">Select a starter topic below or type into the search bar to query official campus documents.</div>'
        '<div class="tip-chips-row">'
        '<div class="tip-chip">🏢 Tip: Ask for room locations & hours</div>'
        '<div class="tip-chip">🚀 Tip: Check HackUSAR dates, tracks & team sizes</div>'
        '<div class="tip-chip">🛡️ Tip: Unverified topics trigger safe fallback</div>'
        '</div>'
        '</div>'
    )
    st.markdown(greeting_html, unsafe_allow_html=True)


def render_prompt_cards(cards: List[PromptCard], view_mode: str = "Full View", animate_entrance: bool = False):
    """
    Renders ALL 6 cards as ONE HTML block (st.markdown with unsafe_allow_html=True)
    inside a single CSS grid container (.card-grid).
    Because of grid-auto-rows: 1fr and flexbox height: 100%, all cards end up exactly
    the same height.
    Clicking any card uses <a href="?ask=CARD_ID" target="_self"> to trigger the query.
    """
    anim_class = "animate-entrance" if animate_entrance else ""

    if view_mode == "Compact View":
        # Force compact scrollable chips across all viewports
        chips_html = '<div class="chips-scroll-wrapper">'
        for idx, card in enumerate(cards):
            delay_style = f"animation-delay: {idx * 0.05}s;" if animate_entrance else ""
            chips_html += (
                f'<a href="?ask={card.id}" target="_self" class="starter-chip {anim_class}" style="{delay_style}">'
                f'<span class="category-badge {card.badge_class}">{card.icon} {card.category}</span>'
                f'<span class="starter-chip-text">{card.short_q}</span>'
                f'</a>'
            )
        chips_html += "</div>"
        full_compact = (
            f'<div style="margin-bottom: 8px; font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em;">'
            f'💡 Quick Starters:</div>'
            f'{chips_html}'
        )
        st.markdown(full_compact, unsafe_allow_html=True)
    else:
        # Full view mode:
        # 1. Desktop & Tablet: .card-grid (3 cols >1024px, 2 cols 640-1024px)
        # 2. Mobile (<640px): .mobile-chips-wrapper (responsive switch via CSS)
        grid_items_html = ""
        for idx, card in enumerate(cards):
            delay_style = f"animation-delay: {idx * 0.05}s;" if animate_entrance else ""
            grid_items_html += (
                f'<a href="?ask={card.id}" target="_self" class="suggestion-card {anim_class}" style="{delay_style}">'
                f'<div class="card-top-content">'
                f'<span class="category-badge {card.badge_class}">{card.icon} {card.category}</span>'
                f'<div class="card-question-text">{card.question}</div>'
                f'<div class="card-desc-text">{card.description}</div>'
                f'</div>'
                f'<div class="card-btn">Ask Question &rarr;</div>'
                f'</a>'
            )

        mobile_chips_html = ""
        for idx, card in enumerate(cards):
            delay_style = f"animation-delay: {idx * 0.05}s;" if animate_entrance else ""
            mobile_chips_html += (
                f'<a href="?ask={card.id}" target="_self" class="starter-chip {anim_class}" style="{delay_style}">'
                f'<span class="category-badge {card.badge_class}">{card.icon} {card.category}</span>'
                f'<span class="starter-chip-text">{card.short_q}</span>'
                f'</a>'
            )

        full_html = (
            f'<div class="card-grid">{grid_items_html}</div>'
            f'<div class="mobile-chips-wrapper"><div class="chips-scroll-wrapper">{mobile_chips_html}</div></div>'
        )
        st.markdown(full_html, unsafe_allow_html=True)


def render_sidebar(
    theme_mode: str,
    active_strategy: str,
    search_scope: str,
    compare_mode: bool,
    top_k: int,
    threshold: float,
    view_mode: str,
    stats: Dict[str, Any],
    data_files: List[Any],
    current_fact: str,
) -> Dict[str, Any]:
    """
    Renders dark surface sidebar with small uppercase section headings,
    consistent vertical spacing, short help text, and returns widget values.
    """
    with st.sidebar:
        # Section 1: THEME
        st.markdown('<div class="sidebar-heading">Theme</div>', unsafe_allow_html=True)
        theme_choice = st.radio(
            "Theme Mode",
            options=["🌙 Dark", "☀️ Light"],
            index=0 if theme_mode == "dark" else 1,
            label_visibility="collapsed",
            horizontal=True,
        )
        st.markdown('<div class="sidebar-help">Default production dark theme or clean light theme.</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Section 2: SEARCH SCOPE
        st.markdown('<div class="sidebar-heading">Search Scope</div>', unsafe_allow_html=True)
        scope_options = ["All documents", "Handbook only"]
        scope_choice = st.radio(
            "Search Scope",
            options=scope_options,
            index=0 if search_scope == "all" else 1,
            label_visibility="collapsed",
        )
        st.markdown('<div class="sidebar-help">Query all campus documents or restrict strictly to Task 3 handbook.</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Section 3: LAYOUT VIEW
        st.markdown('<div class="sidebar-heading">Layout View</div>', unsafe_allow_html=True)
        view_choice = st.radio(
            "Suggestion Cards View",
            options=["Full View", "Compact View"],
            index=0 if view_mode == "Full View" else 1,
            label_visibility="collapsed",
            horizontal=True,
        )
        st.markdown('<div class="sidebar-help">Switch between detailed 3x2 card grid and compact chips.</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Section 4: PIPELINE SETTINGS
        st.markdown('<div class="sidebar-heading">Pipeline Settings</div>', unsafe_allow_html=True)
        strategy_options = list(CHUNK_STRATEGIES.keys())
        strat_choice = st.selectbox(
            "Chunking Strategy",
            options=strategy_options,
            index=strategy_options.index(active_strategy) if active_strategy in strategy_options else 0,
            help="Select text segmentation strategy.",
        )
        st.markdown('<div class="sidebar-help">Strategy A (Character 500) or Strategy B (Recursive 200).</div>', unsafe_allow_html=True)

        col_k, col_thresh = st.columns(2)
        with col_k:
            k_val = st.slider("Top K Chunks", min_value=1, max_value=5, value=top_k)
            st.markdown('<div class="sidebar-help">Passages retrieved</div>', unsafe_allow_html=True)
        with col_thresh:
            thresh_val = st.slider("Min Match Score", min_value=0.20, max_value=0.70, value=threshold, step=0.05)
            st.markdown('<div class="sidebar-help">Cosine cutoff (tau)</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Section 5: COMPARE MODE
        st.markdown('<div class="sidebar-heading">Compare Mode</div>', unsafe_allow_html=True)
        comp_toggle = st.toggle("Side-by-Side Comparison", value=compare_mode)
        st.markdown('<div class="sidebar-help">Queries both chunking strategies simultaneously side by side.</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Section 6: KNOWLEDGE BASE DOCUMENTS
        st.markdown('<div class="sidebar-heading">Knowledge Base</div>', unsafe_allow_html=True)
        with st.expander("📚 Loaded Documents", expanded=False):
            for f in data_files:
                is_hb = "task3" in f.name.lower() or "handbook" in f.name.lower()
                badge = "📘 [HANDBOOK]" if is_hb else "📄 [EXTRA]"
                size_kb = round(f.stat().st_size / 1024, 1)
                st.markdown(f"**{badge}** `{f.name}` ({size_kb} KB)")

            st.markdown("")
            if st.button("🔄 Rebuild Vector Index", use_container_width=True):
                with st.spinner("Rebuilding ChromaDB collections..."):
                    build_all_indices(force_rebuild=True)
                st.success("Vector index rebuilt!")
                st.rerun()

            st.markdown("##### ➕ Upload Document")
            uploaded_file = st.file_uploader(
                "Add .txt, .md, or .pdf",
                type=["txt", "md", "pdf"],
                help="Uploaded files are stored in data/ and indexed immediately.",
            )
            if uploaded_file is not None:
                dest = DATA_DIR / uploaded_file.name
                if not dest.exists():
                    with open(dest, "wb") as f_out:
                        f_out.write(uploaded_file.getbuffer())
                    with st.spinner(f"Indexing {uploaded_file.name}..."):
                        build_all_indices(force_rebuild=True)
                    st.success(f"Indexed {uploaded_file.name}!")
                    st.rerun()

        # Section 7: QUICK FACT
        st.markdown('<div class="sidebar-heading">Quick Fact</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="did-you-know-card">
                <div class="did-you-know-header">✨ Verified Handbook Fact</div>
                <div class="did-you-know-body">{current_fact}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🎲 Next Fact", key="btn_next_fact_sidebar", use_container_width=True):
            st.session_state["current_fact_idx"] = (st.session_state.get("current_fact_idx", 0) + 1) % len(DID_YOU_KNOW_FACTS)
            st.rerun()

        # Section 8: PIPELINE & ANALYTICS
        with st.expander("ℹ️ How It Works (RAG Pipeline)", expanded=False):
            st.markdown(
                """
                ```
                User Question
                      │
                      ▼
                Embeddings (all-MiniLM-L6-v2)
                Cosine Similarity Search (Top-K)
                      │
                      ▼
                Layer A: Retrieval Guard (Score < 0.40)
                      │
                      ▼
                Layer B: Grounded LLM Prompt
                (Strict handbook context only)
                      │
                      ▼
                Verified Answer + Citations
                ```
                """
            )

        with st.expander("📈 Session Analytics", expanded=False):
            q_count = stats.get("queries_count", 0)
            avg_conf = (stats["total_confidence"] / q_count) if q_count > 0 else 0.0
            fb_rate = ((stats["fallback_count"] / q_count) * 100) if q_count > 0 else 0.0
            avg_lat = (stats["total_latency"] / q_count) if q_count > 0 else 0.0

            st.metric("Questions Asked", q_count)
            st.metric("Avg Match Confidence", f"{avg_conf:.3f}")
            st.metric("Fallback Rate", f"{fb_rate:.1f}%")
            st.metric("Avg Latency", f"{avg_lat:.2f}s")

    return {
        "theme_mode": "dark" if "Dark" in theme_choice else "light",
        "search_scope": "all" if scope_choice == "All documents" else "handbook",
        "active_strategy": strat_choice,
        "compare_mode": comp_toggle,
        "top_k": k_val,
        "threshold": thresh_val,
        "view_mode": view_choice,
    }


def render_footer():
    """Renders a clean footer with GDG USAR branding and required notice."""
    st.markdown(
        """
        <div class="app-footer">
            <div class="footer-brand">
                <span style="color:#4285F4;font-weight:700;">G</span><span style="color:#EA4335;font-weight:700;">D</span><span style="color:#FBBC04;font-weight:700;">G</span>
                <span>On Campus USAR &bull; Airaa</span>
            </div>
            <div class="footer-note">
                Answers are generated only from the official documents. Built by GDG On Campus USAR.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
