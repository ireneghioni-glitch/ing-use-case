import json
import os
import re

import pandas as pd
import streamlit as st
from utils.style import inject_css
from utils.config import SUBJECT_BANK, BANK_TYPE_LABEL, BANK_TYPE
from utils.data_loader import load_features, filter_mvp
from utils.style import inject_css
st.set_page_config(page_title="Why It Matters", page_icon="📚", layout="wide")
inject_css() 
st.title("Why It Matters")
st.caption(
    "Academic grounding for the patterns actually observed across the 5 MVP banks — "
    "combines the RAG's market research with your own measured data."
)

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data** for the observed patterns below.", icon="⚠️")


def _get_secret(key: str) -> str | None:
    try:
        value = st.secrets.get(key, os.environ.get(key))
    except Exception:
        value = os.environ.get(key)
    return value


@st.cache_resource
def get_rag_connection():
    """Lazily connects to the Supabase pgvector store used by build_rag.py.
    Returns None if SUPABASE_DB_URL isn't configured. Raises on an actual
    connection failure — cache_resource doesn't cache exceptions, so the
    real error is re-raised (and shown) on every retry rather than getting
    lost behind a generic 'not connected' message."""
    db_url = _get_secret("SUPABASE_DB_URL")
    if not db_url:
        return None

    import psycopg2
    from sentence_transformers import SentenceTransformer
    conn = psycopg2.connect(db_url)
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return conn, model


@st.cache_resource
def get_groq_client():
    """Optional: enables a synthesized, structured answer instead of raw chunks.
    Returns None if GROQ_API_KEY isn't configured — the page still works,
    just falls back to showing the retrieved passages directly."""
    api_key = _get_secret("GROQ_API_KEY")
    if not api_key:
        return None
    from groq import Groq
    return Groq(api_key=api_key)


def retrieve(question: str, top_k: int = 5, audience: str | None = None):
    resource = get_rag_connection()
    if resource is None:
        return None
    conn, model = resource

    query_emb = model.encode([question], normalize_embeddings=True)[0].tolist()
    cur = conn.cursor()
    if audience:
        cur.execute(
            """SELECT text, source, audience, embedding <=> %s::vector AS distance
               FROM rag_chunks WHERE audience = %s ORDER BY distance LIMIT %s""",
            (query_emb, audience, top_k),
        )
    else:
        cur.execute(
            """SELECT text, source, audience, embedding <=> %s::vector AS distance
               FROM rag_chunks ORDER BY distance LIMIT %s""",
            (query_emb, top_k),
        )
    results = cur.fetchall()
    cur.close()
    return results


@st.cache_data
def market_snapshot(_df: pd.DataFrame) -> dict:
    """A compact, factual summary of what was actually measured across the 5 MVP
    banks — by bank type, and for ING specifically. This is passed to the LLM as
    ground truth (not to be recomputed or contradicted), so the answer connects
    the academic 'why' to real numbers from this study rather than staying generic."""
    mvp_df = filter_mvp(_df)
    if mvp_df.empty:
        return {}

    def rate(sub_df: pd.DataFrame, col: str, value: str) -> float | None:
        if col not in sub_df.columns or sub_df.empty:
            return None
        return round((sub_df[col] == value).mean() * 100, 1)

    def top_category(sub_df: pd.DataFrame, col: str) -> dict:
        if col not in sub_df.columns or sub_df.empty:
            return {}
        return (sub_df[col].value_counts(normalize=True) * 100).round(1).to_dict()

    def avg(sub_df: pd.DataFrame, col: str):
        if col not in sub_df.columns or sub_df.empty or sub_df[col].isna().all():
            return None
        return round(sub_df[col].mean(), 1)

    def block(sub_df: pd.DataFrame) -> dict:
        return {
            "n_pages": int(len(sub_df)),
            "tone_distribution_pct": top_category(sub_df, "tone"),
            "price_visible_without_scrolling_pct": rate(sub_df, "price_in_initial_viewport", "yes"),
            "cta_visible_without_scrolling_pct": rate(sub_df, "primary_cta_visibility", "yes"),
            "names_audience_explicitly_pct": rate(sub_df, "audience_explicit", "yes"),
            "clear_specific_value_proposition_pct": rate(sub_df, "value_proposition_clarity", "clear-specific"),
            "avg_word_count": avg(sub_df, "word_count"),
            "avg_jargon_density_per_100_words": avg(sub_df, "jargon_density"),
            "avg_sentence_length_words": avg(sub_df, "mean_sentence_length"),
        }

    snapshot = {
        "pages_analyzed": int(len(mvp_df)),
        "banks": sorted(mvp_df["bank"].unique().tolist()),
        "by_bank_type": {},
        "ing": {},
    }
    for bank_type_key, label in BANK_TYPE_LABEL.items():
        sub = mvp_df[mvp_df["bank_type"] == bank_type_key]
        if not sub.empty:
            snapshot["by_bank_type"][label] = block(sub)

    ing_df = mvp_df[mvp_df["bank"] == SUBJECT_BANK]
    if not ing_df.empty:
        snapshot["ing"] = block(ing_df)

    return snapshot


