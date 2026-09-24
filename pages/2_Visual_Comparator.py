import pandas as pd
import streamlit as st

from utils.config import MVP_BANKS, BANK_TYPE, SUBJECT_BANK
from utils.data_loader import load_features
from utils.style import inject_css 

st.set_page_config(page_title="Visual Comparator", page_icon="🖼️", layout="wide")
inject_css() 
st.title("Visual Comparator")
st.caption("Pick specific pages across banks and see exactly where they differ.")

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data** — screenshots aren't available in demo mode.", icon="⚠️")

SCOPE_BADGE = {"backup": " 🔁 backup", "out_of_scope": " ⛔ out of scope"}
has_scope_role = "scope_role" in df.columns
working_df = df

# --- Filters ---
f1, f2, f3 = st.columns([1.3, 1, 2])
def _as_list(value):
    """Parquet round-trips list columns as numpy arrays, not plain Python
    lists — isinstance(x, list) silently misses them. Normalize here."""
    if isinstance(value, (list, tuple)):
        return list(value)
    if hasattr(value, "tolist"):  # numpy array
        return value.tolist()
    return None


with f2:
    languages = sorted(df["language"].dropna().unique().tolist()) if "language" in df.columns else []
    language_filter = st.selectbox("Language", options=["All"] + languages)

if language_filter != "All":
    working_df = working_df[working_df["language"] == language_filter]

has_topics = "topics" in working_df.columns
topic_filter = "All"
with f1:
    if has_topics:
        # Only offer topics that ING shares with at least one other bank,
        # WITHIN the current language filter — a topic unique to a single
        # bank (or only shared in a different language) wouldn't give a
        # meaningful cross-bank comparison here.
        bank_topics: dict[str, set] = {}
        for _, r in working_df[["bank", "topics"]].dropna().iterrows():
            lst = _as_list(r["topics"])
            if lst:
                bank_topics.setdefault(r["bank"], set()).update(lst)

        ing_topics = bank_topics.get(SUBJECT_BANK, set())
        shared_with_ing = set()
        for bank, topics in bank_topics.items():
            if bank != SUBJECT_BANK:
                shared_with_ing.update(ing_topics & topics)

        topic_filter = st.selectbox(
            "Product / topic", options=["All"] + sorted(shared_with_ing),
            help=f"Only topics {SUBJECT_BANK} shares with at least one other bank "
                 "(within the selected language) are listed.",
        )

if topic_filter != "All":
    working_df = working_df[working_df["topics"].apply(
        lambda t: topic_filter in (_as_list(t) or [])
    )]

available_banks = sorted(working_df["bank"].unique().tolist())
if not available_banks:
    st.info("No pages match these filters.")
    st.stop()

with f3:
    # ING first, then other banks with a page matching the current filters
    # (MVP banks preferred, but not required — a backup bank sharing the
    # topic with ING should still show up).
    ordered_candidates = [SUBJECT_BANK] + MVP_BANKS + available_banks
    default_banks = [b for b in dict.fromkeys(ordered_candidates) if b in available_banks][:3]
    # Reset the widget whenever the filters change, instead of Streamlit
    # silently keeping a stale selection from before the filter changed
    # (st.multiselect only applies `default` on a widget's very first run).
    selected_banks = st.multiselect(
        "Banks to compare (up to 3)", options=available_banks, default=default_banks,
        max_selections=3, key=f"banks_{topic_filter}_{language_filter}",
    )

if not selected_banks:
    st.info("Select at least one bank above.")
    st.stop()


def page_label(row) -> str:
    title = str(row.get("title") or "").strip()
    if title and title.lower() != "nan":
        label = title if len(title) <= 60 else title[:57] + "..."
    else:
        label = str(row.get("url", "")).rstrip("/").split("/")[-1] or row["asset_id"]
    tone = row.get("tone", "")
    return f"{label} — {tone}" if tone else label


# --- Per-bank page picker + screenshots ---
selected_pages = {}  # bank -> row (pandas Series)

