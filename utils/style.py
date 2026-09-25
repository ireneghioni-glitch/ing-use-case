"""Shared ING Belgium look & feel. Call inject_css() at the top of EVERY page
(Home.py AND every file in pages/), right after st.set_page_config()."""
from pathlib import Path

import streamlit as st

ING_ORANGE = "#FF6200"
ORANGE_DARK = "#C94A00"
CHARCOAL = "#2B2D33"
CHARCOAL_SOFT = "#3D4049"
CREAM = "#FFF4EC"
GREY_TEXT = "#6B6F7A"


def inject_css() -> None:
    st.markdown(
        f"""
<style>
/* ---------- Sidebar / sub menu (orange) ---------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {ING_ORANGE} 0%, {ORANGE_DARK} 100%);
}}
[data-testid="stSidebar"] *, [data-testid="stSidebarNav"] span {{ color: #FFFFFF !important; }}
[data-testid="stSidebarNav"] a {{
    border-radius: 10px; margin: 3px 8px; padding: 6px 10px;
}}
[data-testid="stSidebarNav"] a:hover {{ background: rgba(255,255,255,.18); }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,.18);
}}
/* Active item: white pill needs dark orange text on EVERY nested element
   (span, p, div, svg icon). Higher specificity than the white-text rule above. */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] *,
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] * {{
    color: {ORANGE_DARK} !important; font-weight: 700;
}}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: #FFFFFF;
}}

/* ---------- Page headings & metrics ---------- */
h1, h2, h3 {{ color: {CHARCOAL}; }}
[data-testid="stMetricValue"] {{ color: {ING_ORANGE}; font-weight: 700; }}
[data-testid="stMetric"] {{
    background: {CREAM}; border-radius: 12px; padding: .8rem 1rem;
    border-left: 4px solid {ING_ORANGE};
}}
hr {{ border-color: {ING_ORANGE}33; }}

/* ---------- Hero banner ---------- */
.hero {{
    background: linear-gradient(120deg, {CHARCOAL} 0%, {CHARCOAL_SOFT} 55%, {ING_ORANGE} 150%);
    border-radius: 16px; padding: 2.2rem 2.4rem; margin-bottom: 1.4rem;
    border-bottom: 5px solid {ING_ORANGE};
}}
.hero .eyebrow {{
    color: {ING_ORANGE}; font-weight: 700; letter-spacing: .12em;
    font-size: .8rem; text-transform: uppercase;
}}
.hero h1 {{ color: #FFFFFF; margin: .3rem 0 .4rem 0; font-size: 2.2rem; padding: 0; }}
.hero p {{ color: #E6E6EA; margin: 0; font-size: 1.05rem; max-width: 46rem; }}

/* ---------- KPI cards ---------- */
.kpi {{
    background: #FFFFFF; border: 1px solid #F0DDD0; border-top: 4px solid {ING_ORANGE};
    border-radius: 12px; padding: 1rem 1.2rem;
}}
.kpi .v {{ font-size: 1.9rem; font-weight: 700; color: {CHARCOAL}; line-height: 1.1; }}
.kpi .l {{ color: {GREY_TEXT}; font-size: .85rem; }}

/* ---------- Bank chips ---------- */
.bank {{
    display: flex; justify-content: space-between; align-items: center;
    background: #F6F6F8; border-radius: 10px; padding: .55rem .9rem; margin-bottom: .45rem;
    border-left: 4px solid {CHARCOAL_SOFT};
}}
.bank.subject {{ border-left-color: {ING_ORANGE}; background: {CREAM}; }}
.bank .n {{ font-weight: 600; color: {CHARCOAL}; }}
.bank .t {{ font-size: .8rem; color: {GREY_TEXT}; }}

/* ---------- Methodology steps ---------- */
.step {{
    background: #FFFFFF; border: 1px solid #F0DDD0; border-radius: 12px;
    padding: 1rem 1.1rem; height: 100%;
}}
.step .num {{
    display: inline-flex; width: 28px; height: 28px; border-radius: 50%;
    background: {ING_ORANGE}; color: #fff; font-weight: 700;
    align-items: center; justify-content: center; margin-bottom: .5rem;
}}
.step h4 {{ margin: 0 0 .3rem 0; color: {CHARCOAL}; font-size: 1rem; }}
.step p {{ margin: 0; color: #4A4D57; font-size: .88rem; }}
</style>
""",
        unsafe_allow_html=True,
    )
    _sidebar_image()


SIDEBAR_IMAGE = Path(__file__).resolve().parent.parent / "assets" / "sidebar.png"  # your own image (optional)

_DEFAULT_SVG = """
<svg viewBox="0 0 240 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Youth communication">
  <rect x="4" y="4" width="232" height="182" rx="18" fill="#fff" fill-opacity=".14"/>
  <rect x="24" y="26" width="120" height="44" rx="14" fill="#fff"/>
  <path d="M44 70 L38 86 L64 70 Z" fill="#fff"/>
  <rect x="38" y="40" width="72" height="7" rx="3.5" fill="#FF6200"/>
  <rect x="38" y="53" width="48" height="7" rx="3.5" fill="#FFB27A"/>
  <rect x="96" y="96" width="120" height="44" rx="14" fill="#2B2D33"/>
  <path d="M196 140 L202 156 L176 140 Z" fill="#2B2D33"/>
  <rect x="110" y="110" width="72" height="7" rx="3.5" fill="#fff"/>
  <rect x="110" y="123" width="48" height="7" rx="3.5" fill="#FFB27A"/>
  <circle cx="34" cy="150" r="6" fill="#fff"/><circle cx="54" cy="150" r="6" fill="#fff" fill-opacity=".7"/>
  <circle cx="74" cy="150" r="6" fill="#fff" fill-opacity=".4"/>
</svg>
"""


def _sidebar_image() -> None:
    """Shown in the sidebar directly below the page menu."""
    with st.sidebar:
        st.write("")
        if SIDEBAR_IMAGE.exists():
            st.image(str(SIDEBAR_IMAGE), use_container_width=True)
        else:
            st.markdown(_DEFAULT_SVG, unsafe_allow_html=True)
        st.caption("Youth communication, compared.")


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)