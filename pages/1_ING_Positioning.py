import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.config import (
    SUBJECT_BANK, BANK_TYPE, BANK_TYPE_LABEL, TARGET_RECORDS_PER_BANK, MIN_VIABLE_RECORDS_PER_BANK,
)
from utils.data_loader import load_features, filter_mvp, load_manual_annotations
from utils.style import inject_css

st.set_page_config(page_title="ING's Positioning", page_icon="📍", layout="wide")
inject_css()

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
AUDIENCE_TEXT = "youth (12–25)"
IN_LINE_THRESHOLD = 10  # pts: below this gap vs peers, we say "in line"

ING_COLOR = "#FF6200"
GREY = "#A0A0A0"
TYPE_COLORS = {"Traditional bank": "#4472C4", "Digital challenger": "#7B4FA3"}
GROUP_COLORS = {SUBJECT_BANK: ING_COLOR, **TYPE_COLORS}

# Each criterion = one yes/no readout of a page (share of pages showing the trait).
CRITERIA = {
    "value_prop": {
        "label": "Clear, specific value proposition",
        "col": "value_proposition_clarity", "target": ["clear-specific"],
        "action": "Lead each page with one specific benefit instead of a generic promise.",
    },
    "cta_specific": {
        "label": "Specific call-to-action",
        "col": "cta_clarity", "target": ["specific-action"],
        "action": "Replace generic buttons (\"Learn more\") with action-specific wording (\"Open your account\").",
    },
    "cta_visible": {
        "label": "CTA visible without scrolling",
        "col": "primary_cta_visibility", "target": ["yes"],
        "action": "Bring the main call-to-action into the first screen on every youth page.",
    },
    "price_visible": {
        "label": "Price visible without scrolling",
        "col": "price_in_initial_viewport", "target": ["yes"],
        "action": "Show the price (or \"free\") in the first screen so cost is never a hidden barrier.",
    },
    "audience": {
        "label": "Names its youth audience",
        "col": "audience_explicit", "target": ["yes"],
        "action": "Name the youth audience explicitly (age range, student status) so young visitors recognise themselves.",
    },
    "eligibility": {
        "label": "Eligibility clearly stated",
        "col": "eligibility_stated", "target": ["yes"],
        "action": "State upfront who can open the product (age, status) to avoid drop-off.",
    },
}
HEADLINE_KEYS = ["value_prop", "cta_visible", "audience", "price_visible"]

CATEGORICAL_FEATURES = {
    "tone": "Tone",
    "sentiment": "Sentiment",
    "value_proposition_clarity": "Value proposition clarity",
    "cta_clarity": "CTA clarity",
    "verbosity": "Verbosity",
    "distinctiveness": "Distinctiveness",
}
CATEGORY_ORDER = {
    "tone": ["formal", "simple", "persuasive", "playful"],
    "value_proposition_clarity": ["clear-specific", "clear-vague", "unclear"],
    "cta_clarity": ["specific-action", "vague-action", "none"],
    "verbosity": ["low", "medium", "high"],
    "distinctiveness": ["high", "medium", "low"],
    "sentiment": ["positive", "reassuring", "neutral", "urgent"],
}
NUMERIC_FEATURES = {
    "word_count": "Word count",
    "jargon_density": "Jargon density (financial terms per 100 words)",
    "mean_sentence_length": "Average sentence length (words)",
}

# Modelling choices for the positioning map (documented in the method tab).
TONE_SCORE = {"formal": 0, "simple": 1, "persuasive": 2, "playful": 3}
CLARITY_SCORE = {"clear-specific": 100, "clear-vague": 50, "unclear": 0}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def share(frame: pd.DataFrame, col: str, target) -> float:
    if frame.empty or col not in frame.columns:
        return 0.0
    targets = target if isinstance(target, (list, tuple, set)) else [target]
    return frame[col].isin(targets).mean() * 100


def with_n_labels(frame: pd.DataFrame, col: str) -> pd.DataFrame:
    """Replace group labels by 'label (n=…)' so every chart shows its sample size."""
    frame = frame.copy()
    sizes = frame[col].map(frame.groupby(col).size())
    frame[col] = frame[col].astype(str) + " (n=" + sizes.astype(str) + ")"
    return frame