cols = st.columns(len(selected_banks))
for col, bank in zip(cols, selected_banks):
    with col:
        bank_pages = working_df[working_df["bank"] == bank].reset_index(drop=True)

        badge = ""
        if has_scope_role and not bank_pages.empty:
            role = bank_pages["scope_role"].iloc[0]
            badge = SCOPE_BADGE.get(role, "")
        is_subject = bank == SUBJECT_BANK

        header = f"**{bank}{badge}**" + (" 🎯" if is_subject else "")
        st.markdown(header)
        st.caption(BANK_TYPE.get(bank, "—").title())

        if bank_pages.empty:
            st.info("No pages for this bank with these filters.")
            continue

        labels = bank_pages.apply(page_label, axis=1).tolist()
        idx = st.selectbox(f"Page ({bank})", options=range(len(labels)),
                            format_func=lambda i, _labels=labels: _labels[i], key=f"page_{bank}",
                            label_visibility="collapsed")
        page = bank_pages.iloc[idx]
        selected_pages[bank] = page

        screenshot = page.get("screenshot_path")
        if screenshot and not is_demo:
            try:
                st.image(screenshot, use_container_width=True)
            except Exception:
                st.info("Screenshot not found on disk.")
        else:
            st.info("Screenshot preview unavailable in demo mode.")

        st.caption(page.get("url", "—"))

        text = page.get("text")
        if text and not is_demo:
            with st.expander("Page text excerpt"):
                st.caption(text[:400] + ("..." if len(text) > 400 else ""))

if len(selected_pages) < 2:
    st.stop()

st.divider()
st.subheader("Where they differ")

REFERENCE_BANK = SUBJECT_BANK if SUBJECT_BANK in selected_pages else next(iter(selected_pages))
st.caption(
    f"Values that differ from **{REFERENCE_BANK}** (the reference column) are highlighted."
    if REFERENCE_BANK == SUBJECT_BANK else
    f"Values that differ from **{REFERENCE_BANK}** (first selected bank) are highlighted."
)

COMPARISON_FIELDS = {
    "tone": "Tone",
    "sentiment": "Sentiment",
    "value_proposition_clarity": "Value proposition clarity",
    "cta_clarity": "CTA clarity",
    "cta_text": "CTA text",
    "verbosity": "Verbosity",
    "distinctiveness": "Distinctiveness",
    "main_benefit": "Main benefit",
    "audience_explicit": "Names audience explicitly",
    "price_in_initial_viewport": "Price visible without scrolling",
    "primary_cta_visibility": "CTA visible without scrolling",
    "visual_type": "Visual type",
    "word_count": "Word count",
    "jargon_density": "Jargon density",
    "mean_sentence_length": "Avg. sentence length",
}

banks_ordered = [REFERENCE_BANK] + [b for b in selected_pages if b != REFERENCE_BANK]
table_rows = []
for field_key, field_label in COMPARISON_FIELDS.items():
    row = {"Feature": field_label}
    has_any = False
    for bank in banks_ordered:
        value = selected_pages[bank].get(field_key)
        is_missing = value is None or (isinstance(value, float) and pd.isna(value))
        if not is_missing:
            has_any = True
            if isinstance(value, float):
                value = round(value, 2)
            value = str(value)
        else:
            value = "—"
        row[bank] = value
    if has_any:
        table_rows.append(row)

comparison_df = pd.DataFrame(table_rows).set_index("Feature")


def highlight_diff(row):
    ref = row[REFERENCE_BANK]
    return [
        "background-color: #FFE9CC" if (col != REFERENCE_BANK and v != ref) else ""
        for col, v in row.items()
    ]


styled = comparison_df.style.apply(highlight_diff, axis=1)
st.dataframe(styled, use_container_width=True)

st.caption(
    "Orange cells show where a bank's page differs from the reference. "
    "Some differences are meaningful (tone, CTA clarity); others may just reflect "
    "normal page-to-page variation within a bank — use the screenshots above to judge."
)