import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.config import SUBJECT_BANK, BANK_TYPE, BANK_TYPE_LABEL
from utils.data_loader import load_features
from utils.style import inject_css, section

st.set_page_config(page_title="Scope & Methodology", page_icon="🧡", layout="wide")
inject_css()

# ---- Easy settings ----------------------------------------------------------
# Extra columns to show next to each URL in the bank page list.
# Add real column names from your data (names missing from the data are skipped).
EXTRA_URL_COLUMNS = ["language", "eligibility_stated"]
# Set to True once to list all column names of your dataset at the bottom of the page.
SHOW_COLUMN_DEBUG = False
# -----------------------------------------------------------------------------

ING_COLOR = "#FF6200"
LANG_LABEL = {"fr": "FR", "nl": "NL", "en": "EN", "de": "DE"}
# LLM-judged fields the analysis pages rely on: a page is "fully analysed" when all are filled.
LLM_CORE_FIELDS = [
    "tone", "value_proposition_clarity", "cta_clarity", "audience_explicit",
    "primary_cta_visibility", "price_in_initial_viewport", "eligibility_stated",
]

# Make tertiary buttons look like orange links (used for bank names in Coverage)
st.markdown(
    """
<style>
button[kind="tertiary"] { padding: 0; min-height: 0; }
button[kind="tertiary"] p { color: #C94A00 !important; font-weight: 600;
                            text-decoration: underline; }
button[kind="tertiary"]:hover p { color: #FF6200 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Hero ----------------
st.markdown(
    """
<div class="hero">
  <div class="eyebrow">ING Belgium · Youth Acquisition</div>
  <h1>Communication Comparator</h1>
  <p>How does ING speak to young people compared with other banks in Belgium?
  A cross-bank comparison of youth-oriented marketing communication.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Data ----------------
df_all, is_demo = load_features()
if is_demo:
    st.warning(
        "Showing **demo data** — the real pipeline output wasn't found yet. "
        "Every page works the same way once real data is loaded.",
        icon="⚠️",
    )

# The whole web app uses every scraped page that survived cleaning (404 /
# mismatched pages are removed by the loader). Pages scraped as adult
# comparators are left out: the study is about youth communication.
if "audience_label" in df_all.columns:
    is_adult = df_all["audience_label"].eq("general_adult")
else:
    is_adult = pd.Series(False, index=df_all.index)
df = df_all[~is_adult].copy()
n_adult_excluded = int(is_adult.sum())

config_type = df["bank"].map(BANK_TYPE)
bank_type = df["bank_type"].fillna(config_type) if "bank_type" in df.columns else config_type
df["Bank type"] = bank_type.map(BANK_TYPE_LABEL).fillna(bank_type).fillna("Unknown")

# ---------------- KPIs ----------------
n_banks = df["bank"].nunique()
n_ing = int((df["bank"] == SUBJECT_BANK).sum())
n_langs = df["language"].dropna().nunique() if "language" in df.columns else None

k1, k2, k3, k4 = st.columns(4)
for col, value, label in [
    (k1, len(df), "Pages analysed"),
    (k2, n_banks, "Banks compared"),
    (k3, n_ing, f"{SUBJECT_BANK} pages"),
    (k4, n_langs if n_langs is not None else "—", "Languages"),
]:
    col.markdown(
        f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# ---------------- Coverage ----------------
section("Coverage", "All pages kept after cleaning. Click a bank to see its URLs.")

llm_fields = [c for c in LLM_CORE_FIELDS if c in df.columns]
SHORT_TYPE = {"Traditional bank": "Traditional", "Digital challenger": "Challenger"}

bank_order = [SUBJECT_BANK] + sorted(b for b in df["bank"].unique() if b != SUBJECT_BANK)
rows = []
for bank in bank_order:
    g = df[df["bank"] == bank]
    if g.empty:
        continue
    row = {"Bank": bank, "Type": SHORT_TYPE.get(g["Bank type"].iloc[0], g["Bank type"].iloc[0]),
           "Pages": len(g)}
    if "language" in g.columns:
        lang = g["language"].astype(str).str.lower()
        for code in ["fr", "nl", "en"]:
            row[LANG_LABEL[code]] = int(lang.eq(code).sum())
    if llm_fields:
        row["Analysed"] = f"{g[llm_fields].notna().all(axis=1).mean() * 100:.0f}%"
    rows.append(row)
coverage_df = pd.DataFrame(rows)

# Chart: one bar per bank, ING highlighted, nothing else on it.
chart = coverage_df.sort_values("Pages", ascending=False)
fig = px.bar(chart, x="Pages", y="Bank", orientation="h", text="Pages")
fig.update_traces(
    marker_color=[ING_COLOR if b == SUBJECT_BANK else "#B8BDC7" for b in chart["Bank"]],
    marker_cornerradius=4, textposition="outside", cliponaxis=False,
    textfont=dict(color="#5B5F68", size=13),
    hovertemplate="%{y}: %{x} pages<extra></extra>",
)
fig.update_xaxes(visible=False)
fig.update_yaxes(title=None, autorange="reversed", showgrid=False, ticks="",
                 tickfont=dict(size=14, color="#2B2D33"))
fig.update_layout(height=28 + 34 * len(chart), bargap=0.35, showlegend=False,
                  margin=dict(l=0, r=40, t=0, b=0),
                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Table: bank names are clickable and open the list of URLs below.
if "coverage_bank" not in st.session_state:
    st.session_state["coverage_bank"] = None

columns = list(coverage_df.columns)
widths = [2, 1.6] + [1] * (len(columns) - 2)
header = st.columns(widths)
for h, name in zip(header, columns):
    h.markdown(f"**{name}**")
st.markdown('<hr style="margin:.2rem 0 .4rem 0">', unsafe_allow_html=True)

for _, row in coverage_df.iterrows():
    bank = row["Bank"]
    cells = st.columns(widths)
    try:
        clicked = cells[0].button(str(bank), key=f"cov_{bank}", type="tertiary")
    except TypeError:  # older Streamlit without "tertiary"
        clicked = cells[0].button(str(bank), key=f"cov_{bank}")
    if clicked:
        # clicking the same bank again closes the list
        st.session_state["coverage_bank"] = (
            None if st.session_state["coverage_bank"] == bank else bank
        )
    for cell, name in zip(cells[1:], columns[1:]):
        cell.markdown(str(row[name]))  # plain text: st.write renders numpy ints as code chips

note = "Analysed = share of pages with every LLM feature filled. 404 and mismatched pages removed"
if n_adult_excluded:
    note += f"; {n_adult_excluded} adult-audience pages excluded"
st.caption(note + ".")

# ---------------- Selected bank: URL list ----------------
selected = st.session_state["coverage_bank"]
if selected:
    bank_pages = df[df["bank"] == selected]
    st.subheader(f"{selected} — {len(bank_pages)} pages")

    if bank_pages.empty or "url" not in bank_pages.columns:
        st.info("No page URLs available for this bank yet.")
    else:
        shown = [c for c in EXTRA_URL_COLUMNS if c in bank_pages.columns]
        table = bank_pages[["url"] + shown].reset_index(drop=True)
        table.index = table.index + 1
        st.dataframe(
            table,
            use_container_width=True,
            column_config={"url": st.column_config.LinkColumn("URL")},
        )
    if st.button("Close list"):
        st.session_state["coverage_bank"] = None
        st.rerun()

# ---------------- Explore the analysis (auto-discovers your pages) ----------------
PAGE_BLURBS = {
    "market positioning": "Where ING stands against the market, and how traditional banks differ from digital challengers.",
    "ing positioning": "Where ING stands against every other bank, trait by trait.",
    "visual comparator": "Put 2 to 3 banks side by side and compare their actual pages.",
    "traditional vs digital challenger": "How traditional banks and digital challengers speak to young people.",
    "why it matters": "What these differences mean for youth acquisition.",
    "recommendations": "Concrete next steps for ING's youth communication.",
}
pages = sorted((Path(__file__).parent / "pages").glob("*.py"))
section("Explore the analysis", f"{len(pages)} views, from the big picture to concrete actions.")
for row_start in range(0, len(pages), 3):
    for col, page in zip(st.columns(3), pages[row_start:row_start + 3]):
        idx = pages.index(page) + 1
        title = re.sub(r"^\d+[_\- ]*", "", page.stem).replace("_", " ")
        blurb = PAGE_BLURBS.get(title.lower(), "")
        with col:
            st.markdown(
                f'<div class="step"><div class="num">{idx}</div><h4>{title}</h4><p>{blurb}</p></div>',
                unsafe_allow_html=True,
            )
            try:
                st.page_link(f"pages/{page.name}", label="Open", icon="➡️")
            except Exception:
                pass
    st.write("")

with st.expander("How this was built"):
    st.markdown(
        "Public youth-oriented pages of each bank are scraped (robots.txt respected), cleaned "
        "(404 / error pages and content mismatches removed), then described with LLM-judged "
        "features (tone, clarity, CTA, trust signals…) and Python-computed features (word count, "
        "jargon density, sentence length). Every page that survives cleaning is used across the "
        "whole web app. When a bank is compared with its peers, banks with very few pages are "
        "still shown but kept out of the peer average, because their rates are too unstable."
    )

st.divider()

if SHOW_COLUMN_DEBUG:
    with st.expander("Debug: dataset columns"):
        st.write(list(df.columns))
        st.dataframe(df.head(3), use_container_width=True)