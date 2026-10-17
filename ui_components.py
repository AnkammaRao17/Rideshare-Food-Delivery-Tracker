"""
Reusable UI helper components and modern light-theme styling for Streamlit.
Theme Architecture:
- Main background: #F4F7FB
- Sidebar background: #FFFFFF
- Primary teal: #0D9488
- Secondary blue: #3B82F6
- Main text: #1F2937
- Secondary text: #64748B
- Cards: #FFFFFF
- Borders: #E2E8F0
- Success: #16A34A
- Warning: #F59E0B
- Error: #DC2626
"""

import streamlit as st
import pandas as pd
from typing import Any, Optional


def format_inr(amount: Any) -> str:
    """
    Format a number in Indian Rupees (INR) with standard Indian lakh/crore
    grouping and two decimal places.
    Examples:
        500 -> ₹500.00
        1000 -> ₹1,000.00
        10000 -> ₹10,000.00
        55064.94 -> ₹55,064.94
        152320.00 -> ₹1,52,320.00
        1000000 -> ₹10,00,000.00
    """
    if amount is None:
        return "₹0.00"
    try:
        num = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    sign = "-" if num < 0 else ""
    num = abs(num)
    parts = f"{num:.2f}".split(".")
    int_part, dec_part = parts[0], parts[1]

    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        grouped = []
        while len(remaining) > 2:
            grouped.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            grouped.insert(0, remaining)
        formatted_int = ",".join(grouped) + "," + last_three

    return f"{sign}₹{formatted_int}.{dec_part}"