def dominant(distribution: dict) -> str:
    if not distribution:
        return "—"
    return max(distribution, key=distribution.get)


def render_comparison(snapshot: dict):
    """Visual ING-vs-benchmark comparison, built directly from measured data
    (no LLM involved) — the numbers a business audience can trust at a glance."""
    ing = snapshot.get("ing")
    ing_type = BANK_TYPE_LABEL.get(BANK_TYPE.get(SUBJECT_BANK), "Traditional bank")
    benchmark_label = next((lbl for lbl in snapshot.get("by_bank_type", {}) if lbl != ing_type), None)
    benchmark = snapshot.get("by_bank_type", {}).get(benchmark_label) if benchmark_label else None

    if not ing or not benchmark:
        return

    st.subheader(f"{SUBJECT_BANK} vs {benchmark_label}")
    col_ing, col_benchmark = st.columns(2)

    with col_ing:
        st.markdown(f"**{SUBJECT_BANK}** ({ing['n_pages']} pages)")
        st.metric("Dominant tone", dominant(ing["tone_distribution_pct"]).title())
        st.metric("Price visible without scrolling", f"{ing['price_visible_without_scrolling_pct']}%")
        st.metric("CTA visible without scrolling", f"{ing['cta_visible_without_scrolling_pct']}%")
        st.metric("Names audience explicitly", f"{ing['names_audience_explicitly_pct']}%")
        st.metric("Clear, specific value proposition", f"{ing['clear_specific_value_proposition_pct']}%")
        if ing.get("avg_word_count"):
            st.metric("Avg. word count", ing["avg_word_count"])

    with col_benchmark:
        st.markdown(f"**{benchmark_label}** ({benchmark['n_pages']} pages)")

        def delta(ing_val, bench_val):
            if ing_val is None or bench_val is None:
                return None
            return round(ing_val - bench_val, 1)

        st.metric(
            "Dominant tone", dominant(benchmark["tone_distribution_pct"]).title(),
        )
        st.metric(
            "Price visible without scrolling", f"{benchmark['price_visible_without_scrolling_pct']}%",
            delta=delta(ing["price_visible_without_scrolling_pct"], benchmark["price_visible_without_scrolling_pct"]),
            delta_color="off",
        )
        st.metric(
            "CTA visible without scrolling", f"{benchmark['cta_visible_without_scrolling_pct']}%",
            delta=delta(ing["cta_visible_without_scrolling_pct"], benchmark["cta_visible_without_scrolling_pct"]),
            delta_color="off",
        )
        st.metric(
            "Names audience explicitly", f"{benchmark['names_audience_explicitly_pct']}%",
            delta=delta(ing["names_audience_explicitly_pct"], benchmark["names_audience_explicitly_pct"]),
            delta_color="off",
        )
        st.metric(
            "Clear, specific value proposition", f"{benchmark['clear_specific_value_proposition_pct']}%",
            delta=delta(ing["clear_specific_value_proposition_pct"], benchmark["clear_specific_value_proposition_pct"]),
            delta_color="off",
        )
        if benchmark.get("avg_word_count"):
            st.metric(
                "Avg. word count", benchmark["avg_word_count"],
                delta=delta(ing.get("avg_word_count"), benchmark.get("avg_word_count")),
                delta_color="off",
            )

    st.caption("Deltas on the right show ING minus the benchmark (informational, not colored good/bad).")


def _extract_json(raw: str) -> dict:
    stripped = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if match:
        stripped = match.group(1)
    return json.loads(stripped)


