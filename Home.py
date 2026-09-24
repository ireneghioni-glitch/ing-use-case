import streamlit as st

from utils.config import (
    MVP_BANKS, SUBJECT_BANK, TARGET_RECORDS_PER_BANK, MIN_VIABLE_RECORDS_PER_BANK,
)
from utils.data_loader import (
    load_features, compute_coverage, scope_breakdown, deterministic_review_summary,
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

review = deterministic_review_summary()
if review and review["reviewed_share_pct"] < 100:
    st.info(
        f"**Data quality note:** the Python-computed features (word count, "
        f"jargon density, sentence length) are still **pending team review** "
        f"({review['reviewed_share_pct']:.0f}% reviewed so far, "
        f"{review['total_values']} values total). Treat related figures as provisional.",
        icon="🔍",
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

# ---------------- Methodology ----------------
section("Methodology", "How the numbers on the following pages are produced.")
steps = [
    ("Collect", "Public web pages of each MVP bank are scraped into a single corpus."),
    ("Select", f"Only youth-oriented pages are kept, aiming for {TARGET_RECORDS_PER_BANK} per bank."),
    ("Measure", "Python computes objective features: word count, jargon density, sentence length."),
    ("Review", "The team reviews computed values; figures stay provisional until fully reviewed."),
    ("Compare", f"ING is benchmarked against peers. Banks under {MIN_VIABLE_RECORDS_PER_BANK} pages are replaced by a backup bank."),
]
for col, (i, (title, text)) in zip(st.columns(len(steps)), enumerate(steps, 1)):
    col.markdown(
        f'<div class="step"><div class="num">{i}</div><h4>{title}</h4><p>{text}</p></div>',
        unsafe_allow_html=True,
    )

st.divider()

if SHOW_COLUMN_DEBUG:
    with st.expander("Debug: dataset columns"):
        st.write(list(df.columns))
        st.dataframe(df.head(3), use_container_width=True)
