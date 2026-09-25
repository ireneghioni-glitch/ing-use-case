"""Recommendations for ING, in two layers:

1. Measured — computed live from the same page-level data used on Market
   Positioning. Each indicator is paired with the practice it rests on and,
   where the academic corpus supports it, the source. Numbers always match
   the data.
2. From the research — ideas the academic corpus documents (mostly
   neobank practices) that our page-level features don't measure directly.
   Shown separately and labelled as ideas to test, never as findings.
"""
import json

import pandas as pd
import streamlit as st

from utils.config import MIN_VIABLE_RECORDS_PER_BANK, SUBJECT_BANK
from utils.data_loader import filter_mvp, load_features
from utils.style import inject_css, section

st.set_page_config(page_title="Recommendations", page_icon="✅", layout="wide")
inject_css()

GAP_OPPORTUNITY = 8    # pp: ING trails peers by at least this much -> "opportunity"
GAP_STRENGTH = 8       # pp: ING leads peers by at least this much -> "strength"
GAP_HIGH_PRIORITY = 20 # pp: gap large enough to flag as high priority
SMALL_N = 15

# Academic sources (names as stored in the RAG corpus)
SRC_NNG = "Nielsen Norman Group — Designing for Young Adults (3rd ed.)"
SRC_GENZ_FR = "La génération Z et la banque de détail"
SRC_26612 = "26612 — Gen Z marketing review (cites Nielsen 2018)"
SRC_DMT = "Digital Marketing Trends and Their Effectiveness in Reaching Gen Z Consumers"
SRC_IECON = "Sufianur (IECON 2025) — Gen Z and social-media campaigns"


# ------------------------------------------------------------------ field helpers
def as_list(x) -> list[str]:
    """Multi-value fields arrive as lists, numpy arrays (after a Parquet
    round-trip) or 'a|b' strings. Always return a clean list of strings."""
    if x is None:
        return []
    if isinstance(x, float) and pd.isna(x):
        return []
    if isinstance(x, str):
        return [p.strip() for p in x.split("|") if p.strip()]
    if hasattr(x, "tolist"):
        x = x.tolist()
    if isinstance(x, (list, tuple, set)):
        return [str(i).strip() for i in x if str(i).strip()]
    return []


def has_any(col: str, values: set[str]):
    """Row test: the multi-value field contains at least one of `values`."""
    return lambda d: d[col].map(lambda v: bool(set(as_list(v)) & values))


def has_real_value(col: str):
    """Row test: the multi-value field has at least one entry that isn't 'none'.
    An empty list counts as no value — the earlier version turned [] into ''
    and counted it as present."""
    return lambda d: d[col].map(lambda v: any(i.lower() != "none" for i in as_list(v)))


def guidance_present(v) -> bool:
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return v.strip().lower() == "yes"
    if isinstance(v, dict):
        return str(v.get("present", "")).lower() in ("yes", "true")
    return False


