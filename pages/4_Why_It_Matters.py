import json
import os
import re

import pandas as pd
import streamlit as st

from utils.config import SUBJECT_BANK, BANK_TYPE_LABEL
from utils.data_loader import load_features, filter_mvp

st.set_page_config(page_title="Why It Matters", page_icon="📚", layout="wide")

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
    """Lazily connects to the Supabase pgvector store used by build_rag_multilingual.py.
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
    # Multilingual model — replaces bge-small-en-v1.5, which silently
    # under-retrieved non-English sources (confirmed: the French banking
    # report never surfaced with the old model, appears reliably with this one).
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    return conn, model


RAG_TABLE = "rag_chunks_multilingual"  # matches build_rag_multilingual.py's output table


@st.cache_resource
def get_claude_client():
    """Optional: enables a synthesized, structured answer instead of raw chunks.
    Returns None if ANTHROPIC_API_KEY isn't configured — the page still works,
    just falls back to showing the retrieved passages directly."""
    api_key = _get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


# Cosine distance above this is treated as "not actually relevant". Recalibrated
# for paraphrase-multilingual-mpnet-base-v2 (the old 0.35 threshold was tuned for
# bge-small-en-v1.5 and silently rejected almost everything from this model,
# whose distances run structurally higher). Based on two calibration points on
# this corpus: a known-relevant chunk (gamification/neobanks) landed at 0.559,
# a genuinely unrelated test question's closest match landed at 0.672 — 0.60
# sits between them with margin toward not losing relevant results. Only two
# data points so far — revisit if you see clearly irrelevant sources slipping
# through, or relevant ones still getting cut.
RELEVANCE_DISTANCE_THRESHOLD = 0.60

# No single source document should dominate the citations — some PDFs have far
# more chunks than others (e.g. one guide has 112 vs. another's 6), so a plain
# top-k by distance can return 4-5 chunks from the same document even when
# other sources are also relevant. Fetch a wider pool, then cap how many
# chunks any one source contributes.
CANDIDATE_POOL_SIZE = 25
MAX_CHUNKS_PER_SOURCE = 3

MAX_WORDS_PER_CHUNK = 250  # each chunk can be up to 400 words — trimming cuts
# prompt size substantially (this is what pushed a request over Groq's
# free-tier TPM limit once) while keeping the key evidence, which is
# typically front-loaded in these chunks. Shared with the ungrounded-name
# check below, so that check validates against exactly what the LLM saw.


def _trim(text: str, max_words: int = MAX_WORDS_PER_CHUNK) -> str:
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words]) + "..."


def retrieve(question: str, top_k: int = 8, audience: str | None = None):
    resource = get_rag_connection()
    if resource is None:
        return None
    conn, model = resource

    query_emb = model.encode([question], normalize_embeddings=True)[0].tolist()
    cur = conn.cursor()
    if audience:
        cur.execute(
            f"""SELECT text, source, audience, embedding <=> %s::vector AS distance
               FROM {RAG_TABLE} WHERE audience = %s ORDER BY distance LIMIT %s""",
            (query_emb, audience, CANDIDATE_POOL_SIZE),
        )
    else:
        cur.execute(
            f"""SELECT text, source, audience, embedding <=> %s::vector AS distance
               FROM {RAG_TABLE} ORDER BY distance LIMIT %s""",
            (query_emb, CANDIDATE_POOL_SIZE),
        )
    candidates = cur.fetchall()
    cur.close()

    # Drop chunks too far from the query to be genuinely relevant, rather than
    # always forcing top_k regardless of actual relevance (the LLM can't tell
    # relevant from irrelevant context as reliably as this hard cutoff can).
    candidates = [r for r in candidates if r[3] <= RELEVANCE_DISTANCE_THRESHOLD]

    # Walk candidates in distance order (closest first), taking each one
    # unless its source has already hit the per-source cap — this keeps the
    # best matches while preventing one document from crowding out the rest.
    per_source_count: dict[str, int] = {}
    diversified = []
    for r in candidates:
        source = r[1]
        if per_source_count.get(source, 0) >= MAX_CHUNKS_PER_SOURCE:
            continue
        diversified.append(r)
        per_source_count[source] = per_source_count.get(source, 0) + 1
        if len(diversified) >= top_k:
            break

    return diversified


@st.cache_data
def market_snapshot(_df: pd.DataFrame) -> dict:
    """A compact, factual summary of what was actually measured across the 5 MVP
    banks — by bank type, and for ING specifically. This is passed to the LLM as
    ground truth (not to be recomputed or contradicted), so the answer connects
    the academic 'why' to real numbers from this study rather than staying generic."""
    mvp_df = filter_mvp(_df)
    if mvp_df.empty:
        return {}

    def rate(sub_df: pd.DataFrame, col: str, value: str) -> dict | None:
        """Returns both the percentage and the raw count/total — the LLM should
        never have to back-calculate a page count from a percentage itself
        (arithmetic it can get subtly wrong); hand it the exact numbers."""
        if col not in sub_df.columns or sub_df.empty:
            return None
        n_total = len(sub_df)
        n_match = int((sub_df[col] == value).sum())
        return {"pct": round(n_match / n_total * 100, 1), "count": n_match, "of": n_total}

    def top_category(sub_df: pd.DataFrame, col: str) -> dict:
        if col not in sub_df.columns or sub_df.empty:
            return {}
        n_total = len(sub_df)
        counts = sub_df[col].value_counts()
        return {
            k: {"pct": round(v / n_total * 100, 1), "count": int(v), "of": n_total}
            for k, v in counts.items()
        }

    def _as_list(value):
        """Parquet round-trips list columns (trust_signals, support_options) as
        numpy arrays, not plain Python lists — handle both."""
        if isinstance(value, (list, tuple)):
            return list(value)
        if hasattr(value, "tolist"):
            return value.tolist()
        return None

    def list_field_breakdown(sub_df: pd.DataFrame, col: str) -> dict:
        """For list-valued fields (a page can have several trust signals, several
        support channels) — the share of pages containing each distinct value."""
        if col not in sub_df.columns or sub_df.empty:
            return {}
        n_total = len(sub_df)
        counts: dict[str, int] = {}
        for v in sub_df[col].dropna():
            lst = _as_list(v) or []
            for item in lst:
                if item and item != "none":
                    counts[item] = counts.get(item, 0) + 1
        return {
            k: {"pct": round(v / n_total * 100, 1), "count": v, "of": n_total}
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
        }

    def avg(sub_df: pd.DataFrame, col: str):
        if col not in sub_df.columns or sub_df.empty or sub_df[col].isna().all():
            return None
        return round(sub_df[col].mean(), 1)

    def block(sub_df: pd.DataFrame) -> dict:
        return {
            "n_pages": int(len(sub_df)),
            "tone_distribution": top_category(sub_df, "tone"),
            "price_visible_without_scrolling": rate(sub_df, "price_in_initial_viewport", "yes"),
            "cta_visible_without_scrolling": rate(sub_df, "primary_cta_visibility", "yes"),
            "names_audience_explicitly": rate(sub_df, "audience_explicit", "yes"),
            "clear_specific_value_proposition": rate(sub_df, "value_proposition_clarity", "clear-specific"),
            "trust_signals_present": list_field_breakdown(sub_df, "trust_signals"),
            "main_benefit_distribution": top_category(sub_df, "main_benefit"),
            "eligibility_stated": rate(sub_df, "eligibility_stated", "yes"),
            "support_options_offered": list_field_breakdown(sub_df, "support_options"),
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
        # Exclude ING from its own bank_type's aggregate — otherwise "Traditional
        # bank" would include ING's own pages, comparing ING against itself
        # (consistent with how the Positioning page computes its benchmark).
        sub = mvp_df[(mvp_df["bank_type"] == bank_type_key) & (mvp_df["bank"] != SUBJECT_BANK)]
        if not sub.empty:
            snapshot["by_bank_type"][label] = block(sub)

    ing_df = mvp_df[mvp_df["bank"] == SUBJECT_BANK]
    if not ing_df.empty:
        snapshot["ing"] = block(ing_df)

    return snapshot





def _find_ungrounded_names(answer: dict, source_text: str) -> list[str]:
    """Safety net against a specific failure mode we've seen: naming a
    real-sounding brand/company not actually in the retrieved passages.
    Extracts capitalized words that appear MID-SENTENCE (not sentence-initial
    — any English word is capitalized there by grammar convention, which is
    why a growing blocklist of common words was never going to keep up) and
    flags any that don't appear in the source text actually sent to the LLM."""
    text = " ".join(answer.get(k, "") for k in ("observation", "why_it_matters", "implication_for_ing"))

    # App/domain terms that are legitimately capitalized and would otherwise
    # false-positive even under the mid-sentence check (they're expected
    # vocabulary, not brand names drawn from outside the sources).
    KNOWN_TERMS = {
        "ING", "Gen", "Belfius", "KBC", "N26", "Revolut", "BNP", "Traditional",
        "Digital", "Challenger", "Xaalys", "Osper", "Vybe", "Greenlight", "MVP",
    }

    sentences = re.split(r"(?<=[.!?])\s+", text)
    candidates = set()
    for sentence in sentences:
        words = sentence.split()
        for word in words[1:]:  # skip the sentence-initial word
            no_possessive = re.sub(r"[’']s$", "", word)  # "Vybe's" -> "Vybe",
            # not "Vybes" — strip the possessive suffix before stripping the
            # apostrophe itself, or the two merge into a word that matches
            # neither the known term nor the source text.
            cleaned = re.sub(r"[^a-zA-Z]", "", no_possessive)
            if re.match(r"^[A-Z][a-zA-Z]{2,}$", cleaned):
                candidates.add(cleaned)

    candidates -= KNOWN_TERMS
    source_lower = source_text.lower()
    return sorted(c for c in candidates if c.lower() not in source_lower)