def category_shares(frame: pd.DataFrame, group_col: str, feature: str) -> pd.DataFrame:
    counts = frame.groupby([group_col, feature]).size().reset_index(name="Pages")
    totals = frame.groupby(group_col).size()
    counts["Share (%)"] = counts["Pages"] / counts[group_col].map(totals) * 100
    return counts


def stacked_share(frame, group_col, feature, height=320, group_order=None, color_map=None):
    """100% stacked horizontal bars: distribution of a categorical feature per group."""
    labelled = with_n_labels(frame, group_col)
    data = category_shares(labelled, group_col, feature)
    data["label"] = data["Share (%)"].apply(lambda v: f"{v:.0f}%" if v >= 8 else "")
    orders = {feature: [c for c in CATEGORY_ORDER.get(feature, []) if c in set(data[feature])]}
    if group_order:
        orders[group_col] = [f"{g} (n={(frame[group_col] == g).sum()})"
                             for g in group_order if g in set(frame[group_col])]
    fig = px.bar(
        data, x="Share (%)", y=group_col, color=feature, orientation="h",
        barmode="stack", text="label", category_orders=orders,
        color_discrete_map=color_map,
    )
    fig.update_layout(yaxis_title=None, legend_title=CATEGORICAL_FEATURES.get(feature, feature),
                      height=height, xaxis_range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)


def grouped_bar(data, x, y, color, color_map, height, title=None):
    fig = px.bar(
        data, x=x, y=y, color=color, barmode="group", orientation="h",
        color_discrete_map=color_map, title=title,
    )
    fig.update_layout(yaxis_title=None, legend_title=None, height=height, xaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)


def build_rates(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per bank x criterion: k pages showing the trait out of n, and the rate."""
    rows = []
    for bank, g in frame.groupby("bank"):
        for key, c in CRITERIA.items():
            hit = g[c["col"]].isin(c["target"])
            rows.append({
                "bank": bank, "key": key, "label": c["label"],
                "k": int(hit.sum()), "n": len(g), "rate": hit.mean() * 100,
            })
    return pd.DataFrame(rows)


def build_gaps(rates: pd.DataFrame) -> pd.DataFrame:
    """ING vs the MEDIAN of the other banks' rates (each bank counts once,
    so a bank with more pages doesn't weigh more)."""
    out = []
    for key, g in rates.groupby("key"):
        ing = g[g["bank"] == SUBJECT_BANK]
        peers = g[g["bank"] != SUBJECT_BANK]
        if ing.empty or peers.empty:
            continue
        ing_rate = ing["rate"].iloc[0]
        out.append({
            "key": key, "label": ing["label"].iloc[0],
            "ing": ing_rate, "ing_k": int(ing["k"].iloc[0]), "ing_n": int(ing["n"].iloc[0]),
            "peer_median": peers["rate"].median(),
            "gap": ing_rate - peers["rate"].median(),
            "rank": 1 + int((peers["rate"] > ing_rate).sum()),
            "n_banks": len(g),
        })
    return pd.DataFrame(out).sort_values("gap", ascending=False).reset_index(drop=True)


def cohen_kappa(a: pd.Series, b: pd.Series) -> float:
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in set(a) | set(b))
    return np.nan if pe == 1 else (po - pe) / (1 - pe)


def dumbbell(gaps: pd.DataFrame, rates: pd.DataFrame):
    g = gaps.sort_values("gap")  # ascending -> biggest lead ends up at the top
    labels = {r.key: f"{r.label}  ({r.gap:+.0f} pts)" for r in g.itertuples()}
    fig = go.Figure()
    for r in g.itertuples():
        fig.add_trace(go.Scatter(
            x=[r.peer_median, r.ing], y=[labels[r.key]] * 2, mode="lines",
            line=dict(color="#D0D0D0", width=5), showlegend=False, hoverinfo="skip",
        ))
    peers = rates[rates["bank"] != SUBJECT_BANK]
    fig.add_trace(go.Scatter(
        x=peers["rate"], y=peers["key"].map(labels), mode="markers", name="Other banks",
        marker=dict(color=GREY, size=9, opacity=0.75), text=peers["bank"],
        hovertemplate="%{text}: %{x:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=g["peer_median"], y=g["key"].map(labels), mode="markers", name="Peer median",
        marker=dict(color="#333333", size=13, symbol="diamond"),
        hovertemplate="Peer median: %{x:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=g["ing"], y=g["key"].map(labels), mode="markers", name=SUBJECT_BANK,
        marker=dict(color=ING_COLOR, size=16, line=dict(color="white", width=1.5)),
        text=[f"{r.ing_k}/{r.ing_n} pages" for r in g.itertuples()],
        hovertemplate=f"{SUBJECT_BANK}: %{{x:.0f}}% (%{{text}})<extra></extra>",
    ))
    fig.update_yaxes(categoryorder="array", categoryarray=list(labels.values()), title=None)
    fig.update_xaxes(range=[-5, 105], title="% of pages showing the trait")
    fig.update_layout(height=110 + 62 * len(g), legend_title=None,
                      legend=dict(orientation="h", y=1.12, x=0))
    return fig


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------
# Source: llm_claude.parquet + deterministic.parquet + cleaned_assets.jsonl (all scraped URLs,
# 404 / mismatched pages removed by the loader). Not the consolidated all_features.parquet.
df, is_demo = load_features()

