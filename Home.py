import streamlit as st

from utils.config import (
    MVP_BANKS, SUBJECT_BANK, TARGET_RECORDS_PER_BANK,
    MIN_VIABLE_RECORDS_PER_BANK, OUT_OF_SCOPE, BANK_TYPE_LABEL, BANK_TYPE,
)
from utils.data_loader import (
    load_features, compute_coverage, scope_breakdown, deterministic_review_summary,
)

st.set_page_config(page_title="Scope & Methodology", page_icon="📋", layout="wide")

st.title("ING Youth Acquisition — Communication Comparator")
st.caption("A cross-bank comparison of youth-oriented marketing communication.")

df, is_demo = load_features()
if is_demo:
    st.warning(
        "Showing **demo data** — the real pipeline output wasn't found yet. "
        "Every page below works the same way once real data is loaded.",
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

st.header("What this compares")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Subject bank:** {SUBJECT_BANK}")
    st.markdown("**Comparison design:** cross-bank, on youth-oriented pages only")
    st.markdown(f"**Banks in the MVP:** {len(MVP_BANKS)}")
with col2:
    for bank in MVP_BANKS:
        label = BANK_TYPE_LABEL[BANK_TYPE[bank]]
        st.markdown(f"- **{bank}** — {label}")

st.header("Coverage")
st.markdown(
    f"Target: **{TARGET_RECORDS_PER_BANK} youth-oriented pages per bank**. "
    f"Minimum viable: **{MIN_VIABLE_RECORDS_PER_BANK}** — below that, patterns are "
    "considered anecdotal and a backup bank is activated instead."
)
coverage_df = compute_coverage(df)
st.dataframe(coverage_df, use_container_width=True, hide_index=True)

at_minimum = coverage_df[coverage_df["Status"] == "⚠ at minimum, below target"]
if not at_minimum.empty:
    names = ", ".join(at_minimum["Bank"].tolist())
    st.caption(
        f"⚠ **{names}** meets the minimum-viable threshold but not the 10-page target — "
        "patterns for this bank rest on a smaller sample than the others."
    )

with st.expander("Full corpus breakdown (including backup and out-of-scope banks)"):
    st.dataframe(scope_breakdown(df), use_container_width=True, hide_index=True)
    st.caption(
        "'Backup' banks (BNP Paribas Fortis, bunq) are scraped and ready but only "
        "promoted into the comparison if an MVP bank falls short. 'Out of scope' "
        "banks (Argenta, Beobank) were collected in an earlier iteration and are "
        "excluded from this MVP entirely."
    )

st.header("Out of scope")
st.markdown("Deliberately excluded from this MVP:")
for item in OUT_OF_SCOPE:
    st.markdown(f"- {item}")

st.divider()
st.page_link("pages/1_ING_Positioning.py", label="Continue to ING's Positioning →", icon="📍")