def _get_response_text(message) -> str:
    """Find the text content block, skipping any thinking/redacted_thinking
    blocks — content[0] isn't reliably the text block once thinking is
    involved (bit us once before in claude_extract_features.py)."""
    for block in message.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError(f"No text block found in message content: {message.content}")


def _extract_json(raw: str) -> dict:
    stripped = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if match:
        stripped = match.group(1)
    return json.loads(stripped)


def synthesize_answer(question: str, chunks: list[tuple], snapshot: dict) -> dict | None:
    """Combines the RAG's academic passages with the study's own measured data
    into a structured, multi-part answer via Claude. Returns None if Claude isn't
    configured — caller falls back to raw chunks. Returns a dict with keys:
    headline, observation, why_it_matters, implication_for_ing."""
    client = get_claude_client()
    if client is None:
        return None

    context_block = "\n\n".join(
        f"[Source: {source}, audience: {audience}]\n{_trim(text)}"
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
First check: does the question ask about something this study actually measured?
This study covers ONLY youth-oriented pages (audience 18-25) across 5 banks — it
does NOT compare youth pages to adult/general-audience pages at the same bank
(that comparison was explicitly out of scope). If the question asks for something
outside what's in the "Observed data" section above (e.g. a youth-vs-adult
comparison, a bank or metric not covered), say so explicitly as the first
sentence of "observation" — do not silently substitute a different, adjacent
question and answer that instead without disclosing the substitution.

