"""Recommendations: generated live from the same indicators used on the
Market Positioning page, each paired with a widely used UX / conversion-rate
best practice — not fixed text, so the numbers here always match the data."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.config import BANK_TYPE, SUBJECT_BANK
from utils.data_loader import filter_mvp, load_features
from utils.style import inject_css, section

st.set_page_config(page_title="Recommendations", page_icon="✅", layout="wide")
inject_css()

ORANGE, NAVY, GREEN, INK = "#FF6200", "#3B4A6B", "#3F8F87", "#2B2D33"
GAP_OPPORTUNITY = 8   # pp: ING trails peers by at least this much -> "opportunity"
GAP_STRENGTH = 8      # pp: ING leads peers by at least this much -> "strength"
SMALL_N = 15

# Indicator -> (test, why it's a recognised industry practice, action if ING trails,
#               note if ING already leads and should protect the advantage)
INDICATORS = {
    "Price visible without scrolling": dict(
        test=lambda d: d["price_in_initial_viewport"].eq("yes"),
        practice="Disclosing cost or key terms before a click-through is standard consumer-transparency "
                 "practice in retail banking, and a common driver of drop-off and complaints when it's missing.",
        action="Surface indicative pricing (fees, minimum balance, conditions) in the first screen of youth "
               "pages, even a simple 'from €0/month' line, rather than only after the user clicks through.",
        protect="Keep pricing visible early — it removes a common reason for hesitation before signup.",
    ),
    "CTA visible without scrolling": dict(
        test=lambda d: d["primary_cta_visibility"].eq("yes"),
        practice="Placing the primary call-to-action within the first viewport is a long-standing "
                 "conversion-rate-optimisation convention, especially important on mobile where most youth "
                 "traffic lands.",
        action="Move the primary CTA above the fold on pages where it currently sits lower, and keep the "
               "button label consistent with the page's main promise.",
        protect="This is already a strength — keep the CTA above the fold as new pages are built.",
    ),
    "Clear, specific value proposition": dict(
        test=lambda d: d["value_proposition_clarity"].eq("clear-specific"),
        practice="Landing pages with a single, specific value proposition stated up front consistently "
                 "outperform vague or generic claims in usability testing.",
        action="Rewrite the opening line of lower-scoring pages to name one concrete benefit "
               "(a number, a feature, a price) instead of a general claim.",
        protect="Specific, concrete opening claims are working — keep new pages to the same standard.",
    ),
    "Names its youth audience": dict(
        test=lambda d: d["audience_explicit"].eq("yes"),
        practice="Explicitly naming the audience ('for students', 'under 25') signals relevance immediately "
                 "and is a standard personalisation technique in acquisition marketing.",
        action="Add a short audience line near the top of pages that don't yet name who the page is for.",
        protect="Naming the audience directly is a clear point of difference — keep it front and centre.",
    ),
    "Eligibility clearly stated": dict(
        test=lambda d: d["eligibility_stated"].eq("yes"),
        practice="Stating eligibility (age, residency, documents needed) early reduces abandoned "
                 "applications caused by users discovering disqualifying conditions late in the funnel.",
        action="Add a short eligibility line or FAQ near the CTA on pages that don't state requirements yet.",
        protect="Eligibility is already stated clearly — keep it visible as pages are updated.",
    ),
    "Specific-action CTA": dict(
        test=lambda d: d["cta_clarity"].eq("specific-action"),
        practice="Action-specific CTA copy ('Open your account in 5 minutes') is generally read as more "
                 "credible and clickable than vague copy ('Learn more', 'Discover').",
        action="Replace vague CTA labels with a specific action and, where relevant, a time or effort cue.",
        protect="Specific CTA copy is already the norm — keep new CTAs equally concrete.",
    ),
    "Real people in imagery": dict(
        test=lambda d: d["visual_type"].eq("real-people"),
        practice="Human imagery tends to increase perceived trust and relatability, which matters most "
                 "when a first-time customer is evaluating a new financial relationship.",
        action="Where imagery is currently abstract or product-only, test adding a real-person visual "
               "alongside it rather than replacing it outright.",
        protect="People-led imagery is a recognisable part of the brand's youth pages — worth protecting "
                "as a visual identity, even while testing product shots elsewhere.",
    ),
    "Strong / moderate mobile cues": dict(
        test=lambda d: d["mobile_first_cues"].isin(["strong", "moderate"]),
        practice="With youth banking traffic overwhelmingly mobile, pages built mobile-first — thumb-"
                 "reachable CTAs, short paragraphs, minimal horizontal scrolling — convert more reliably.",
        action="Review the pages with weak mobile cues on an actual phone, and shorten blocks of text "
               "that force excessive scrolling.",
        protect="Mobile-first layout is already in place — keep testing new pages on a real device before launch.",
    ),
    "At least one trust signal": dict(
        test=lambda d: ~d["trust_signals"].fillna("none").eq("none"),
        practice="Visible trust markers (security badges, deposit guarantees, regulator mentions) are a "
                 "standard trust-building technique, especially for a first account with a given brand.",
        action="Add at least one trust signal (security badge, guarantee, regulator reference) to pages "
               "that currently show none.",
        protect="Trust signals are already present on most pages — keep them visible as designs change.",
    ),
    "Gain-framed persuasion": dict(
        test=lambda d: d["persuasive_framing"].eq("gain"),
        practice="Gain-framed messaging ('save', 'earn', 'get') is generally associated with stronger "
                 "response in acquisition contexts than loss-framed messaging, though this is worth "
                 "A/B testing rather than assuming.",
        action="Reframe pages that currently lead with loss- or fear-based language ('don't miss out', "
               "'avoid fees') around what the customer gains instead.",
        protect="Gain-framed language is already the norm — a good default to keep testing against.",
    ),
}


def as_pipe(x):
    """Multi-value fields may arrive as 'a|b' strings OR as lists / numpy arrays."""
    if isinstance(x, str):
        return x
    if x is None:
        return ""
    if isinstance(x, (list, tuple, set)) or hasattr(x, "tolist"):
        items = x.tolist() if hasattr(x, "tolist") else list(x)
        items = items if isinstance(items, list) else [items]
        return "|".join(str(i) for i in items)
    return ""


def rate(fn, d):
    try:
        return fn(d).mean() * 100 if len(d) else float("nan")
    except KeyError:
        return float("nan")


# ------------------------------------------------------------------ header & data
st.markdown(
    f"""
