"""
Styles and Theming for GDG On Campus USAR - Knowledge Assistant.
Provides centralized CSS variables, Google palette constants, and complete WCAG AA compliant theming
for both Dark and Light modes.
"""

# Google Developer Group Palette
GOOGLE_BLUE = "#4285F4"
GOOGLE_RED = "#EA4335"
GOOGLE_YELLOW = "#FBBC04"
GOOGLE_GREEN = "#34A853"


def get_app_css(theme_mode: str) -> str:
    """
    Returns the complete CSS stylesheet for the application.
    Supports both Dark (#121212 / #1E1E2E) and Light themes with WCAG AA/AAA contrast.
    """
    is_dark = theme_mode == "Dark"

    # Theme Variable Definitions
    if is_dark:
        bg_primary = "#121212"
        bg_secondary = "#181824"
        bg_card = "#1E1E2E"
        bg_subtle = "#252538"
        bg_hover = "#2C2C42"
        text_primary = "#F1F3F4"
        text_secondary = "#BDC1C6"
        text_muted = "#9AA0A6"
        border_color = "#2E2E42"
        btn_bg = "#252538"
        btn_text = "#F1F3F4"
        btn_border = "#4285F4"
        card_shadow = "0 4px 16px rgba(0, 0, 0, 0.4)"
        hero_grad = "linear-gradient(135deg, #8AB4F8 0%, #F28B82 35%, #FDD663 70%, #81C995 100%)"
        mark_bg = "#5A4500"
        mark_color = "#FFF176"
    else:
        bg_primary = "#FFFFFF"
        bg_secondary = "#F8F9FA"
        bg_card = "#FFFFFF"
        bg_subtle = "#F1F3F4"
        bg_hover = "#E8F0FE"
        text_primary = "#202124"
        text_secondary = "#3C4043"
        text_muted = "#5F6368"
        border_color = "#DADCE0"
        btn_bg = "#FFFFFF"
        btn_text = "#1A73E8"
        btn_border = "#4285F4"
        card_shadow = "0 2px 8px rgba(0, 0, 0, 0.06)"
        hero_grad = "linear-gradient(135deg, #1A73E8 0%, #D93025 35%, #F9AB00 70%, #188038 100%)"
        mark_bg = "#FFF176"
        mark_color = "#202124"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {{
        --bg-primary: {bg_primary};
        --bg-secondary: {bg_secondary};
        --bg-card: {bg_card};
        --bg-subtle: {bg_subtle};
        --bg-hover: {bg_hover};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --text-muted: {text_muted};
        --border-color: {border_color};
        --btn-bg: {btn_bg};
        --btn-text: {btn_text};
        --btn-border: {btn_border};
        --card-shadow: {card_shadow};
        --google-blue: {GOOGLE_BLUE};
        --google-red: {GOOGLE_RED};
        --google-yellow: {GOOGLE_YELLOW};
        --google-green: {GOOGLE_GREEN};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Global Streamlit App Overrides */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
        padding-top: 1.2rem !important;
    }}
    [data-testid="stSidebar"] * {{
        color: var(--text-primary);
    }}
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* Accent Rainbow Bar */
    .gdg-accent-bar {{
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #4285F4 0%, #EA4335 33%, #FBBC04 66%, #34A853 100%);
        border-radius: 2px;
        margin-bottom: 1.2rem;
    }}

    /* Header Layout - Single line title, responsive clamp, zero overlap */
    .main-header {{
        padding: 0.2rem 0 1.0rem 0;
        margin-bottom: 0.5rem;
    }}
    .brand-title {{
        font-size: clamp(1.35rem, 3.2vw, 2.25rem);
        font-weight: 800;
        letter-spacing: -0.025em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: flex;
        align-items: center;
        gap: 0.2rem;
        line-height: 1.2;
    }}
    .brand-g {{ color: #4285F4; }}
    .brand-d {{ color: #EA4335; }}
    .brand-g2 {{ color: #FBBC04; }}
    .brand-campus {{
        color: var(--text-primary);
        margin-left: 0.35rem;
    }}
    .brand-subtitle {{
        font-size: clamp(0.85rem, 1.3vw, 0.98rem);
        color: var(--text-secondary);
        margin-top: 0.35rem;
        line-height: 1.45;
    }}

    /* Sidebar Clean Grouping & Compact Headers (Fixes big gaps) */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {{
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        color: var(--text-muted) !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.25rem !important;
        padding-bottom: 0.15rem !important;
    }}
    [data-testid="stSidebar"] hr {{
        margin: 0.55rem 0 !important;
        border-color: var(--border-color) !important;
    }}
    .sidebar-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.7rem;
    }}
    .sidebar-card-title {{
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #4285F4;
        margin-bottom: 0.45rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }}

    /* Fix: Button styling - Readable in both Light & Dark themes */
    .stButton > button {{
        background-color: var(--btn-bg) !important;
        color: var(--btn-text) !important;
        border: 1.5px solid var(--btn-border) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 0.95rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }}
    .stButton > button:hover {{
        background-color: #4285F4 !important;
        color: #FFFFFF !important;
        border-color: #4285F4 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(66, 133, 244, 0.35) !important;
    }}
    .stButton > button * {{
        color: var(--btn-text) !important;
        font-weight: 600 !important;
    }}
    .stButton > button:hover * {{
        color: #FFFFFF !important;
    }}
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}

    /* Fix: Selectbox & Dropdown Menus in Dark Theme */
    div[data-baseweb="select"] > div {{
        background-color: var(--bg-card) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] div {{
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="menu"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
    }}
    ul[role="listbox"] {{
        background-color: var(--bg-card) !important;
    }}
    li[role="option"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }}
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {{
        background-color: var(--bg-hover) !important;
        color: #4285F4 !important;
    }}

    /* Fix: Chat Input Bar in Dark Theme */
    [data-testid="stChatInput"] {{
        background-color: transparent !important;
        padding-bottom: 0.6rem !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: var(--bg-card) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: none !important;
        font-size: 0.95rem !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: var(--text-muted) !important;
    }}
    [data-testid="stChatInput"] button {{
        background-color: #4285F4 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: #FFFFFF !important;
    }}
    [data-testid="stBottom"] > div {{
        background-color: var(--bg-primary) !important;
    }}

    /* Radio buttons & sliders */
    .stRadio label span {{
        color: var(--text-primary) !important;
    }}
    .stSlider label {{
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}

    /* Hero Welcome Screen */
    .hero-container {{
        text-align: center;
        padding: 1.5rem 1rem 1.6rem 1rem;
        max-width: 840px;
        margin: 0 auto;
    }}
    .hero-badge {{
        display: inline-block;
        padding: 0.25rem 0.8rem;
        background: var(--bg-subtle);
        border: 1px solid var(--border-color);
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #4285F4;
        margin-bottom: 0.8rem;
    }}
    .hero-title {{
        font-size: clamp(1.7rem, 4vw, 2.6rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.2;
        margin-bottom: 0.6rem;
        background: {hero_grad};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .hero-tagline {{
        font-size: clamp(0.95rem, 1.8vw, 1.1rem);
        color: var(--text-secondary);
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }}

    /* Fix: Suggestion Cards - Equal Height, Responsive Grid, Aligned Buttons */
    .suggestion-card-box {{
        background: var(--bg-card);
        border: 1.5px solid var(--border-color);
        border-bottom: none;
        border-radius: 14px 14px 0 0;
        padding: 1.15rem 1.15rem 0.85rem 1.15rem;
        height: 150px; /* Uniform height ensures all 6 cards line up perfectly */
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        box-shadow: var(--card-shadow);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }}
    .suggestion-card-box:hover {{
        border-color: #4285F4;
    }}
    .suggestion-card-top {{
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.45rem;
    }}
    .suggestion-icon {{
        font-size: 1.2rem;
    }}
    .suggestion-cat {{
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #4285F4;
    }}
    .suggestion-q {{
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.35;
        margin-bottom: 0.35rem;
        min-height: 44px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    .suggestion-desc {{
        font-size: 0.77rem;
        color: var(--text-secondary);
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}

    /* Card Action Button - Seamless Bottom Cap */
    .card-btn-container .stButton > button {{
        border-radius: 0 0 14px 14px !important;
        border-top: 1px dashed var(--border-color) !important;
        width: 100% !important;
        background: var(--bg-subtle) !important;
        margin-top: 0 !important;
    }}
    .card-btn-container .stButton > button:hover {{
        background-color: #4285F4 !important;
        color: #FFFFFF !important;
    }}

    /* Chat Messages styling */
    [data-testid="stChatMessage"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 14px !important;
        padding: 1.1rem 1.25rem !important;
        margin-bottom: 0.9rem !important;
        box-shadow: var(--card-shadow) !important;
        animation: fadeIn 0.3s ease-out;
    }}
    [data-testid="stChatMessage"] * {{
        color: var(--text-primary);
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Shimmer Skeleton & Thinking State */
    .thinking-container {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 4px solid #4285F4;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }}
    .thinking-title {{
        font-size: 0.92rem;
        font-weight: 600;
        color: #4285F4;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .skeleton-shimmer {{
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
    }}
    .skeleton-line {{
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(90deg, var(--bg-subtle) 25%, var(--bg-card) 50%, var(--bg-subtle) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.8s infinite ease-in-out;
    }}
    .skeleton-line.full {{ width: 100%; }}
    .skeleton-line.long {{ width: 85%; }}
    .skeleton-line.medium {{ width: 60%; }}

    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    /* Confidence Badges (Google Palette) */
    .badge-high {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: {"#13381B" if is_dark else "#E6F4EA"};
        color: {"#81C995" if is_dark else "#137333"};
        border: 1px solid {"#1E5629" if is_dark else "#CEEAD6"};
    }}
    .badge-medium {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: {"#3D2B05" if is_dark else "#FEF7E0"};
        color: {"#FDD663" if is_dark else "#B06000"};
        border: 1px solid {"#664908" if is_dark else "#FEEFC3"};
    }}
    .badge-low {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background-color: {"#3C1816" if is_dark else "#FCE8E6"};
        color: {"#F28B82" if is_dark else "#C5221F"};
        border: 1px solid {"#5E2421" if is_dark else "#FAD2CF"};
    }}

    /* Event Cards (Styled card for events_calendar_2026.md) */
    .event-banner-card {{
        background: var(--bg-card);
        border: 1px solid #4285F4;
        border-left: 5px solid #4285F4;
        border-radius: 12px;
        padding: 1.0rem 1.25rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 12px rgba(66, 133, 244, 0.12);
    }}
    .event-banner-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.65rem;
    }}
    .event-badge {{
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: #E8F0FE;
        color: #1967D2;
        padding: 0.15rem 0.55rem;
        border-radius: 6px;
    }}
    .event-title {{
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.4rem;
    }}
    .event-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.55rem;
        margin-top: 0.5rem;
    }}
    .event-item {{
        font-size: 0.83rem;
        line-height: 1.4;
    }}
    .event-label {{
        font-weight: 600;
        color: var(--text-secondary);
        margin-right: 0.3rem;
    }}
    .event-val {{
        font-weight: 600;
        color: var(--text-primary);
    }}

    /* Fallback Card (Amber) */
    .fallback-card {{
        background-color: {"#2A210A" if is_dark else "#FFF9E6"};
        border: 1px solid {"#6E5114" if is_dark else "#FFE082"};
        border-left: 5px solid #FBBC04;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin: 0.8rem 0;
        color: var(--text-primary);
    }}
    .fallback-title {{
        font-weight: 700;
        color: {"#FDD663" if is_dark else "#92400E"};
        font-size: 1.0rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.45rem;
    }}
    .fallback-hint {{
        font-size: 0.88rem;
        color: {"#E0D5B5" if is_dark else "#78350F"};
        line-height: 1.5;
    }}

    /* Source Cards */
    .source-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
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
        background: var(--bg-subtle);
        border-radius: 8px;
        border-left: 3px solid #4285F4;
        line-height: 1.45;
        margin-top: 0.3rem;
        color: var(--text-primary);
    }}

    /* "Did you know?" Sidebar Card */
    .did-you-know-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 4px solid #FBBC04;
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.5rem;
    }}
    .did-you-know-header {{
        font-size: 0.74rem;
        font-weight: 700;
        color: #FBBC04;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }}
    .did-you-know-body {{
        font-size: 0.82rem;
        line-height: 1.4;
        color: var(--text-primary);
    }}

    /* Clean Footer */
    .app-footer {{
        margin-top: 3.5rem;
        padding: 1.5rem 0 2rem 0;
        border-top: 1px solid var(--border-color);
        text-align: center;
    }}
    .footer-brand {{
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        margin-bottom: 0.35rem;
    }}
    .footer-note {{
        font-size: 0.78rem;
        color: var(--text-muted);
        line-height: 1.4;
    }}

    /* Mobile Responsive Tweaks */
    @media (max-width: 768px) {{
        .brand-title {{ font-size: 1.35rem; }}
        .suggestion-card-box {{ height: 135px; }}
        .source-header {{ flex-direction: column; align-items: flex-start; gap: 0.2rem; }}
        .event-grid {{ grid-template-columns: 1fr; }}
    }}
    </style>
    """
