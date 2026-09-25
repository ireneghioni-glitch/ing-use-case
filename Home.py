import re
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import (
    MVP_BANKS, SUBJECT_BANK, TARGET_RECORDS_PER_BANK, MIN_VIABLE_RECORDS_PER_BANK, BANK_TYPE,
)
from utils.data_loader import (
    load_features, filter_mvp, compute_coverage, scope_breakdown, deterministic_review_summary,
)
from utils.style import inject_css, section

st.set_page_config(page_title="Scope & Methodology", page_icon="🧡", layout="wide")
inject_css()

# ---- Easy settings ----------------------------------------------------------
# Extra columns to show next to each URL in the bank page list.
# Add real column names from your data (names missing from the data are skipped).
EXTRA_URL_COLUMNS = ["eligibility_stated"]
# Set to True once to list all column names of your dataset at the bottom of the page.
SHOW_COLUMN_DEBUG = False
# -----------------------------------------------------------------------------

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

# ---------------- Data status ----------------
df, is_demo = load_features()
if is_demo:
    st.warning(
        "Showing **demo data** — the real pipeline output wasn't found yet. "
        "Every page works the same way once real data is loaded.",
        icon="⚠️",
    )

# ---------------- KPIs ----------------
k1, k2, k3, k4 = st.columns(4)
for col, value, label in [
    (k1, SUBJECT_BANK, "Subject bank"),
    (k2, len(MVP_BANKS), "Banks in the MVP"),
    (k3, TARGET_RECORDS_PER_BANK, "Target pages per bank"),
    (k4, MIN_VIABLE_RECORDS_PER_BANK, "Minimum viable pages"),
]:
    col.markdown(
        f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# ---------------- Coverage ----------------
section(
    "Coverage",
    f"Target: {TARGET_RECORDS_PER_BANK} youth-oriented pages per bank. Minimum viable: "
    f"{MIN_VIABLE_RECORDS_PER_BANK} — below that, patterns are considered anecdotal "
    "and a backup bank is activated instead. Click a bank name to see its pages.",
)

coverage_df = compute_coverage(df)
coverage_df = coverage_df.drop(columns=[c for c in coverage_df.columns if "backup" in c.lower()])
columns = list(coverage_df.columns)
bank_col = "Bank" if "Bank" in columns else columns[0]

if "coverage_bank" not in st.session_state:
    st.session_state["coverage_bank"] = None

# Header row
widths = [2] + [1.5] * (len(columns) - 1)
header = st.columns(widths)
ordered = [bank_col] + [c for c in columns if c != bank_col]
for h, name in zip(header, ordered):
    h.markdown(f"**{name}**")
st.markdown('<hr style="margin:.2rem 0 .4rem 0">', unsafe_allow_html=True)

# Data rows — bank name is a clickable link-style button
for _, row in coverage_df.iterrows():
    bank = row[bank_col]
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
    for cell, name in zip(cells[1:], ordered[1:]):
        cell.write(row[name])

at_minimum = coverage_df[coverage_df["Status"] == "⚠ at minimum, below target"]
if not at_minimum.empty:
    names = ", ".join(at_minimum["Bank"].tolist())
    st.caption(
        f"⚠ **{names}** meets the minimum-viable threshold but not the "
        f"{TARGET_RECORDS_PER_BANK}-page target — patterns for this bank rest on a "
        "smaller sample than the others."
    )

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

with st.expander("Comprehensive corpus breakdown including pipeline and future potential banks"):
    st.dataframe(scope_breakdown(df), use_container_width=True, hide_index=True)
    st.caption(
        "'Backup' banks (BNP Paribas Fortis, bunq) are scraped and ready but only "
        "promoted into the comparison if an MVP bank falls short. 'Out of scope' "
        "banks (Argenta, Beobank) were collected in an earlier iteration and are "
        "excluded from this MVP entirely."
    )

# ---------------- Key findings (computed live from the data) ----------------
def key_findings():
    d = filter_mvp(df)
    tests = {
        "CTA visible without scrolling": lambda x: x["primary_cta_visibility"].eq("yes"),
        "Price visible without scrolling": lambda x: x["price_in_initial_viewport"].eq("yes"),
        "Clear, specific value proposition": lambda x: x["value_proposition_clarity"].eq("clear-specific"),
        "Names its youth audience": lambda x: x["audience_explicit"].eq("yes"),
        "Eligibility clearly stated": lambda x: x["eligibility_stated"].eq("yes"),
        "Gain-framed persuasion": lambda x: x["persuasive_framing"].eq("gain"),
        "Real people in imagery": lambda x: x["visual_type"].eq("real-people"),
    }
    rates = {}
    for bank, sub in d.groupby("bank"):
        rates[bank] = {}
        for k, fn in tests.items():
            try:
                rates[bank][k] = fn(sub).mean() * 100
            except KeyError:
                pass
    r = pd.DataFrame(rates).T
    gap = (r.loc[SUBJECT_BANK] - r.drop(SUBJECT_BANK).mean()).dropna().sort_values()
    cards = [
        (f"{gap.iloc[-1]:+.0f} pp", f"<b>{gap.index[-1]}</b><br>{SUBJECT_BANK}'s biggest lead over peers"),
        (f"{gap.iloc[0]:+.0f} pp", f"<b>{gap.index[0]}</b><br>{SUBJECT_BANK}'s biggest gap to peers"),
    ]
    types = d["bank"].map(BANK_TYPE)
    trad = next((t for t in types.dropna().unique() if str(t).lower().startswith("trad")), None)
    if trad is not None and types.nunique() > 1:
        tg = {}
        for k, fn in tests.items():
            try:
                m = fn(d).groupby(types).mean() * 100
                tg[k] = m.drop(trad).mean() - m[trad]
            except KeyError:
                pass
        tg = pd.Series(tg).dropna()
        k = tg.abs().idxmax()
        who = "digital challengers" if tg[k] > 0 else "traditional banks"
        cards.append((f"{abs(tg[k]):.0f} pp", f"<b>{k}</b><br>biggest gap between bank types ({who} ahead)"))
    return cards


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
        f"Public pages of each MVP bank are scraped, filtered to youth-oriented pages "
        f"(target {TARGET_RECORDS_PER_BANK} per bank, minimum {MIN_VIABLE_RECORDS_PER_BANK}), "
        "described with LLM-judged and Python-computed features, and reviewed by the team. "
        "Banks below the minimum are replaced by a backup bank."
    )

st.divider()

if SHOW_COLUMN_DEBUG:
    with st.expander("Debug: dataset columns"):
        st.write(list(df.columns))
        st.dataframe(df.head(3), use_container_width=True)
