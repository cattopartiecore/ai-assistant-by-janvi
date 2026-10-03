"""
Design System and Centralized Styles for GDG On Campus USAR Knowledge Assistant.
Production-grade dark theme (default) and clean light theme with:
- Strict design tokens (spacing, radius, typography, transitions)
- Single CSS Grid container for 100% uniform card heights (grid-auto-rows: 1fr)
- CSS-only lightweight animations with prefers-reduced-motion protection
- Pinned bottom chat input with blue focus ring
- Right-aligned user bubbles & left-aligned assistant cards (max reading width 760px)
- Responsive breakpoints for desktop (3 col), tablet (2 col), and mobile (chips)
"""

GOOGLE_BLUE = "#4285F4"
GOOGLE_RED = "#EA4335"
GOOGLE_YELLOW = "#FBBC04"
GOOGLE_GREEN = "#34A853"


def get_app_css(theme: str = "dark") -> str:
    """
    Returns the complete centralized CSS stylesheet for the application.
    Supports 'dark' (default production mode) and 'light' via CSS variables.
    """
    is_dark = theme.lower() != "light"

    # Theme-specific color values
    if is_dark:
        bg_page = "#0f1115"
        bg_surface = "#181b22"
        bg_sidebar = "#14171c"
        bg_subtle = "#1f242d"
        border_color = "#2a2f3a"
        border_focus = "#4285F4"
        text_main = "#E8EAED"
        text_muted = "#9AA0A6"
        text_subtle = "#5f6368"
        color_primary = "#4285F4"
        color_primary_hover = "#3367D6"
        user_bubble_bg = "#172554"
        user_bubble_border = "#1e3a8a"
        card_shadow = "0 1px 3px rgba(0, 0, 0, 0.4)"
        card_hover_shadow = "0 8px 24px rgba(66, 133, 244, 0.18)"
        tag_bg = "rgba(66, 133, 244, 0.12)"
        tag_border = "rgba(66, 133, 244, 0.3)"
        tag_text = "#8ab4f8"
    else:
        bg_page = "#F8F9FA"
        bg_surface = "#FFFFFF"
        bg_sidebar = "#FFFFFF"
        bg_subtle = "#F1F3F4"
        border_color = "#DADCE0"
        border_focus = "#1A73E8"
        text_main = "#202124"
        text_muted = "#5F6368"
        text_subtle = "#80868B"
        color_primary = "#1A73E8"
        color_primary_hover = "#1557B0"
        user_bubble_bg = "#E8F0FE"
        user_bubble_border = "#D2E3FC"
        card_shadow = "0 1px 3px rgba(0, 0, 0, 0.05)"
        card_hover_shadow = "0 6px 18px rgba(26, 115, 232, 0.12)"
        tag_bg = "#E8F0FE"
        tag_border = "#D2E3FC"
        tag_text = "#1967D2"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        /* Design Tokens: Spacing */
        --space-1: 4px;
        --space-2: 8px;
        --space-3: 12px;
        --space-4: 16px;
        --space-6: 24px;
        --space-8: 32px;

        /* Design Tokens: Radii */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-full: 9999px;

        /* Design Tokens: Fonts & Motion */
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        --transition: 150ms cubic-bezier(0.16, 1, 0.3, 1);

        /* Theme Color Tokens */
        --bg-page: {bg_page};
        --bg-surface: {bg_surface};
        --bg-sidebar: {bg_sidebar};
        --bg-subtle: {bg_subtle};
        --border-color: {border_color};
        --border-focus: {border_focus};
        --text-main: {text_main};
        --text-muted: {text_muted};
        --text-subtle: {text_subtle};
        --color-primary: {color_primary};
        --color-primary-hover: {color_primary_hover};
        --user-bubble-bg: {user_bubble_bg};
        --user-bubble-border: {user_bubble_border};
        --card-shadow: {card_shadow};
        --card-hover-shadow: {card_hover_shadow};
        --tag-bg: {tag_bg};
        --tag-border: {tag_border};
        --tag-text: {tag_text};

        /* Google Brand Accents */
        --google-blue: #4285F4;
        --google-red: #EA4335;
        --google-yellow: #FBBC04;
        --google-green: #34A853;
    }}

    /* Global Typography & Base Styles */
    html, body, [class*="css"] {{
        font-family: var(--font-family) !important;
        font-size: 15px;
        line-height: 1.6;
        color: var(--text-main);
    }}

    /* Page Canvas */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-page) !important;
        color: var(--text-main) !important;
    }}
    .main .block-container {{
        padding-top: var(--space-4) !important;
        padding-bottom: 140px !important; /* Prevents sticky chat input from obscuring bottom row */
        max-width: 1080px !important;
    }}
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* Header Accent Line (slides in once from left) */
    .gdg-accent-bar {{
        height: 3px;
        width: 100%;
        background: linear-gradient(90deg, #4285F4 0%, #EA4335 33%, #FBBC04 66%, #34A853 100%);
        border-radius: 2px;
        margin-bottom: var(--space-3);
        transform-origin: left center;
    }}

    /* Header Component */
    .main-header {{
        padding: var(--space-1) 0;
        margin-bottom: var(--space-3);
    }}
    .header-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-2);
        margin-bottom: var(--space-1);
    }}
    .page-title {{
        font-size: 28px !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: var(--text-main) !important;
        line-height: 1.3 !important;
        margin: 0 !important;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .brand-g {{ color: var(--google-blue); font-weight: 700; }}
    .brand-d {{ color: var(--google-red); font-weight: 700; }}
    .brand-g2 {{ color: var(--google-yellow); font-weight: 700; }}
    .brand-campus {{ color: var(--text-main); font-weight: 600; margin-left: 4px; }}
    
    .status-chip {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: var(--radius-full);
        background: rgba(52, 168, 83, 0.12);
        border: 1px solid rgba(52, 168, 83, 0.3);
        color: #81c995;
    }}
    .status-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--google-green);
        display: inline-block;
    }}

    .page-subtitle {{
        font-size: 14.5px !important;
        color: var(--text-muted) !important;
        line-height: 1.5 !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
    }}
    .header-divider {{
        height: 1px;
        background-color: var(--border-color);
        margin-top: var(--space-3);
        margin-bottom: var(--space-4);
    }}

    /* First-Load Greeting & Tip Chips */
    .greeting-banner {{
        margin-bottom: var(--space-4);
    }}
    .greeting-title {{
        font-size: 16px;
        font-weight: 600;
        color: var(--text-main);
        margin-bottom: 4px;
    }}
    .greeting-desc {{
        font-size: 13.5px;
        color: var(--text-muted);
        margin-bottom: var(--space-3);
    }}
    .tip-chips-row {{
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
        margin-bottom: var(--space-4);
    }}
    .tip-chip {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
        font-weight: 500;
        color: var(--text-muted);
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        padding: 4px 10px;
        border-radius: var(--radius-full);
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color) !important;
        padding-top: var(--space-3) !important;
    }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    .sidebar-heading {{
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--text-muted) !important;
        margin-top: var(--space-3) !important;
        margin-bottom: var(--space-1) !important;
        padding-bottom: 2px !important;
    }}
    .sidebar-help {{
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.4;
        margin-top: -2px;
        margin-bottom: var(--space-2);
    }}
    [data-testid="stSidebar"] hr {{
        margin: var(--space-3) 0 !important;
        border: none !important;
        border-top: 1px solid var(--border-color) !important;
    }}
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] label span,
    [data-testid="stSidebar"] .stRadio label span {{
        font-size: 13.5px !important;
        font-weight: 500 !important;
        color: var(--text-main) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: var(--bg-surface) !important;
        border-color: var(--border-color) !important;
        color: var(--text-main) !important;
    }}
    [data-baseweb="popover"], [data-baseweb="menu"] {{
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-main) !important;
    }}
    [data-baseweb="menu"] * {{
        color: var(--text-main) !important;
    }}

    /* =========================================================================
       CSS GRID FOR UNIFORM CARDS (Single HTML container with grid-auto-rows: 1fr)
       ========================================================================= */
    .card-grid {{
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        grid-auto-rows: 1fr !important;
        gap: 16px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin-bottom: var(--space-4) !important;
    }}

    @media (min-width: 641px) and (max-width: 1024px) {{
        .card-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
        }}
    }}

    @media (max-width: 640px) {{
        .card-grid {{
            display: none !important;
        }}
        .mobile-chips-wrapper {{
            display: block !important;
            margin-bottom: var(--space-4) !important;
        }}
    }}

    @media (min-width: 641px) {{
        .mobile-chips-wrapper {{
            display: none !important;
        }}
    }}

    /* Individual Suggestion Card (Flex Column with 100% Height) */
    .suggestion-card {{
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px !important;
        box-sizing: border-box !important;
        text-decoration: none !important;
        color: var(--text-main) !important;
        cursor: pointer !important;
        transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease !important;
    }}

    .suggestion-card:hover {{
        transform: translateY(-2px) !important;
        border-color: var(--color-primary) !important;
        box-shadow: var(--card-hover-shadow) !important;
        text-decoration: none !important;
        color: var(--text-main) !important;
    }}

    .suggestion-card:active {{
        transform: translateY(0) !important;
    }}

    .suggestion-card:focus-visible {{
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.45) !important;
    }}

    /* Top Content Area of Card */
    .card-top-content {{
        display: flex !important;
        flex-direction: column !important;
        flex-grow: 1 !important;
    }}

    .card-question-text {{
        font-size: 16px !important;
        font-weight: 500 !important;
        color: var(--text-main) !important;
        line-height: 1.45 !important;
        margin-top: 8px !important;
        margin-bottom: 6px !important;
        word-wrap: break-word !important;
        white-space: normal !important;
    }}

    .card-desc-text {{
        font-size: 13.5px !important;
        color: var(--text-muted) !important;
        line-height: 1.5 !important;
        margin-bottom: 16px !important;
        word-wrap: break-word !important;
        white-space: normal !important;
    }}

    /* Card Action Button (Docked at card bottom with margin-top: auto) */
    .card-btn {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 44px !important;
        min-height: 44px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin-top: auto !important;
        background-color: var(--color-primary) !important;
        color: #FFFFFF !important;
        border-radius: var(--radius-sm) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        text-decoration: none !important;
        transition: background-color 150ms ease, transform 150ms ease, box-shadow 150ms ease !important;
    }}

    .suggestion-card:hover .card-btn {{
        background-color: var(--color-primary-hover) !important;
        box-shadow: 0 4px 12px rgba(66, 133, 244, 0.35) !important;
    }}

    .suggestion-card:active .card-btn {{
        transform: scale(0.98) !important;
    }}

    /* Category Badges: Single-Line, Uniform 24px Height */
    .category-badge {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 5px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        height: 24px !important;
        padding: 0 8px !important;
        border-radius: var(--radius-full) !important;
        margin-bottom: 4px !important;
        width: fit-content !important;
        white-space: nowrap !important;
    }}
    .badge-blue {{
        background-color: rgba(66, 133, 244, 0.15) !important;
        color: #8ab4f8 !important;
        border: 1px solid rgba(66, 133, 244, 0.3) !important;
    }}
    .badge-green {{
        background-color: rgba(52, 168, 83, 0.15) !important;
        color: #81c995 !important;
        border: 1px solid rgba(52, 168, 83, 0.3) !important;
    }}
    .badge-amber {{
        background-color: rgba(251, 188, 4, 0.15) !important;
        color: #fdd663 !important;
        border: 1px solid rgba(251, 188, 4, 0.3) !important;
    }}
    .badge-purple {{
        background-color: rgba(168, 85, 247, 0.15) !important;
        color: #c084fc !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
    }}
    .badge-teal {{
        background-color: rgba(20, 184, 166, 0.15) !important;
        color: #5eead4 !important;
        border: 1px solid rgba(20, 184, 166, 0.3) !important;
    }}
    .badge-grey {{
        background-color: rgba(154, 160, 166, 0.15) !important;
        color: #bdc1c6 !important;
        border: 1px solid rgba(154, 160, 166, 0.3) !important;
    }}

    /* Compact / Mobile Scrollable Chips */
    .chips-scroll-wrapper {{
        display: flex !important;
        overflow-x: auto !important;
        gap: 10px !important;
        padding: 6px 2px 14px 2px !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: thin !important;
    }}
    .starter-chip {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 8px 14px !important;
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-full) !important;
        text-decoration: none !important;
        color: var(--text-main) !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        cursor: pointer !important;
        transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease !important;
    }}
    .starter-chip:hover {{
        border-color: var(--color-primary) !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--card-hover-shadow) !important;
        text-decoration: none !important;
        color: var(--text-main) !important;
    }}
    .starter-chip:active {{
        transform: scale(0.98) !important;
    }}
    .starter-chip .category-badge {{
        margin-bottom: 0 !important;
    }}
    .starter-chip-text {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--text-main) !important;
    }}

    /* General Streamlit Buttons */
    .stButton > button {{
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        min-height: 40px !important;
        border: 1px solid var(--border-color) !important;
        background-color: var(--bg-surface) !important;
        color: var(--text-main) !important;
        transition: all 150ms ease !important;
    }}
    .stButton > button:hover {{
        border-color: var(--border-focus) !important;
        color: var(--border-focus) !important;
    }}
    .stButton > button:active {{
        transform: scale(0.98) !important;
    }}
    .stButton > button:focus-visible {{
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.35) !important;
    }}

    /* Sticky Chat Input Bar */
    [data-testid="stChatInput"] {{
        background-color: transparent !important;
        padding-bottom: var(--space-4) !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 24px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        transition: border-color 150ms ease, box-shadow 150ms ease !important;
    }}
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.35) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background-color: transparent !important;
        color: var(--text-main) !important;
        border: none !important;
        font-size: 14.5px !important;
        line-height: 1.5 !important;
        padding: 10px 16px !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: var(--text-muted) !important;
    }}
    [data-testid="stChatInput"] button {{
        background-color: var(--color-primary) !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
        border: none !important;
        width: 34px !important;
        height: 34px !important;
        transition: background-color 150ms ease !important;
    }}
    [data-testid="stChatInput"] button:hover {{
        background-color: var(--color-primary-hover) !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: #FFFFFF !important;
    }}
    [data-testid="stBottom"] > div {{
        background-color: var(--bg-page) !important;
    }}

    /* Chat Messages Layout & Max Reading Width (760px) */
    [data-testid="stChatMessage"] {{
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        padding: var(--space-4) !important;
        margin-bottom: var(--space-3) !important;
        box-shadow: var(--card-shadow) !important;
        max-width: 760px !important;
        transition: all 150ms ease !important;
    }}
    
    /* User Message Bubble - Right-Aligned Blue-Tinted */
    .user-bubble-wrapper {{
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-bottom: var(--space-3);
    }}
    .user-msg-bubble {{
        background-color: var(--user-bubble-bg);
        border: 1px solid var(--user-bubble-border);
        color: var(--text-main);
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 760px;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: var(--card-shadow);
        word-wrap: break-word;
    }}

    /* Stable Loading State with Bouncing Dots */
    .thinking-container {{
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--color-primary);
        border-radius: var(--radius-md);
        padding: var(--space-4);
        margin-bottom: var(--space-3);
        max-width: 760px;
        min-height: 104px;
        box-sizing: border-box;
    }}
    .thinking-title {{
        font-size: 14px;
        font-weight: 600;
        color: var(--color-primary);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .bouncing-dots {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-left: 2px;
    }}
    .bouncing-dots .dot {{
        width: 4px;
        height: 4px;
        background-color: var(--color-primary);
        border-radius: 50%;
        display: inline-block;
    }}
    .bouncing-dots .dot:nth-child(1) {{ animation-delay: 0s; }}
    .bouncing-dots .dot:nth-child(2) {{ animation-delay: 0.18s; }}
    .bouncing-dots .dot:nth-child(3) {{ animation-delay: 0.36s; }}

    .skeleton-shimmer {{
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .skeleton-line {{
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(90deg, var(--bg-subtle) 25%, rgba(66, 133, 244, 0.12) 50%, var(--bg-subtle) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite ease-in-out;
    }}
    .skeleton-line.full {{ width: 100%; }}
    .skeleton-line.long {{ width: 85%; }}
    .skeleton-line.medium {{ width: 55%; }}

    /* Confidence Indicators (High/Medium/Low) */
    .confidence-badge {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: var(--radius-full);
        font-size: 11.5px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    .conf-high {{
        background-color: rgba(52, 168, 83, 0.15);
        color: #81c995;
        border: 1px solid rgba(52, 168, 83, 0.3);
    }}
    .conf-medium {{
        background-color: rgba(251, 188, 4, 0.15);
        color: #fdd663;
        border: 1px solid rgba(251, 188, 4, 0.3);
    }}
    .conf-low {{
        background-color: rgba(154, 160, 166, 0.15);
        color: #bdc1c6;
        border: 1px solid rgba(154, 160, 166, 0.3);
    }}

    /* Calm Unanswerable / Fallback Card (No harsh error look) */
    .unanswerable-card {{
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--text-muted);
        border-radius: var(--radius-md);
        padding: var(--space-4);
        margin: var(--space-3) 0;
        color: var(--text-main);
    }}
    .unanswerable-header {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
        font-size: 14.5px;
        color: var(--text-main);
        margin-bottom: 6px;
    }}
    .unanswerable-message {{
        font-size: 14px;
        color: var(--text-muted);
        line-height: 1.5;
    }}

    /* Expandable Sources & Citations */
    .source-card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
        padding: 12px 14px;
        margin-bottom: var(--space-2);
        transition: border-color 150ms ease;
    }}
    .source-card:hover {{
        border-color: var(--border-focus);
    }}
    .source-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        font-size: 13px;
        flex-wrap: wrap;
        gap: 4px;
    }}
    .source-tag {{
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11.5px;
        font-weight: 600;
        background: var(--tag-bg);
        border: 1px solid var(--tag-border);
        color: var(--tag-text);
        margin-right: 6px;
    }}
    .source-score-badge {{
        font-size: 11px;
        font-weight: 500;
        color: var(--text-muted);
        background: var(--bg-subtle);
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid var(--border-color);
    }}
    .source-snippet {{
        font-size: 13px;
        font-style: italic;
        padding: 8px 12px;
        background: var(--bg-subtle);
        border-radius: 6px;
        border-left: 2px solid var(--color-primary);
        line-height: 1.45;
        margin-top: 4px;
        color: var(--text-main);
    }}

    /* Event Card (events_calendar_2026.md match) */
    .event-banner-card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--color-primary);
        border-radius: var(--radius-md);
        padding: var(--space-4);
        margin-bottom: var(--space-3);
    }}
    .event-badge {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: var(--tag-bg);
        color: var(--tag-text);
        border: 1px solid var(--tag-border);
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .event-title {{
        font-size: 16px;
        font-weight: 700;
        color: var(--text-main);
        margin-top: 6px;
        margin-bottom: 6px;
    }}
    .event-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
        margin-top: 8px;
    }}
    .event-item {{ font-size: 13px; line-height: 1.4; }}
    .event-label {{ font-weight: 600; color: var(--text-muted); margin-right: 4px; }}
    .event-val {{ font-weight: 500; color: var(--text-main); }}

    /* Quick Fact Sidebar Card */
    .did-you-know-card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--google-yellow);
        border-radius: var(--radius-sm);
        padding: 10px 12px;
        margin-bottom: 8px;
    }}
    .did-you-know-header {{
        font-size: 11px;
        font-weight: 700;
        color: var(--google-yellow);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }}
    .did-you-know-body {{
        font-size: 12.5px;
        line-height: 1.4;
        color: var(--text-main);
    }}

    /* Footer */
    .app-footer {{
        margin-top: var(--space-8);
        padding: var(--space-4) 0 var(--space-2) 0;
        border-top: 1px solid var(--border-color);
        text-align: center;
    }}
    .footer-brand {{
        font-size: 13.5px;
        font-weight: 600;
        color: var(--text-main);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-bottom: 4px;
    }}
    .footer-note {{
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.4;
    }}

    /* =========================================================================
       ANIMATIONS (Only transform and opacity, with prefers-reduced-motion check)
       ========================================================================= */
    @keyframes cardEntrance {{
        0% {{
            opacity: 0;
            transform: translateY(12px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes accentSlideIn {{
        0% {{
            transform: scaleX(0);
            opacity: 0;
        }}
        100% {{
            transform: scaleX(1);
            opacity: 1;
        }}
    }}

    @keyframes messageFadeIn {{
        0% {{
            opacity: 0;
            transform: translateY(6px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes softBounce {{
        0%, 80%, 100% {{
            transform: scale(0.6);
            opacity: 0.35;
        }}
        40% {{
            transform: scale(1.15);
            opacity: 1;
        }}
    }}

    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    /* Active Animation Classes */
    @media (prefers-reduced-motion: no-preference) {{
        .animate-entrance {{
            opacity: 0;
            animation: cardEntrance 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        .animate-slide-in {{
            animation: accentSlideIn 600ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        .new-message-anim {{
            animation: messageFadeIn 250ms ease-out forwards;
        }}
        .bouncing-dots .dot {{
            animation: softBounce 1.2s infinite ease-in-out both;
        }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, ::before, ::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
        .animate-entrance,
        .animate-slide-in,
        .new-message-anim,
        .bouncing-dots .dot,
        .skeleton-line {{
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
        }}
    }}

    /* Responsive Breakpoints */
    @media (max-width: 640px) {{
        .page-title {{ font-size: 22px !important; }}
        .page-subtitle {{ font-size: 13.5px !important; }}
        [data-testid="stChatMessage"] {{ max-width: 92% !important; }}
        .user-msg-bubble {{ max-width: 92% !important; }}
        .event-grid {{ grid-template-columns: 1fr !important; }}
        .main .block-container {{
            padding-bottom: 120px !important;
        }}
    }}
    @media (min-width: 641px) and (max-width: 1024px) {{
        .page-title {{ font-size: 25px !important; }}
    }}
    </style>
    """
