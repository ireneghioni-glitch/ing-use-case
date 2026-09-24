import pandas as pd
import plotly.express as px
import streamlit as st

from utils.config import BANK_TYPE_LABEL
from utils.data_loader import load_features, filter_mvp, load_manual_annotations
from utils.style import inject_css
st.set_page_config(page_title="Traditional vs Digital Challenger", page_icon="📊", layout="wide")
inject_css() 
st.title("Traditional Banks vs Digital Challengers")
st.caption("Aggregate patterns across all youth-oriented pages, MVP banks only.")

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data**.", icon="⚠️")

mvp_df = filter_mvp(df).copy()
mvp_df["Bank type"] = mvp_df["bank_type"].map(BANK_TYPE_LABEL).fillna(mvp_df["bank_type"])

COLOR_MAP = {"Traditional bank": "#4472C4", "Digital challenger": "#FF6200"}

st.subheader("Interpretive features (LLM-judged)")
CATEGORICAL_FEATURES = {
    "tone": "Tone",
    "sentiment": "Sentiment",
    "value_proposition_clarity": "Value proposition clarity",
    "cta_clarity": "CTA clarity",
    "verbosity": "Verbosity",
    "distinctiveness": "Distinctiveness",
}

feature_key = st.selectbox(
    "Feature to break down",
    options=list(CATEGORICAL_FEATURES.keys()),
    format_func=lambda k: CATEGORICAL_FEATURES[k],
)

counts = mvp_df.groupby(["Bank type", feature_key]).size().reset_index(name="Pages")
totals = mvp_df.groupby("Bank type").size().to_dict()
counts["Share (%)"] = counts.apply(lambda r: r["Pages"] / totals[r["Bank type"]] * 100, axis=1)

fig = px.bar(
    counts, x="Share (%)", y=feature_key, color="Bank type", barmode="group", orientation="h",
    color_discrete_map=COLOR_MAP,
)
fig.update_layout(yaxis_title=None, legend_title=None, height=420)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Yes/no traits")
YES_NO_FEATURES = {
    "price_in_initial_viewport": "Price visible without scrolling",
    "primary_cta_visibility": "CTA visible without scrolling",
    "audience_explicit": "Names its youth audience explicitly",
    "eligibility_stated": "States eligibility requirements",
}

rows = []
for col, label in YES_NO_FEATURES.items():
    if col not in mvp_df.columns:
        continue
    for bank_type in mvp_df["Bank type"].unique():
        subset = mvp_df[mvp_df["Bank type"] == bank_type]
        rate = (subset[col] == "yes").mean() * 100
        rows.append({"Trait": label, "Bank type": bank_type, "Share (%)": rate})

if rows:
    yn_df = pd.DataFrame(rows)
    fig2 = px.bar(
        yn_df, x="Share (%)", y="Trait", color="Bank type", barmode="group", orientation="h",
        color_discrete_map=COLOR_MAP,
    )
    fig2.update_layout(yaxis_title=None, legend_title=None, height=300)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Writing style (Python-computed)")
st.caption(
    "Word count, jargon density, and average sentence length — computed "
    "deterministically, not judged by an LLM. Currently pending team review; "
    "treat as provisional."
)

NUMERIC_FEATURES = {
    "word_count": "Word count",
    "jargon_density": "Jargon density (financial terms per 100 words)",
    "mean_sentence_length": "Average sentence length (words)",
}
available_numeric = {k: v for k, v in NUMERIC_FEATURES.items() if k in mvp_df.columns}

if not available_numeric:
    st.info(
        "No deterministic writing-style features found yet — this section will "
        "populate once `data/features/deterministic.parquet` is available."
    )
else:
    numeric_key = st.selectbox(
        "Metric",
        options=list(available_numeric.keys()),
        format_func=lambda k: available_numeric[k],
    )
    plot_df = mvp_df.dropna(subset=[numeric_key])
    fig3 = px.box(
        plot_df, x="Bank type", y=numeric_key, color="Bank type",
        color_discrete_map=COLOR_MAP, points="all",
    )
    fig3.update_layout(xaxis_title=None, yaxis_title=available_numeric[numeric_key],
                        showlegend=False, height=420)
    st.plotly_chart(fig3, use_container_width=True)

    avg_by_type = plot_df.groupby("Bank type")[numeric_key].mean().round(1)
    cols = st.columns(len(avg_by_type))
    for col, (bank_type, value) in zip(cols, avg_by_type.items()):
        col.metric(f"{bank_type} — average", value)

st.divider()

st.subheader("Manual visual annotation (analysis set)")
st.caption(
    "Human-annotated on the smaller analysis set (~50 records), not the full corpus — "
    "covers what LLM vision alone can't fully verify."
)

manual_df, manual_is_demo = load_manual_annotations()

if manual_is_demo or manual_df.empty:
    st.info(
        "No manual annotation data yet — this section will populate once your "
        "colleagues' results land in `data/features/visual_manual.csv` "
        "(columns: `asset_id`, `imagery_type`, `primary_cta_visible`, `price_in_viewport`)."
    )
else:
    # Join on asset_id to bring in Bank type for the breakdown.
    joined = manual_df.merge(
        mvp_df[["asset_id", "Bank type"]], on="asset_id", how="inner"
    )
    if joined.empty:
        st.info("The manual annotation file doesn't match any MVP page's asset_id yet.")
    else:
        st.caption(f"{len(joined)} of the analysis set's pages matched to MVP banks.")

        if "imagery_type" in joined.columns:
            counts = joined.groupby(["Bank type", "imagery_type"]).size().reset_index(name="Pages")
            totals = joined.groupby("Bank type").size().to_dict()
            counts["Share (%)"] = counts.apply(lambda r: r["Pages"] / totals[r["Bank type"]] * 100, axis=1)
            fig4 = px.bar(
                counts, x="Share (%)", y="imagery_type", color="Bank type", barmode="group",
                orientation="h", color_discrete_map=COLOR_MAP,
            )
            fig4.update_layout(yaxis_title=None, legend_title=None, height=300,
                                title="Imagery type")
            st.plotly_chart(fig4, use_container_width=True)

        manual_yes_no = {
            "primary_cta_visible": "CTA visible without scrolling (manual check)",
            "price_in_viewport": "Price visible without scrolling (manual check)",
        }
        rows2 = []
        for col, label in manual_yes_no.items():
            if col not in joined.columns:
                continue
            for bank_type in joined["Bank type"].unique():
                subset = joined[joined["Bank type"] == bank_type]
                rate = (subset[col].astype(str).str.lower() == "yes").mean() * 100
                rows2.append({"Trait": label, "Bank type": bank_type, "Share (%)": rate})

        if rows2:
            manual_yn_df = pd.DataFrame(rows2)
            fig5 = px.bar(
                manual_yn_df, x="Share (%)", y="Trait", color="Bank type", barmode="group",
                orientation="h", color_discrete_map=COLOR_MAP,
            )
            fig5.update_layout(yaxis_title=None, legend_title=None, height=250)
            st.plotly_chart(fig5, use_container_width=True)