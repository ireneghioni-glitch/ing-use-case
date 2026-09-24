import pandas as pd
import plotly.express as px
import streamlit as st

from utils.config import SUBJECT_BANK, MVP_BANKS, BANK_TYPE
from utils.data_loader import load_features, filter_mvp

st.set_page_config(page_title="ING's Positioning", page_icon="📍", layout="wide")

st.title("Where ING stands")
st.caption("Cross-bank comparison on youth-oriented pages — the 5 MVP banks only.")

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data**.", icon="⚠️")

mvp_df = filter_mvp(df)

# --- Headline indicators ---
st.header("At a glance")
cols = st.columns(4)

with cols[0]:
    ing_playful_share = (
        mvp_df[mvp_df["bank"] == SUBJECT_BANK]["tone"].isin(["playful", "persuasive"]).mean() * 100
    )
    st.metric(f"{SUBJECT_BANK} — persuasive/playful tone", f"{ing_playful_share:.0f}%")

with cols[1]:
    ing_cta_visible = (mvp_df[mvp_df["bank"] == SUBJECT_BANK]["primary_cta_visibility"] == "yes").mean() * 100
    st.metric(f"{SUBJECT_BANK} — CTA visible without scrolling", f"{ing_cta_visible:.0f}%")

with cols[2]:
    ing_clear = (
        mvp_df[mvp_df["bank"] == SUBJECT_BANK]["value_proposition_clarity"] == "clear-specific"
    ).mean() * 100
    st.metric(f"{SUBJECT_BANK} — clear, specific value proposition", f"{ing_clear:.0f}%")

with cols[3]:
    ing_audience_explicit = (
        mvp_df[mvp_df["bank"] == SUBJECT_BANK]["audience_explicit"] == "yes"
    ).mean() * 100
    st.metric(f"{SUBJECT_BANK} — names its youth audience", f"{ing_audience_explicit:.0f}%")

st.divider()

# --- ING vs market average, on a few key yes/no and categorical rates ---
st.header(f"{SUBJECT_BANK} vs the other {len(MVP_BANKS) - 1} MVP banks")

metrics = {
    "CTA visible without scrolling": ("primary_cta_visibility", "yes"),
    "Price visible without scrolling": ("price_in_initial_viewport", "yes"),
    "Clear, specific value proposition": ("value_proposition_clarity", "clear-specific"),
    "Names its youth audience": ("audience_explicit", "yes"),
    "Eligibility clearly stated": ("eligibility_stated", "yes"),
}

rows = []
for label, (col, target) in metrics.items():
    ing_rate = (mvp_df[mvp_df["bank"] == SUBJECT_BANK][col] == target).mean() * 100
    market_rate = (mvp_df[mvp_df["bank"] != SUBJECT_BANK][col] == target).mean() * 100
    rows.append({"Metric": label, "ING": ing_rate, "Other MVP banks (avg)": market_rate})

comparison_df = pd.DataFrame(rows)
melted = comparison_df.melt(id_vars="Metric", var_name="Who", value_name="Share (%)")

fig = px.bar(
    melted, x="Share (%)", y="Metric", color="Who", barmode="group", orientation="h",
    color_discrete_map={"ING": "#FF6200", "Other MVP banks (avg)": "#8A8A8A"},
)
fig.update_layout(yaxis_title=None, legend_title=None, height=350)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Read as: on each metric, what share of ING's youth pages show this trait, "
    "compared to the average across the other 4 MVP banks."
)