# ------------------------------------------------------------------ indicators
# Each indicator: test, practice (why it matters), source (academic corpus,
# or None if it's a general UX convention), action (if ING trails),
# protect (if ING leads).
INDICATORS = {
    "Peer proof (testimonials / customer numbers)": dict(
        test=has_any("trust_signals", {"testimonials", "customer_numbers"}),
        practice="Gen Z trusts peer reviews and user-generated content more than traditional advertising; "
                 "authentic testimonials build credibility.",
        source=SRC_26612,
        action="Add real student or young-customer testimonials, or a concrete customer count, to youth "
               "pages, placed near the CTA where a first-time customer is deciding.",
        protect="Peer proof is already a differentiator. Refresh the testimonials regularly so they stay "
                "authentic.",
    ),
    "Security reassurance (badge / deposit guarantee)": dict(
        test=has_any("trust_signals", {"security_badge", "deposit_guarantee"}),
        practice="Visible safety markers matter most when someone opens a first account with a brand. "
                 "Young adults also leave quickly if they feel tricked or deceived.",
        source=SRC_NNG,
        action="Add a short, visible reassurance line (deposit guarantee, secure app login, regulator "
               "reference) to youth pages that currently show none.",
        protect="Reassurance cues are in place — keep them visible as page designs change.",
    ),
    "Support channel shown": dict(
        test=has_real_value("support_options"),
        practice="When young adults can't find an answer on the website, some turn to social networks to "
                 "ask the brand directly, or to complain publicly.",
        source=SRC_NNG,
        action="Show at least one direct help channel (chat, app messaging, phone) on every youth page, "
               "so the question gets answered on the page instead of on social media.",
        protect="Help channels are visible. Keep them there, especially next to eligibility and pricing.",
    ),
    "Price visible without scrolling": dict(
        test=lambda d: d["price_in_initial_viewport"].eq("yes"),
        practice="Hidden cost undermines trust. Young adults leave quickly if they feel tricked or deceived.",
        source=SRC_NNG,
        action="Put indicative pricing in the first screen of youth pages, even a simple "
               "'€0/month for under-25s' line, rather than only after a click-through.",
        protect="Keep pricing visible early. It removes a common reason for hesitation.",
    ),
    "Price conditions next to the price": dict(
        test=lambda d: d["conditional_price_disclosure"].eq("adjacent"),
        practice="Conditions that surface late (age limits, fees after 25, minimum deposits) read as a "
                 "bait-and-switch, and that sense of being tricked is exactly what young adults react "
                 "against.",
        source=SRC_NNG,
        action="Place the conditions ('free until 25', 'fee after X') right next to the headline price "
               "instead of in a footnote or a separate page.",
        protect="Conditions are shown alongside the price, which is a transparency advantage worth keeping.",
    ),
    "Eligibility clearly stated": dict(
        test=lambda d: d["eligibility_stated"].eq("yes"),
        practice="Stating eligibility (age, residency, documents) early reduces abandoned applications "
                 "from users who discover disqualifying conditions late.",
        source=None,
        action="Add a short eligibility line ('18–24, Belgian resident, ID card') near the CTA on pages "
               "that don't state requirements yet.",
        protect="Eligibility is already stated clearly. Keep it visible as pages are updated.",
    ),
    "Guided opening steps": dict(
        test=lambda d: d["opening_guidance"].map(guidance_present),
        practice="Gen Z is intolerant of digital inefficiency. Showing how short the opening process is "
                 "lowers the perceived effort.",
        source=SRC_GENZ_FR,
        action="Show the opening journey as 3–4 numbered steps with a time cue ('open in 10 minutes "
               "from the app').",
        protect="Step-by-step opening guidance is already a strength. Keep it short and up to date.",
    ),
    "CTA visible without scrolling": dict(
        test=lambda d: d["primary_cta_visibility"].eq("yes"),
        practice="Gen Z predominantly reaches digital content on smartphones, where anything below the "
                 "first screen is easily missed.",
        source=SRC_DMT,
        action="Move the primary CTA into the first screen on pages where it currently sits lower.",
        protect="This is already a strength. Keep the CTA above the fold as new pages are built.",
    ),
    "Strong / moderate mobile cues": dict(
        test=lambda d: d["mobile_first_cues"].isin(["strong", "moderate"]),
        practice="Mobile optimisation is crucial for reaching Gen Z, who expect seamless smartphone "
                 "experiences.",
        source=SRC_DMT,
        action="Review weak-mobile pages on an actual phone. Shorten text blocks and make CTAs "
               "thumb-reachable.",
        protect="Mobile-first layout is in place. Keep testing new pages on a real device before launch.",
    ),
    "Clear, specific value proposition": dict(
        test=lambda d: d["value_proposition_clarity"].eq("clear-specific"),
        practice="A single, concrete benefit stated up front reads as more credible than generic claims, "
                 "which matters for a generation with low tolerance for outdated or vague experiences.",
        source=SRC_26612,
        action="Rewrite the opening line of lower-scoring pages to name one concrete benefit "
               "(a number, a feature, a price).",
        protect="Specific opening claims are a clear advantage. Keep new pages to the same standard.",
    ),
    "Names its youth audience": dict(
        test=lambda d: d["audience_explicit"].eq("yes"),
        practice="Gen Z values personalised experiences. Naming the audience ('for students', "
                 "'under 25') signals relevance immediately.",
        source=SRC_26612,
        action="Add a short audience line near the top of pages that don't yet say who they're for.",
        protect="Naming the audience directly is a point of difference. Keep it front and centre.",
    ),
    "Specific-action CTA": dict(
        test=lambda d: d["cta_clarity"].eq("specific-action"),
        practice="Action-specific CTA copy ('Open your account in 5 minutes') reads as more credible than "
                 "vague copy ('Learn more').",
        source=None,
        action="Replace vague CTA labels with a specific action and, where relevant, a time or effort cue.",
        protect="Specific CTA copy is the norm. Keep new CTAs equally concrete.",
    ),
    "Real people in imagery": dict(
        test=lambda d: d["visual_type"].eq("real-people"),
        practice="Visual content and brand authenticity shape how Gen Z responds to campaigns. Real "
                 "people read as more authentic than stock product shots.",
        source=SRC_IECON,
        action="Where imagery is abstract or product-only, test adding a real young customer alongside "
               "it rather than replacing it outright.",
        protect="People-led imagery is part of the youth pages' identity. It's worth protecting.",
    ),
    "Lifestyle / rewards as main benefit": dict(
        test=lambda d: d["main_benefit"].eq("lifestyle-rewards"),
        practice="Neobanks targeting Gen Z use partner cashback (for example Pixpay's partnerships) and "
                 "rewards to attract and keep young customers.",
        source=SRC_GENZ_FR,
        action="If ING offers perks to young customers (partner discounts, cashback, student deals), "
               "lead with them on at least some youth pages instead of keeping them in the small print.",
        protect="Rewards-led messaging is already present. Keep the perks concrete and current.",
    ),
    "Gain-framed persuasion": dict(
        test=lambda d: d["persuasive_framing"].eq("gain"),
        practice="Gain-framed messaging ('save', 'earn', 'get') is generally associated with stronger "
                 "response in acquisition contexts than loss-framed messaging. Worth A/B testing.",
        source=None,
        action="Reframe pages that lead with loss- or fear-based language around what the customer gains.",
        protect="Gain framing is already the default. Keep testing against it.",
    ),
}