def synthesize_answer(question: str, chunks: list[tuple], snapshot: dict) -> dict | None:
    """Combines the RAG's academic passages with the study's own measured data
    into a structured, multi-part answer via Groq. Returns None if Groq isn't
    configured — caller falls back to raw chunks. Returns a dict with keys:
    headline, observation, why_it_matters, implication_for_ing."""
    client = get_groq_client()
    if client is None:
        return None

    context_block = "\n\n".join(
        f"[Source: {source}, audience: {audience}]\n{text}"
        for text, source, audience, _distance in chunks
    )
    snapshot_block = json.dumps(snapshot, ensure_ascii=False, indent=2) if snapshot else "(no data available)"

    prompt = f"""### Question
{question}

### Observed data — this study's own measurements across the 5 MVP banks
(treat as established fact: do not recompute, re-derive, or contradict these numbers)
{snapshot_block}

### Academic / market-research passages (external sources, for context only)
{context_block}

### Instructions
Write a structured answer for an ING business audience, grounded in BOTH sections
above. Return ONLY a JSON object with exactly these four keys:

- "headline": one short sentence stating the core finding (max 15 words).
- "observation": 2-3 sentences describing what the observed data actually shows,
  citing specific numbers, and naming {SUBJECT_BANK} explicitly where its figures
  differ from the benchmark bank type.
- "why_it_matters": 2-3 sentences explaining why this pattern matters, grounded
  in the academic passages. If the passages don't fully support the pattern, say
  so plainly rather than inventing a justification.
- "implication_for_ing": 1-2 sentences on what this pattern means specifically
  for {SUBJECT_BANK} — observational, not a prescriptive recommendation (that
  belongs elsewhere).

If the observed data and the academic passages disagree, say so explicitly in
"why_it_matters" rather than smoothing it over. No source names, no citations,
no markdown formatting inside the field values — plain business prose, no jargon.
Output raw JSON only, no markdown code fences, no text before or after."""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a marketing analyst writing short, structured, data-grounded answers for an ING business audience. You always respond with valid JSON matching the requested schema."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return _extract_json(completion.choices[0].message.content)


SUGGESTED_QUESTIONS = [
    "Why do digital challengers use a more playful tone with young audiences?",
    "Why does showing the price above the fold matter for youth acquisition?",
    "Why is gamification effective for engaging Gen Z with financial products?",
    "How important is naming the target audience explicitly in youth-oriented banking pages?",
]

question = st.selectbox(
    "Pick a pattern to explore, or write your own below",
    options=["(write my own)"] + SUGGESTED_QUESTIONS,
)
if question == "(write my own)":
    question = st.text_input("Your question")

audience_filter = st.radio("Audience filter (RAG only)", options=["genz", "adult", "no filter"], horizontal=True)
audience = None if audience_filter == "no filter" else audience_filter

if st.button("Get answer", type="primary", disabled=not question):
    connection_error = None
    try:
        resource = get_rag_connection()
    except Exception as e:
        resource = None
        connection_error = str(e)

    if connection_error:
        st.error(f"Connection error: {connection_error}")
    elif resource is None:
        st.info(
            "The RAG isn't connected in this environment. Add `SUPABASE_DB_URL` to "
            "`.streamlit/secrets.toml` to enable retrieval from the market-research corpus."
        )
    else:
        with st.spinner("Searching the market-research corpus..."):
            results = retrieve(question, audience=audience)

        if not results:
            st.info("No relevant passages found for this question.")
        else:
            snapshot = market_snapshot(df)

            render_comparison(snapshot)
            st.divider()

            answer = None
            try:
                with st.spinner("Writing a structured answer..."):
                    answer = synthesize_answer(question, results, snapshot)
            except Exception as e:
                st.warning(f"Couldn't generate a synthesized answer ({e}) — showing raw sources instead.")

            if answer:
                st.subheader(answer.get("headline", ""))
                st.markdown("**What we found**")
                st.write(answer.get("observation", ""))
                st.markdown("**Why it matters**")
                st.write(answer.get("why_it_matters", ""))
                st.markdown(f"**What this means for {SUBJECT_BANK}**")
                st.write(answer.get("implication_for_ing", ""))
            else:
                st.info(
                    "Showing raw retrieved passages — add `GROQ_API_KEY` to "
                    "`.streamlit/secrets.toml` for a structured, data-grounded answer instead."
                )

            with st.expander("Observed data used for this answer"):
                st.json(snapshot)

            with st.expander(f"Academic sources ({len(results)})" if answer else "Retrieved passages", expanded=not answer):
                for text, source, aud, distance in results:
                    st.markdown(f"**{source}** · *{aud}*")
                    st.caption(text[:600] + ("..." if len(text) > 600 else ""))
                    st.divider()