st.title("Where ING stands")
st.caption(
    f"How ING communicates to {AUDIENCE_TEXT} on its website, compared with four other "
    "Belgian banks — traditional banks and digital challengers."
)
if is_demo:
    st.warning("Showing **demo data** — `data/features/llm_claude.parquet` not found.", icon="⚠️")

mvp_df = filter_mvp(df).copy()
# load_features() doesn't derive bank_type, and deterministic values may arrive as strings.
if "bank_type" not in mvp_df.columns:
    mvp_df["bank_type"] = mvp_df["bank"].map(BANK_TYPE)
for _col in NUMERIC_FEATURES:
    if _col in mvp_df.columns:
        mvp_df[_col] = pd.to_numeric(mvp_df[_col], errors="coerce")
mvp_df["Bank type"] = mvp_df["bank_type"].map(BANK_TYPE_LABEL).fillna(mvp_df["bank_type"])
mvp_df["tone_score"] = mvp_df["tone"].map(TONE_SCORE)
mvp_df["clarity_score"] = mvp_df["value_proposition_clarity"].map(CLARITY_SCORE)

ing_df = mvp_df[mvp_df["bank"] == SUBJECT_BANK]
others_df = mvp_df[mvp_df["bank"] != SUBJECT_BANK]
if ing_df.empty or others_df.empty:
    st.error(f"Need pages for {SUBJECT_BANK} and at least one other MVP bank to compare.")
    st.stop()

n_by_bank = mvp_df.groupby("bank").size()
bank_order = [SUBJECT_BANK] + sorted(others_df["bank"].unique())
bank_colors = {
    b: ING_COLOR if b == SUBJECT_BANK else TYPE_COLORS.get(
        mvp_df.loc[mvp_df["bank"] == b, "Bank type"].iloc[0], GREY)
    for b in bank_order
}

rates = build_rates(mvp_df)
gaps = build_gaps(rates)

small = n_by_bank[n_by_bank < TARGET_RECORDS_PER_BANK]
if not small.empty:
    st.info(
        f"**Read with care — small samples.** {len(mvp_df)} pages in total; "
        + ", ".join(
            f"{b} ({n}{' — below the ' + str(MIN_VIABLE_RECORDS_PER_BANK) + '-page minimum' if n < MIN_VIABLE_RECORDS_PER_BANK else ''})"
            for b, n in small.items())
        + f" have fewer than the {TARGET_RECORDS_PER_BANK}-page target. "
        "Results show tendencies, not statistical proof.",
        icon="ℹ️",
    )

# ---------------------------------------------------------------------
# 1. Key message
# ---------------------------------------------------------------------
st.header("The key message")

leads = gaps[gaps["gap"] >= IN_LINE_THRESHOLD]
lags = gaps[gaps["gap"] <= -IN_LINE_THRESHOLD]
messages = []
if not leads.empty:
    top = leads.iloc[0]
    messages.append(
        f"✅ **Where ING stands out:** {top['label'].lower()} — "
        f"{top['ing']:.0f}% of ING pages vs {top['peer_median']:.0f}% for the median peer bank."
    )
if not lags.empty:
    low = lags.iloc[-1]
    messages.append(
        f"⚠️ **Where ING lags:** {low['label'].lower()} — "
        f"{low['ing']:.0f}% of ING pages vs {low['peer_median']:.0f}% for the median peer bank."
    )