# Ideas documented in the academic corpus that our page features don't measure.
RESEARCH_IDEAS = [
    dict(
        title="Build financial education into the youth offer",
        evidence="To help Gen Z manage money, neobanks use discovery simulators and gamification "
                 "(Xaalys), online courses (Osper), savings modules tied to a personal project (Vybe) "
                 "and paid 'to-do' tasks (Greenlight). These tools also generate behavioural data "
                 "that improves the offer.",
        source=SRC_GENZ_FR,
        action="Show project-based savings goals or money-management tips on youth pages. If ING's app "
               "already has comparable features, the youth pages are where they should be visible.",
    ),
    dict(
        title="Use peers and ambassadors as reassurance",
        evidence="Gen Z trusts peer reviews and user-generated content more than advertising. Vybe's "
                 "influencer programme is cited as a way to deliver reassurance through the community.",
        source=f"{SRC_26612}; {SRC_GENZ_FR}",
        action="Pilot a student-ambassador or testimonial programme and feature its content directly "
               "on the youth pages, not only on social media.",
    ),
    dict(
        title="Offer concrete, youth-relevant perks",
        evidence="Partner cashback on brands young people already buy from (e.g. Pixpay with PlayStation "
                 "and Monoprix) is one of the levers neobanks use to engage Gen Z.",
        source=SRC_GENZ_FR,
        action="Assess whether a small set of partner perks relevant to 18–25s would strengthen the "
               "youth proposition, and test it on one product page first.",
    ),
    dict(
        title="Be reachable where young customers ask questions",
        evidence="Young adults who can't find an answer on a website sometimes contact the brand through "
                 "social networks instead, or complain there publicly.",
        source=SRC_NNG,
        action="Link youth pages to a fast answer channel (chat or in-app messaging), and monitor social "
               "channels for questions about the youth account.",
    ),
]