<div class="hero">
  <div class="eyebrow">ING Belgium · Youth Acquisition</div>
  <h1>Recommendations</h1>
  <p>Computed live from the same page-level data used on Market Positioning, each finding paired
  with a widely used UX / conversion best practice. Numbers here update automatically as the
  underlying data changes.</p>
</div>
""",
    unsafe_allow_html=True,
)

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data** — recommendations below reflect the demo data, not real findings.",
               icon="⚠️")

mvp = filter_mvp(df).copy()
if "trust_signals" in mvp.columns:
    mvp["trust_signals"] = mvp["trust_signals"].map(as_pipe)

ING = mvp[mvp["bank"] == SUBJECT_BANK]
PEERS = mvp[mvp["bank"] != SUBJECT_BANK]
if ING.empty or PEERS.empty:
    st.info(f"Need pages for {SUBJECT_BANK} and at least one other bank to generate recommendations.")
    st.stop()

bank_rates = pd.DataFrame(
    {bank: {k: rate(v["test"], sub) for k, v in INDICATORS.items()} for bank, sub in mvp.groupby("bank")}
).T.dropna(axis=1, how="all")
labels = [l for l in INDICATORS if l in bank_rates.columns]
ing_r = bank_rates.loc[SUBJECT_BANK]
peer_avg = bank_rates.drop(SUBJECT_BANK).mean()   # each peer bank counts once
n_ing = len(ING)
gap = (ing_r - peer_avg).dropna().sort_values()

if n_ing < SMALL_N or len(PEERS["bank"].unique()) < 2:
    st.info(f"Small sample: {n_ing} {SUBJECT_BANK} pages across {PEERS['bank'].nunique()} peer banks. "
            "Treat the sizes of these gaps as directional, and confirm with A/B testing before rolling "
            "out changes broadly.", icon="ℹ️")

opportunities = gap[gap <= -GAP_OPPORTUNITY].sort_values()
strengths = gap[gap >= GAP_STRENGTH].sort_values(ascending=False)
if opportunities.empty:
    opportunities = gap.sort_values().head(3)

# ------------------------------------------------------------------ opportunities
section("Opportunities", "Ranked by the size of the gap to the peer average.")
for i, (label, g) in enumerate(opportunities.items(), start=1):
    spec = INDICATORS[label]
    with st.container(border=True):
        st.markdown(f"##### {i}. {label}")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(
                f'<div class="kpi"><div class="v">{ing_r[label]:.0f}%</div>'
                f'<div class="l">{SUBJECT_BANK}, vs {peer_avg[label]:.0f}% peer average '
                f'(<b>{g:+.0f} pp</b>)</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Why it matters:** {spec['practice']}")
            st.markdown(f"**Suggested action:** {spec['action']}")

# ------------------------------------------------------------------ strengths
if not strengths.empty:
    section("Strengths to protect", f"Traits where {SUBJECT_BANK} already leads peers by 8 pp or more.")
    cols = st.columns(min(3, len(strengths)))
    for col, (label, g) in zip(cols * (len(strengths) // len(cols) + 1), strengths.items()):
        spec = INDICATORS[label]
        with col:
            st.markdown(
                f'<div class="step"><div class="num">✓</div><h4>{label}</h4>'
                f'<p><b>{ing_r[label]:.0f}%</b> vs {peer_avg[label]:.0f}% peer average '
                f'({g:+.0f} pp)<br><br>{spec["protect"]}</p></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ evidence
with st.expander("Underlying figures, bank by bank"):
    show_df = bank_rates[labels].round(0).astype("Int64")
    st.dataframe(show_df, use_container_width=True)
    st.caption("Share of pages (%) showing each trait, one row per bank.")

st.divider()
st.caption(
    "Out of scope for these recommendations: conversion or revenue impact (no internal performance "
    "data was available), and any youth-vs-adult comparison for the same bank. Practices referenced "
    "above are general, widely cited UX and conversion-rate-optimisation conventions, not claims "
    "specific to ING's own funnel — validate with A/B testing before rolling changes out broadly."
)