Word choice — this matters: every field in "Observed data" is a communication
DESIGN trait (tone, layout, wording), judged by an LLM or computed from page
text — none of it measures actual user behavior. This study has no clicks, time
on page, conversion, or engagement data. Never use words like "engagement",
"conversion", "performance", or "resonates with users" as if they were measured
— they weren't. Say "the page is designed to..." or "this trait is associated
with...", not "this drives engagement" or "this converts better".

Sample size — it's handed to you directly, use it as-is: every rate and
category in "Observed data" is given as {{"pct": ..., "count": ..., "of": ...}}
— read "count" and "of" directly rather than calculating a page count from the
percentage yourself (don't do that arithmetic; just quote the numbers given).
Whenever "of" is under 30, mention the fraction (e.g. "6.7% — 1 of 15 pages")
so the reader isn't misled by false precision, and use hedged language ("may
suggest" rather than "shows") for small-sample findings.

Relevance check — if the retrieved academic passages aren't topically related
to the question, say so plainly in "why_it_matters" rather than forcing a
connection. Do not stretch an unrelated passage to sound relevant.

Data quality caveat — general rule: any avg_* or rate figure computed from a
small or unreviewed sample may be unreliable — in particular, the Digital
challenger group's averages currently include at least one known data-quality
issue (some pages show identical, likely-erroneous values) and all
Python-computed fields (avg_word_count, avg_jargon_density_per_100_words,
avg_sentence_length_words) are still pending team review. If your answer
leans on any of these three fields for the Digital challenger group, add one
caveat sentence noting the figure is provisional — in "why_it_matters" if you
use the field there, otherwise in "observation".

Use concrete evidence, not generic paraphrase: when a retrieved passage names
specific examples — a company, tool, feature, or named mechanism (e.g. "Xaalys'
gamified simulator" rather than just "gamification") — use that specific detail
in "why_it_matters" instead of restating the passage's general idea. A named,
concrete example is far more convincing to a business audience than a vague
academic claim, and you should never write a generic summary when a specific
one is available in the passages you were given.

Otherwise, write a structured answer for an ING business audience, grounded in
BOTH sections above. Return ONLY a JSON object with exactly these four keys:

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

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,  # headroom for the 4-field JSON response
        thinking={"type": "disabled"},  # not needed for this task, and extended
        # thinking silently ate the whole max_tokens budget once before (see
        # claude_extract_features.py's history) — disable it explicitly.
        system="You are a marketing analyst writing short, structured, data-grounded answers for an ING business audience. You always respond with valid JSON matching the requested schema. You are careful about small sample sizes and never let a precise-looking percentage imply more certainty than the underlying page count supports.",
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(_get_response_text(message))


SUGGESTED_QUESTIONS = [
    "Why do digital challengers use a more playful tone with young audiences?",
    "Why does showing the price above the fold matter for youth acquisition?",
    "Why is gamification effective for engaging Gen Z with financial products?",
    "How important is naming the target audience explicitly in youth-oriented banking pages?",
]

question = st.selectbox(
    "Ask a question",
    options=SUGGESTED_QUESTIONS,
    index=None,
    placeholder="Pick a suggested question, or type your own...",
    accept_new_options=True,
)

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

            answer = None
            try:
                with st.spinner("Writing a structured answer..."):
                    answer = synthesize_answer(question, results, snapshot)
            except Exception as e:
                st.warning(f"Couldn't generate a synthesized answer ({e}) — showing raw sources instead.")

            REQUIRED_KEYS = {"headline", "observation", "why_it_matters", "implication_for_ing"}
            if answer and not REQUIRED_KEYS.issubset(answer):
                missing = REQUIRED_KEYS - set(answer)
                st.warning(f"The model's answer was missing expected field(s) ({', '.join(missing)}) — showing raw sources instead.")
                answer = None

            if answer:
                source_text = " ".join(_trim(text) for text, *_ in results)
                ungrounded = _find_ungrounded_names(answer, source_text)
                if ungrounded:
                    st.warning(
                        f"⚠️ This answer names {', '.join(ungrounded)}, which "
                        f"doesn't appear in the retrieved sources below — it may "
                        f"be drawn from the model's general knowledge rather than "
                        f"this study's corpus. Verify before using."
                    )

                st.subheader(answer.get("headline", ""))
                st.markdown("**What we found**")
                st.write(answer.get("observation", ""))
                st.markdown("**Why it matters**")
                st.write(answer.get("why_it_matters", ""))
                st.markdown(f"**What this means for {SUBJECT_BANK}**")
                st.write(answer.get("implication_for_ing", ""))
            else:
                st.info(
                    "Showing raw retrieved passages — add `ANTHROPIC_API_KEY` to "
                    "`.streamlit/secrets.toml` for a structured, data-grounded answer instead."
                )

            with st.expander("Observed data used for this answer"):
                st.json(snapshot)

            with st.expander(f"Academic sources ({len(results)})" if answer else "Retrieved passages", expanded=not answer):
                for text, source, aud, distance in results:
                    st.markdown(f"**{source}** · *{aud}*")
                    st.caption(text[:600] + ("..." if len(text) > 600 else ""))
                    st.divider()