def rate(fn, d) -> float:
    try:
        return fn(d).astype(bool).mean() * 100 if len(d) else float("nan")
    except KeyError:
        return float("nan")


def source_line(src) -> str:
    return f"<br><span style='opacity:.7;font-size:.85em'>Source: {src}</span>" if src else ""


# ------------------------------------------------------------------ header & data
st.markdown(
    """
<div class="hero">
  <div class="eyebrow">ING Belgium · Youth Acquisition</div>
  <h1>Recommendations</h1>
  <p>Measured recommendations are computed live from the page-level data used on Market Positioning,
  each paired with the practice and research it rests on. Ideas from the research are shown separately,
  because our page data doesn't measure them directly.</p>
</div>
""",
    unsafe_allow_html=True,
)

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data**. The recommendations below reflect demo data, not real findings.",
               icon="⚠️")

mvp = filter_mvp(df).copy()
ING = mvp[mvp["bank"] == SUBJECT_BANK]
if ING.empty:
    st.info(f"No pages for {SUBJECT_BANK} yet, so recommendations can't be computed.")
    st.stop()

# Peer banks below the minimum sample are excluded from the benchmark: with
# 2 pages a bank can only score 0 / 50 / 100 %, and that noise would carry
# the same weight as a bank with dozens of pages.
pages_per_bank = mvp.groupby("bank").size()
peer_counts = pages_per_bank.drop(SUBJECT_BANK, errors="ignore")
valid_peers = peer_counts[peer_counts >= MIN_VIABLE_RECORDS_PER_BANK].index.tolist()
excluded_peers = peer_counts[peer_counts < MIN_VIABLE_RECORDS_PER_BANK]

if not valid_peers:
    st.info(f"No peer bank has at least {MIN_VIABLE_RECORDS_PER_BANK} pages, so no benchmark is possible.")
    st.stop()

bank_rates = pd.DataFrame(
    {bank: {k: rate(v["test"], sub) for k, v in INDICATORS.items()} for bank, sub in mvp.groupby("bank")}
).T.dropna(axis=1, how="all")
labels = [l for l in INDICATORS if l in bank_rates.columns]
ing_r = bank_rates.loc[SUBJECT_BANK, labels]
peer_avg = bank_rates.loc[valid_peers, labels].mean()   # each valid peer bank counts once
gap = (ing_r - peer_avg).dropna()
n_ing = len(ING)

if not excluded_peers.empty:
    names = ", ".join(f"{b} ({n} pages)" for b, n in excluded_peers.items())
    st.info(f"Excluded from the peer benchmark (fewer than {MIN_VIABLE_RECORDS_PER_BANK} pages): {names}. "
            "Their figures still appear in the table at the bottom.", icon="ℹ️")
if n_ing < SMALL_N or len(valid_peers) < 2:
    st.info(f"Small sample: {n_ing} {SUBJECT_BANK} pages against {len(valid_peers)} peer bank(s). "
            "Treat the sizes of these gaps as directional.", icon="ℹ️")

opportunities = gap[gap <= -GAP_OPPORTUNITY].sort_values()
strengths = gap[gap >= GAP_STRENGTH].sort_values(ascending=False)


def ing_count(label: str) -> int:
    return int(round(ing_r[label] / 100 * n_ing))


# ------------------------------------------------------------------ summary
section("At a glance", f"Benchmark: average of {len(valid_peers)} peer banks ({', '.join(valid_peers)}), "
                        "each bank weighted equally.")
top = opportunities.head(3)
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Top priorities**")
    if top.empty:
        st.markdown(f"No trait where {SUBJECT_BANK} trails peers by {GAP_OPPORTUNITY} pp or more.")
    for label, g in top.items():
        st.markdown(f"- **{label}**: {ing_r[label]:.0f}% vs {peer_avg[label]:.0f}% ({g:+.0f} pp)")
with c2:
    st.markdown("**Strengths to protect**")
    if strengths.empty:
        st.markdown(f"No trait where {SUBJECT_BANK} leads peers by {GAP_STRENGTH} pp or more.")
    for label, g in strengths.head(3).items():
        st.markdown(f"- **{label}**: {ing_r[label]:.0f}% vs {peer_avg[label]:.0f}% ({g:+.0f} pp)")