if leads.empty and lags.empty:
    messages.append("ING is broadly in line with its peers on every measured criterion.")

challenger_tone = mvp_df.loc[mvp_df["Bank type"] == "Digital challenger", "tone_score"].mean()
ing_tone = ing_df["tone_score"].mean()
if pd.notna(challenger_tone) and pd.notna(ing_tone):
    diff = ing_tone - challenger_tone
    if diff <= -0.3:
        tone_msg = "more formal than the digital challengers"
    elif diff >= 0.3:
        tone_msg = "more expressive than the digital challengers"
    else:
        tone_msg = "close to the digital challengers"
    messages.append(f"🗣️ **Tone:** ING's youth pages are {tone_msg}.")

st.info("\n\n".join(messages))

cols = st.columns(len(HEADLINE_KEYS))
for col, key in zip(cols, HEADLINE_KEYS):
    row = gaps[gaps["key"] == key]
    if row.empty:
        continue
    r = row.iloc[0]
    # Custom card instead of st.metric: st.metric truncates long labels ("Clear, specific
    # value propo…"), this one wraps the title onto as many lines as it needs.
    col.markdown(
        f"""
<div style="border:1px solid rgba(128,128,128,.25); border-radius:10px; padding:14px 16px; height:100%;">
  <div style="font-size:.95rem; line-height:1.3; font-weight:600; min-height:2.6em;">{r['label']}</div>
  <div style="font-size:2rem; font-weight:700; line-height:1.2; margin-top:6px; color:{ING_COLOR};">{r['ing']:.0f}%</div>
  <div style="font-size:.85rem; opacity:.75;">{r['gap']:+.0f} pts vs peer median</div>
  <div style="font-size:.8rem; opacity:.6; margin-top:6px;">
    {r['ing_k']}/{r['ing_n']} ING pages · ranks {r['rank']}/{r['n_banks']}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
st.write("")
st.caption(
    f"Peer median = median of the {others_df['bank'].nunique()} other banks' rates "
    "(each bank counts once, whatever its number of pages)."
)

st.divider()

# ---------------------------------------------------------------------
# 2. Positioning map
# ---------------------------------------------------------------------
st.header("Where does ING sit on tone and clarity?")

pos = mvp_df.groupby("bank").agg(
    tone_score=("tone_score", "mean"),
    clarity_score=("clarity_score", "mean"),
    n_pages=("asset_id", "size"),
    bank_type=("Bank type", "first"),
).reset_index()
pos["Group"] = np.where(pos["bank"] == SUBJECT_BANK, SUBJECT_BANK, pos["bank_type"])

fig = px.scatter(
    pos, x="tone_score", y="clarity_score", size="n_pages", color="Group", text="bank",
    color_discrete_map=GROUP_COLORS, size_max=40,
    hover_data={"n_pages": True, "tone_score": ":.1f", "clarity_score": ":.0f", "Group": False},
    labels={"n_pages": "Pages", "tone_score": "Tone", "clarity_score": "Clarity"},
)
fig.update_traces(textposition="top center")
fig.add_vline(x=pos["tone_score"].mean(), line_dash="dot", line_color=GREY)
fig.add_hline(y=pos["clarity_score"].mean(), line_dash="dot", line_color=GREY)
fig.update_xaxes(
    range=[-0.4, 3.4], tickvals=[0, 1, 2, 3],
    ticktext=["Formal", "Simple", "Persuasive", "Playful"],
    title="Tone of the pages  (formal → expressive)",
)
fig.update_yaxes(
    range=[max(0, pos["clarity_score"].min() - 20), 108],
    title="Value proposition clarity  (0–100)",
)
fig.update_layout(height=470, legend_title=None)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "One bubble per bank; bubble size = number of pages analysed. Dotted lines = average of "
    "all banks. Top-right = clear and expressive. The tone axis is an ordinal encoding "
    "(formal 0 → playful 3) — see method notes at the bottom of the page."
)

st.divider()

# ---------------------------------------------------------------------
# 3. Leads and lags vs peers
# ---------------------------------------------------------------------
st.header("Where does ING lead — and lag — versus its peers?")
st.plotly_chart(dumbbell(gaps, rates), use_container_width=True)
st.caption(
    "Orange = ING · grey dots = each other bank · diamond = median of the other banks. "
    "Sorted by ING's gap to the median (biggest lead on top). Gaps under "
    f"{IN_LINE_THRESHOLD} pts are best read as “in line”."
)

st.divider()

# ---------------------------------------------------------------------
# 4. Traditional vs challengers
# ---------------------------------------------------------------------
st.header("Is it a traditional-vs-digital story?")

exclude_ing = st.toggle(
    f"Exclude {SUBJECT_BANK} from the traditional group (compare peers only)", value=False,
)
type_df = mvp_df[mvp_df["bank"] != SUBJECT_BANK] if exclude_ing else mvp_df

type_counts = type_df.groupby("Bank type")["bank"].agg(["nunique", "size"])
st.caption(
    " · ".join(f"**{t}**: {r['nunique']} banks, {r['size']} pages" for t, r in type_counts.iterrows())
    + ("" if exclude_ing else f" — {SUBJECT_BANK} counts as a traditional bank.")
)
if (type_counts["nunique"] < 3).any():
    st.warning(
        "One group has fewer than 3 banks — differences may reflect individual banks rather "
        "than a real traditional/digital pattern.", icon="⚠️",
    )

left, right = st.columns(2)
with left:
    st.subheader("Tone & style")
    type_feature = st.selectbox(
        "Feature", options=list(CATEGORICAL_FEATURES.keys()),
        format_func=lambda k: CATEGORICAL_FEATURES[k], key="type_feature",
    )
    stacked_share(type_df, "Bank type", type_feature, height=260)
with right:
    st.subheader("What each type shows on the page")
    rows = [
        {"Trait": c["label"], "Bank type": bank_type, "Share (%)": share(subset, c["col"], c["target"])}
        for c in CRITERIA.values() if c["col"] in type_df.columns
        for bank_type, subset in type_df.groupby("Bank type")
    ]
    if rows:
        grouped_bar(pd.DataFrame(rows), "Share (%)", "Trait", "Bank type", TYPE_COLORS, height=380)

st.divider()


# ---------------------------------------------------------------------
# Technical appendix
# ---------------------------------------------------------------------
with st.expander("For the technical team — coverage, method and validation"):
    t_cov, t_heat, t_dist, t_style, t_valid = st.tabs([
        "Coverage & method", "Bank × criterion", "Distributions by bank",
        "Writing style (provisional)", "LLM vs manual check",
    ])

    with t_cov:
        cov = pd.DataFrame({
            "Bank": n_by_bank.index,
            "Type": [mvp_df.loc[mvp_df["bank"] == b, "Bank type"].iloc[0] for b in n_by_bank.index],
            "Pages analysed": n_by_bank.values,
            "Status": ["✓ meets target" if n >= TARGET_RECORDS_PER_BANK
                       else "⚠ below target" if n >= MIN_VIABLE_RECORDS_PER_BANK
                       else "✗ below minimum" for n in n_by_bank.values],
        }).sort_values("Bank")
        st.dataframe(cov, hide_index=True, use_container_width=True)
        st.markdown(
            "- **Features**: interpretive features (tone, clarity, CTA…) are LLM-judged; "
            "word count, jargon density and sentence length are computed in Python.\n"
            "- **Pages**: 404 / error pages and confirmed content mismatches are removed upstream.\n"
            f"- **Peer comparison**: ING vs the median of the other banks' rates; "
            f"gaps under {IN_LINE_THRESHOLD} pts are treated as “in line”.\n"
            "- **Positioning map**: tone encoded formal 0 / simple 1 / persuasive 2 / playful 3 "
            "(a modelling choice — “simple” is not strictly between formal and persuasive); "
            "clarity encoded clear-specific 100 / clear-vague 50 / unclear 0; bank score = mean over pages.\n"
            f"- **Traditional vs challenger**: {SUBJECT_BANK} is counted as traditional unless excluded "
            "with the toggle."
        )

    with t_heat:
        ordered = list(gaps["label"])
        z = rates.pivot(index="label", columns="bank", values="rate").reindex(index=ordered, columns=bank_order)
        k = rates.pivot(index="label", columns="bank", values="k").reindex(index=ordered, columns=bank_order)
        n = rates.pivot(index="label", columns="bank", values="n").reindex(index=ordered, columns=bank_order)
        text = k.astype("Int64").astype(str) + "/" + n.astype("Int64").astype(str)
        text = z.round(0).astype(int).astype(str) + "%<br>" + text
        fig = go.Figure(go.Heatmap(
            z=z.values, x=[f"{b}<br>n={n_by_bank[b]}" for b in bank_order], y=ordered,
            text=text.values, texttemplate="%{text}", colorscale="Oranges",
            zmin=0, zmax=100, colorbar=dict(title="% of pages"),
            hovertemplate="%{y}<br>%{x}: %{z:.0f}%<extra></extra>",
        ))
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(side="top")
        fig.update_layout(height=130 + 62 * len(ordered))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Each cell: share of the bank's pages showing the trait, and the raw count k/n. ING first.")

    with t_dist:
        feat = st.selectbox(
            "Feature", options=list(CATEGORICAL_FEATURES.keys()),
            format_func=lambda k_: CATEGORICAL_FEATURES[k_], key="per_bank_feature",
        )
        stacked_share(mvp_df, "bank", feat, height=120 + 60 * len(bank_order), group_order=bank_order)

    with t_style:
        st.caption(
            "Computed deterministically (not LLM-judged) and pending team review — provisional. "
            "Very large word counts suggest that navigation/footer text may be included in some "
            "pages, so compare banks relatively, not in absolute terms."
        )
        avail = {k_: v for k_, v in NUMERIC_FEATURES.items() if k_ in mvp_df.columns}
        if not avail:
            st.info("No deterministic writing-style features found (`deterministic.parquet`).")
        else:
            metric_key = st.selectbox(
                "Metric", options=list(avail.keys()),
                format_func=lambda k_: avail[k_], key="numeric_feature",
            )
            plot_df = mvp_df.dropna(subset=[metric_key])
            fig = px.box(
                plot_df, x="bank", y=metric_key, color="bank", points="all",
                color_discrete_map=bank_colors, category_orders={"bank": bank_order},
            )
            fig.update_layout(xaxis_title=None, yaxis_title=avail[metric_key],
                              showlegend=False, height=420)
            st.plotly_chart(fig, use_container_width=True)

    with t_valid:
        st.caption(
            "How well do the LLM-judged features agree with human annotation on the "
            "analysis set (~50 pages)?"
        )
        manual_df, manual_is_demo = load_manual_annotations()
        if manual_is_demo or manual_df.empty:
            st.info(
                "No manual annotation data yet — this section populates once "
                "`data/features/visual_manual.csv` is available "
                "(columns: `asset_id`, `imagery_type`, `primary_cta_visible`, `price_in_viewport`)."
            )
        else:
            llm_cols = ["asset_id", "Bank type", "primary_cta_visibility", "price_in_initial_viewport"]
            joined = manual_df.merge(mvp_df[llm_cols], on="asset_id", how="inner")
            if joined.empty:
                st.info("The manual annotation file doesn't match any MVP page's asset_id yet.")
            else:
                pairs = [
                    ("primary_cta_visible", "primary_cta_visibility", "CTA visible without scrolling"),
                    ("price_in_viewport", "price_in_initial_viewport", "Price visible without scrolling"),
                ]
                out = []
                for manual_col, llm_col, label in pairs:
                    if manual_col not in joined.columns:
                        continue
                    sub = joined[[manual_col, llm_col]].dropna()
                    a = sub[manual_col].astype(str).str.lower().str.strip()
                    b = sub[llm_col].astype(str).str.lower().str.strip()
                    if a.empty:
                        continue
                    out.append({
                        "Feature": label, "Pages compared": len(sub),
                        "Agreement (%)": round((a == b).mean() * 100, 0),
                        "Cohen's kappa": round(cohen_kappa(a, b), 2),
                    })
                if out:
                    st.dataframe(pd.DataFrame(out), hide_index=True, use_container_width=True)
                    st.caption("Kappa above ~0.6 is usually read as substantial agreement; "
                               "with few pages, treat it as indicative.")

                if "imagery_type" in joined.columns:
                    st.markdown("**Imagery type by bank type (manual annotation)**")
                    fig = px.bar(
                        category_shares(with_n_labels(joined, "Bank type"), "Bank type", "imagery_type"),
                        x="Share (%)", y="Bank type", color="imagery_type",
                        orientation="h", barmode="stack",
                    )
                    fig.update_layout(yaxis_title=None, legend_title="Imagery type",
                                      height=260, xaxis_range=[0, 100])
                    st.plotly_chart(fig, use_container_width=True)