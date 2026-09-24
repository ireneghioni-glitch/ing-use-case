import streamlit as st

from utils.config import SUBJECT_BANK

st.set_page_config(page_title="Recommendations", page_icon="✅", layout="wide")

st.title("Recommendations")
st.caption(f"Concrete next steps for {SUBJECT_BANK}, each tied to an observation and its grounding.")

st.info(
    "Recommendations below are placeholders — replace with the findings from the "
    "Positioning and Traditional vs Digital Challenger pages once the real pipeline "
    "output is loaded. Keep each one inside the acknowledged scope: no ROI/conversion "
    "claims, no youth-vs-adult claims (not measured in this MVP).",
    icon="✏️",
)

RECOMMENDATIONS = [
    {
        "title": "Make the primary CTA visible without scrolling on youth pages",
        "observation": "ING's youth pages show the CTA above the fold less often than the "
                        "digital challengers in this comparison.",
        "why": "Retrieved from the RAG on the 'Why It Matters' page — see the sourced "
               "passage on CTA visibility and conversion-adjacent engagement.",
        "action": "Audit the top 5 highest-traffic youth pages and move the primary CTA "
                   "above the fold where it currently isn't.",
    },
    {
        "title": "Name the youth audience explicitly earlier in the page",
        "observation": "Pages that explicitly name their audience ('students', 'under 25') "
                        "show higher audience-explicit rates among digital challengers than ING.",
        "why": "See the sourced passage on explicit audience framing in the market-research corpus.",
        "action": "Add a clear audience statement in the first screen of key youth pages.",
    },
]

for i, rec in enumerate(RECOMMENDATIONS, start=1):
    with st.container(border=True):
        st.subheader(f"{i}. {rec['title']}")
        st.markdown(f"**Observation:** {rec['observation']}")
        st.markdown(f"**Why it matters:** {rec['why']}")
        st.markdown(f"**Suggested action:** {rec['action']}")

st.divider()
st.caption(
    "Out of scope for these recommendations: conversion/ROI impact (no internal "
    "performance data), and any youth-vs-adult comparison for the same bank."
)