# ------------------------------------------------------------------ opportunities
section("Opportunities (measured)", f"Traits where {SUBJECT_BANK} trails the peer average by "
                                    f"{GAP_OPPORTUNITY} pp or more, largest gap first.")
if opportunities.empty:
    closest = gap[gap < 0].sort_values().head(3)
    st.success(f"{SUBJECT_BANK} doesn't trail the peer average by {GAP_OPPORTUNITY} pp or more on any "
               "measured trait.")
    if not closest.empty:
        st.caption("Smaller gaps to watch: " + ", ".join(f"{l} ({g:+.0f} pp)" for l, g in closest.items()))

for i, (label, g) in enumerate(opportunities.items(), start=1):
    spec = INDICATORS[label]
    priority = "High priority" if g <= -GAP_HIGH_PRIORITY else "Medium priority"
    with st.container(border=True):
        st.markdown(f"##### {i}. {label} · <span style='font-size:.8em'>{priority}</span>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(
                f'<div class="kpi"><div class="v">{ing_r[label]:.0f}%</div>'
                f'<div class="l">{SUBJECT_BANK} ({ing_count(label)} of {n_ing} pages), vs '
                f'{peer_avg[label]:.0f}% peer average (<b>{g:+.0f} pp</b>)</div></div>',
                unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Why it matters:** {spec['practice']}{source_line(spec['source'])}",
                        unsafe_allow_html=True)
            st.markdown(f"**Suggested action:** {spec['action']}")

# ------------------------------------------------------------------ strengths
if not strengths.empty:
    section("Strengths to protect", f"Traits where {SUBJECT_BANK} leads peers by {GAP_STRENGTH} pp or more.")
    items = list(strengths.items())
    for row_start in range(0, len(items), 3):
        cols = st.columns(3)
        for col, (label, g) in zip(cols, items[row_start:row_start + 3]):
            spec = INDICATORS[label]
            with col:
                st.markdown(
                    f'<div class="step"><div class="num">✓</div><h4>{label}</h4>'
                    f'<p><b>{ing_r[label]:.0f}%</b> ({ing_count(label)} of {n_ing} pages) vs '
                    f'{peer_avg[label]:.0f}% peer average ({g:+.0f} pp)<br><br>{spec["protect"]}'
                    f'{source_line(spec["source"])}</p></div>',
                    unsafe_allow_html=True)

# ------------------------------------------------------------------ research ideas
section("Ideas from the research (not measured)",
        "Practices documented in the academic corpus that our page features don't capture directly. "
        "Test them before rolling them out. They aren't findings about ING's pages.")
for idea in RESEARCH_IDEAS:
    with st.container(border=True):
        st.markdown(f"##### {idea['title']}")
        st.markdown(f"**What the research says:** {idea['evidence']}{source_line(idea['source'])}",
                    unsafe_allow_html=True)
        st.markdown(f"**Idea for {SUBJECT_BANK}:** {idea['action']}")

# ------------------------------------------------------------------ evidence
with st.expander("Underlying figures, bank by bank"):
    show_df = bank_rates[labels].round(0).astype("Int64")
    show_df.insert(0, "Pages (n)", pages_per_bank.reindex(show_df.index).astype("Int64"))
    show_df.insert(1, "In benchmark", ["subject" if b == SUBJECT_BANK else ("yes" if b in valid_peers else "no")
                                       for b in show_df.index])
    st.dataframe(show_df, use_container_width=True)
    st.caption("Share of pages (%) showing each trait, one row per bank. Banks under "
               f"{MIN_VIABLE_RECORDS_PER_BANK} pages are shown but excluded from the peer average.")

st.divider()
st.caption(
    "Out of scope: conversion or revenue impact (no internal performance data was available) and any "
    "youth-vs-adult comparison for the same bank. Practices are drawn from the project's academic corpus "
    "or widely used UX conventions, not from ING's own funnel data. Validate with A/B testing before "
    "rolling changes out broadly."
)