def inject_custom_css():
    """Inject cohesive modern Indian mobility and food delivery theme CSS with floating gradient orbs and animations."""
    st.markdown("""
    <!-- Ambient Floating Gradient Orbs Background -->
    <div class="ambient-orbs-container" aria-hidden="true">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
        <div class="ambient-orb orb-3"></div>
        <div class="ambient-orb orb-4"></div>
    </div>

    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Main Application Canvas with Subtle Multi-Gradient */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 50%, #EAF2FF 100%);
        color: #1F2937;
        min-height: 100vh;
    }

    /* Ambient Floating Gradient Orbs */
    .ambient-orbs-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        pointer-events: none !important;
        z-index: 0 !important;
    }

    .ambient-orb {
        position: absolute;
        border-radius: 50%;
        pointer-events: none !important;
        filter: blur(85px);
        opacity: 0.22;
        will-change: transform;
    }

    .orb-1 {
        width: 440px;
        height: 440px;
        background: radial-gradient(circle, #0F9D8A 0%, rgba(15, 157, 138, 0) 70%);
        top: -80px;
        left: 18%;
        animation: orbFloat1 22s ease-in-out infinite alternate;
    }

    .orb-2 {
        width: 460px;
        height: 460px;
        background: radial-gradient(circle, #3B82F6 0%, rgba(59, 130, 246, 0) 70%);
        top: 25%;
        right: -80px;
        animation: orbFloat2 26s ease-in-out infinite alternate;
    }

    .orb-3 {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #8B5CF6 0%, rgba(139, 92, 246, 0) 70%);
        bottom: 8%;
        left: 8%;
        animation: orbFloat3 24s ease-in-out infinite alternate;
    }

    .orb-4 {
        width: 380px;
        height: 380px;
        background: radial-gradient(circle, #EC4899 0%, rgba(236, 72, 153, 0) 70%);
        bottom: -60px;
        right: 22%;
        animation: orbFloat1 28s ease-in-out infinite alternate-reverse;
    }

    @keyframes orbFloat1 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(35px, -30px) scale(1.06); }
        100% { transform: translate(-25px, 20px) scale(0.96); }
    }

    @keyframes orbFloat2 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-30px, 35px) scale(1.05); }
        100% { transform: translate(25px, -20px) scale(0.97); }
    }

    @keyframes orbFloat3 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(28px, 28px) scale(1.04); }
        100% { transform: translate(-22px, -30px) scale(0.95); }
    }

    /* Page Entrance Animation */
    @keyframes pageSlideUp {
        0% {
            opacity: 0;
            transform: translateY(8px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .stApp [data-testid="stMainBlockContainer"] {
        animation: pageSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        position: relative;
        z-index: 1;
    }

    /* ========================================================
       SIDEBAR STYLING (#FFFFFF with Glass & Gradient Accents)
       ======================================================== */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.96) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.85) !important;
        box-shadow: 2px 0 16px rgba(15, 23, 42, 0.03) !important;
        position: relative;
        z-index: 2;
    }

    [data-testid="stSidebar"] * {
        color: #1F2937 !important;
    }

    /* Sidebar Headings & Titles */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #172554 !important;
        font-weight: 700;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #374151 !important;
    }

    /* Native st.navigation Sidebar Links */
    [data-testid="stSidebarNav"] {
        padding-top: 0.25rem;
    }

    [data-testid="stSidebarNavSeparator"] {
        border-top: 1px solid rgba(226, 232, 240, 0.8) !important;
        margin: 0.5rem 0 !important;
    }

    /* Section Headers in Sidebar Navigation */
    [data-testid="stSidebarNavItems"] > div > span,
    [data-testid="stSidebarNav"] [data-testid="stMarkdownContainer"] p strong,
    [data-testid="stSidebarNav"] header {
        color: #64748B !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-weight: 700 !important;
        margin-top: 0.85rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* Individual Nav Links with Smooth Hover & Active States */
    [data-testid="stSidebarNavLink"] {
        border-radius: 8px !important;
        padding: 0.45rem 0.75rem !important;
        margin-bottom: 0.2rem !important;
        border: 1px solid transparent !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    [data-testid="stSidebarNavLink"] span {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
    }

    /* Hover State */
    [data-testid="stSidebarNavLink"]:hover {
        background: linear-gradient(90deg, #F0FDFA 0%, #EFF6FF 100%) !important;
        border-color: rgba(15, 157, 138, 0.2) !important;
        transform: translateX(3px) !important;
    }

    [data-testid="stSidebarNavLink"]:hover span {
        color: #0F9D8A !important;
    }

    /* Active Nav Item - Modern Teal-to-Blue Gradient Highlight */
    [data-testid="stSidebarNavLink"][aria-current="page"],
    [data-testid="stSidebarNavLink"].active {
        background: linear-gradient(90deg, rgba(15, 157, 138, 0.16) 0%, rgba(59, 130, 246, 0.12) 100%) !important;
        border-left: 4px solid #0F9D8A !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(15, 157, 138, 0.08) !important;
    }

    [data-testid="stSidebarNavLink"][aria-current="page"] span,
    [data-testid="stSidebarNavLink"].active span {
        color: #0F766E !important;
        font-weight: 700 !important;
    }

    /* Sidebar Expander & Inputs */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: rgba(248, 250, 252, 0.9) !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }

    /* ========================================================
       PAGE HEADER WITH GLASSMORPHISM & GRADIENT ACCENTS
       ======================================================== */
    .dashboard-header {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 14px;
        padding: 1.15rem 1.45rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 20px -3px rgba(15, 23, 42, 0.05);
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.25s ease, border-color 0.25s ease;
    }

    .dashboard-header:hover {
        box-shadow: 0 8px 28px -4px rgba(15, 157, 138, 0.12);
        border-color: rgba(15, 157, 138, 0.3);
    }

    .header-content-wrapper {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .header-icon-box {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(15, 157, 138, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.55rem;
        border: 1px solid rgba(15, 157, 138, 0.22);
        box-shadow: 0 4px 12px rgba(15, 157, 138, 0.08);
        flex-shrink: 0;
    }

    .main-title {
        font-size: 1.68rem;
        font-weight: 800;
        color: #172554;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }

    .sub-title {
        color: #64748B;
        font-size: 0.88rem;
        margin-top: 0.25rem;
        margin-bottom: 0;
        font-weight: 450;
    }

    .header-gradient-bar {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3.5px;
        background: linear-gradient(90deg, #0F9D8A 0%, #3B82F6 33%, #8B5CF6 66%, #EC4899 100%);
    }

    /* ========================================================
       FLOATING KPI METRIC CARDS (Glassmorphism & Lift on Hover)
       ======================================================== */
    .kpi-card {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 12px;
        padding: 1.05rem 1.15rem;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.75rem;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease;
    }

    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 32px -6px rgba(15, 23, 42, 0.1), 0 0 0 1px rgba(15, 157, 138, 0.25);
    }

    .kpi-title {
        font-size: 0.73rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .kpi-value {
        font-size: clamp(1.15rem, 1.4vw, 1.48rem);
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.01em;
        line-height: 1.25;
        word-break: break-word;
        white-space: normal;
    }

    .kpi-subtext {
        font-size: 0.78rem;
        margin-top: 0.3rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    /* Glass Cards for Chart Containers & Details */
    .glass-card {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 12px;
        padding: 1.15rem 1.35rem;
        box-shadow: 0 4px 18px -2px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.85rem;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .glass-card:hover {
        box-shadow: 0 10px 28px -4px rgba(15, 23, 42, 0.08);
        border-color: rgba(15, 157, 138, 0.25);
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 0.22rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 600;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .badge-completed, .badge-delivered, .badge-active {
        background: linear-gradient(135deg, #DEF7EC 0%, #D1FAE5 100%);
        color: #03543F;
        border: 1px solid #A7F3D0;
    }

    .badge-in_progress, .badge-preparing, .badge-accepted, .badge-out_for_delivery {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
        border: 1px solid #FCD34D;
    }

    .badge-requested, .badge-placed {
        background: linear-gradient(135deg, #E0E7FF 0%, #EDE9FE 100%);
        color: #3730A3;
        border: 1px solid #C7D2FE;
    }

    .badge-cancelled, .badge-inactive {
        background: linear-gradient(135deg, #FDE8E8 0%, #FEE2E2 100%);
        color: #9B1C1C;
        border: 1px solid #FCA5A5;
    }

    /* Buttons with Modern Gradient and Dynamic Hover Lift */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #0F9D8A 0%, #2563EB 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.52rem 1.25rem !important;
        box-shadow: 0 4px 14px rgba(15, 157, 138, 0.3) !important;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0D8272 0%, #1D4ED8 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(15, 157, 138, 0.45) !important;
    }
    .stButton>button[kind="primary"]:active {
        transform: translateY(0) scale(0.98) !important;
    }

    .stButton>button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid #CBD5E1 !important;
        color: #1E293B !important;
        font-weight: 550 !important;
        border-radius: 8px !important;
        padding: 0.52rem 1.25rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton>button[kind="secondary"]:hover {
        background: #F0FDFA !important;
        border-color: #0F9D8A !important;
        color: #0F9D8A !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06) !important;
    }
    .stButton>button[kind="secondary"]:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* Form Inputs & Focus Glow */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        background-color: rgba(255, 255, 255, 0.95) !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #0F9D8A !important;
        box-shadow: 0 0 0 3px rgba(15, 157, 138, 0.2) !important;
    }

    /* Tables & Dataframes with Glass Effect */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(8px) !important;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04) !important;
    }

    /* Tab Styling with Gradient Active Underline */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid rgba(226, 232, 240, 0.8);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        color: #64748B;
        font-weight: 550;
        border-radius: 6px 6px 0 0;
        transition: color 0.18s ease, border-color 0.18s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #0F766E !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #0F9D8A !important;
    }

    /* Reduced Motion Accessibility */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
        .ambient-orb {
            animation: none !important;
            display: none !important;
        }
    }

    /* Query Code Boxes with Gradient Accent */
    .query-box {
        background-color: rgba(248, 250, 252, 0.95);
        border-left: 4px solid #0F9D8A;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.86rem;
        color: #1E293B;
        margin: 0.6rem 0;
        border: 1px solid #E2E8F0;
        border-left-width: 4px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 2.75rem 1.5rem;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        margin: 1.25rem 0;
        box-shadow: 0 4px 14px rgba(0,0,0,0.02);
    }
    .empty-state-icon {
        font-size: 2.4rem;
        color: #94A3B8;
        margin-bottom: 0.4rem;
    }
    .empty-state-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #172554;
        margin-bottom: 0.25rem;
    }
    .empty-state-desc {
        font-size: 0.88rem;
        color: #64748B;
        max-width: 480px;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str, icon: str = "🚗"):
    """Render consistent premium glassmorphism page header with gradient accents."""
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-content-wrapper">
            <div class="header-icon-box">
                <span>{icon}</span>
            </div>
            <div>
                <div class="main-title">{title}</div>
                <div class="sub-title">{subtitle}</div>
            </div>
        </div>
        <div class="header-gradient-bar"></div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi(col, title: str, value: str, subtext: str = "", color: str = "#0D9488"):
    """Render a KPI metric card with top accent bar, hover lift, and clear typography."""
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 3.5px solid {color};">
            <div>
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-subtext" style="color: {color};">
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: {color}; margin-right: 4px;"></span>
                {subtext}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_empty_state(title: str, description: str, icon: str = "📭"):
    """Render a friendly empty state message when no documents match."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def get_plotly_theme_layout():
    """Returns consistent Plotly layout matching the light palette with transparent backgrounds."""
    return dict(
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#1F2937"),
        paper_bgcolor="rgba(255, 255, 255, 0)",
        plot_bgcolor="rgba(255, 255, 255, 0)",
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B", size=11)
        ),
        yaxis=dict(
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B", size=11)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#475569", size=11)
        )
    )


def paginate_dataframe(df: pd.DataFrame, page_size: int = 10, key_prefix: str = "page"):
    """Render pagination controls and return sliced dataframe."""
    if df.empty:
        return df
        
    total_rows = len(df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        current_page = st.number_input(
            f"Page (1 of {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"{key_prefix}_num"
        )
        
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    st.caption(f"Showing records {start_idx + 1} to {end_idx} of {total_rows}")
    return df.iloc[start_idx:end_idx]
