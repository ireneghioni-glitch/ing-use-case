"""
Data loading for the ING Youth Acquisition Communication Comparator.

Reads the real pipeline outputs when present:
  - data/features/llm_claude.parquet — LLM-derived interpretive features (wide format)
  - data/features/deterministic.parquet — Python/HTML-computed features (LONG format:
    one row per asset_id x feature_name, pivoted to wide here before use)
  - data/processed/cleaned_assets.jsonl — cleaned text + screenshot paths
  - data/features/visual_manual.csv — manual visual annotation subset

If a file is missing — e.g. while building/demoing the app before the full
pipeline has run — falls back to a small generated demo dataset with the same
shape, clearly flagged in the UI so it's never mistaken for real results.

scope_role (present in deterministic.parquet, and merged into the combined
dataframe) is the pipeline's own authoritative in/out-of-scope call for each
asset — 'mvp', 'backup', or 'out_of_scope' — reflecting scope.md's backup-bank
activation rules as already resolved upstream. Prefer filtering on this column
over the static MVP_BANKS list wherever it's available.
"""

import json
import random
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import (
    FEATURES_PATH,
    DETERMINISTIC_FEATURES_PATH,
    CLEANED_ASSETS_PATH,
    MANUAL_ANNOTATIONS_PATH,
    MVP_BANKS,
    BACKUP_BANKS,
    BANK_TYPE,
    AUDIENCE_LABEL,
    TARGET_RECORDS_PER_BANK,
    MIN_VIABLE_RECORDS_PER_BANK,
    SUBJECT_BANK,
)

FEATURE_COLUMNS = [
    "value_proposition_clarity", "trust_signals", "tone", "sentiment", "verbosity",
    "cta_clarity", "cta_text", "distinctiveness", "visual_hierarchy_focus",
    "text_image_layout", "color_touch_location", "animation_level", "visual_type",
    "mobile_first_cues", "topics", "main_benefit", "audience_explicit",
    "conditional_price_disclosure", "eligibility_stated", "opening_guidance",
    "support_options", "persuasive_framing", "price_in_initial_viewport",
    "primary_cta_visibility",
]

# Identifying columns that may appear in deterministic.parquet's long format
# alongside asset_id — kept once per asset (not treated as pivoted features).
_DETERMINISTIC_ID_COLUMNS = ["bank", "audience_label", "language", "scope_role", "asset_role"]


def _demo_dataframe() -> pd.DataFrame:
    """A small, clearly-labeled placeholder dataset — same shape as the real
    pipeline output — so every page renders sensibly before real data lands."""
    random.seed(42)
    tones = ["formal", "persuasive", "simple", "playful"]
    sentiments = ["positive", "neutral", "reassuring", "urgent"]
    clarity = ["clear-specific", "clear-vague", "unclear"]
    cta_clarity = ["specific-action", "vague-action", "none"]
    verbosity = ["low", "medium", "high"]
    yes_no = ["yes", "no"]
    trust_options = ["security_badge", "deposit_guarantee", "testimonials", "customer_numbers", "none"]
    topic_pool = [
        "student account", "savings", "youth", "budgeting", "gamification",
        "mobile banking", "investing", "eligibility", "free account",
    ]
    # Guarantee at least one shared topic between ING and another bank, on
    # each bank's first page — otherwise random sampling could produce a
    # demo where no two banks ever share a topic, making the "Product /
    # topic" filter on the Visual Comparator look broken even when it isn't.
    SHARED_TOPIC = "student account"
    SHARED_TOPIC_PARTNER = next((b for b in MVP_BANKS if b != SUBJECT_BANK), None)

    def pick_topics(bank: str, page_index: int) -> list[str]:
        sampled = random.sample(topic_pool, k=random.randint(2, 3))
        must_share = page_index == 0 and bank in (SUBJECT_BANK, SHARED_TOPIC_PARTNER)
        if must_share and SHARED_TOPIC not in sampled:
            sampled = [SHARED_TOPIC] + sampled[:2]
        return sampled

    rows = []
    for bank in MVP_BANKS:
        bank_type = BANK_TYPE[bank]
        # Reflect the real corpus's borderline case (Revolut at the 5-record
        # minimum, not the 10-record target) so the coverage page has
        # something realistic to flag even in demo mode.
        n = 5 if bank == "Revolut" else 10
        for i in range(n):
            is_challenger = bank_type == "digital challenger"
            rows.append({
                "asset_id": f"{bank.lower().replace(' ', '-')}__demo-{i}",
                "bank": bank,
                "bank_type": bank_type,
                "audience_label": AUDIENCE_LABEL,
                "scope_role": "mvp",
                "url": f"https://example.com/{bank.lower()}/youth-page-{i}",
                "language": random.choice(["en", "fr", "nl"]),
                "tone": random.choices(
                    tones, weights=[1, 2, 2, 4] if is_challenger else [4, 3, 2, 1]
                )[0],
                "sentiment": random.choice(sentiments),
                "value_proposition_clarity": random.choices(clarity, weights=[6, 3, 1])[0],
                "cta_clarity": random.choices(cta_clarity, weights=[6, 3, 1])[0],
                "cta_text": random.choice(["Open your account", "Get started", "Learn more", "Sign up"]),
                "verbosity": random.choices(
                    verbosity, weights=[3, 4, 3] if is_challenger else [1, 4, 5]
                )[0],
                "distinctiveness": random.choices(["high", "medium", "low"], weights=[3, 5, 2])[0],
                "trust_signals": random.sample(trust_options, k=random.randint(1, 2)),
                "audience_explicit": random.choices(yes_no, weights=[7, 3])[0],
                "eligibility_stated": random.choices(yes_no, weights=[7, 3])[0],
                "price_in_initial_viewport": random.choices(
                    yes_no, weights=[6, 4] if is_challenger else [3, 7]
                )[0],
                "primary_cta_visibility": random.choices(yes_no, weights=[7, 3])[0],
                "main_benefit": random.choice([
                    "affordability", "convenience", "independence-control",
                    "security-support", "lifestyle-rewards",
                ]),
                "word_count": random.randint(80, 900),
                "jargon_density": round(random.uniform(0.5, 6.0), 2),
                "mean_sentence_length": round(random.uniform(8, 35), 1),
                "topics": pick_topics(bank, i),
                "screenshot_path": None,
                "text": "[Demo placeholder — real cleaned page text will appear here once the pipeline output is loaded.]",
                "_is_demo_data": True,
            })
    return pd.DataFrame(rows)


def _load_deterministic_wide() -> pd.DataFrame | None:
    """Pivots deterministic.parquet from its long format (asset_id, feature_name,
    value) into one row per asset_id with one column per feature_name — plus
    the per-asset identifying columns (bank, scope_role, etc.) carried along.
    Returns None if the file doesn't exist. New feature_names your colleagues
    add later (cta_count, dominant_color, conditions_link...) appear
    automatically — no code change needed here."""
    if not DETERMINISTIC_FEATURES_PATH.exists():
        return None

    long_df = pd.read_parquet(DETERMINISTIC_FEATURES_PATH)

    # Values arrive as strings — cast numeric-looking ones to float, keep the
    # rest (e.g. a future 'yes'/'no' or a hex color) as-is. (errors="ignore"
    # on pd.to_numeric is deprecated, hence the explicit per-value cast.)
    def _try_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    long_df["value"] = long_df["value"].apply(_try_float)

    wide = long_df.pivot_table(
        index="asset_id", columns="feature_name", values="value", aggfunc="first"
    ).reset_index()

    id_cols = [c for c in _DETERMINISTIC_ID_COLUMNS if c in long_df.columns]
    ids = long_df[["asset_id"] + id_cols].drop_duplicates("asset_id")
    wide = wide.merge(ids, on="asset_id", how="left")

    return wide


def deterministic_review_summary() -> dict | None:
    """How much of the deterministic feature set has actually been reviewed
    yet — surfaced on the Scope & Methodology page so provisional data is
    never presented as if it were finalized."""
    if not DETERMINISTIC_FEATURES_PATH.exists():
        return None
    long_df = pd.read_parquet(DETERMINISTIC_FEATURES_PATH)
    if "review_status" not in long_df.columns:
        return None
    counts = long_df["review_status"].value_counts(dropna=False).to_dict()
    total = len(long_df)
    reviewed = counts.get("reviewed", 0) + counts.get("approved", 0)
    return {
        "total_values": total,
        "by_status": {str(k): int(v) for k, v in counts.items()},
        "reviewed_share_pct": round(reviewed / total * 100, 1) if total else 0,
    }


@st.cache_data
def load_features() -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_demo_data)."""
    if FEATURES_PATH.exists():
        df = pd.read_parquet(FEATURES_PATH)
        df["_is_demo_data"] = False

        if CLEANED_ASSETS_PATH.exists():
            with CLEANED_ASSETS_PATH.open(encoding="utf-8") as f:
                cleaned = [json.loads(line) for line in f]
            cleaned_df = pd.DataFrame(cleaned)
            keep_cols = [c for c in ["asset_id", "text", "screenshot_path", "title"] if c in cleaned_df.columns]
            cleaned_df = cleaned_df[keep_cols]
            df = df.merge(cleaned_df, on="asset_id", how="left")

        det_wide = _load_deterministic_wide()
        if det_wide is not None:
            # Don't duplicate identifying columns already present in df (e.g.
            # 'bank') — but DO bring in scope_role/asset_role even if df
            # already has some overlapping id columns, since those are the
            # authoritative scope call this whole app should defer to.
            overlap = [
                c for c in det_wide.columns
                if c in df.columns and c not in ("asset_id", "scope_role", "asset_role")
            ]
            det_wide = det_wide.drop(columns=overlap)
            df = df.merge(det_wide, on="asset_id", how="left")

        df = _drop_404_pages(df)

        return df, False

    return _demo_dataframe(), True


def _is_404_topics(topics) -> bool:
    """Flags a page whose LLM-extracted topics indicate it's actually a 404 /
    error page rather than real content — confirmed in this corpus: several
    pages (16 for Belfius, 5 for N26, 1 each for KBC/BNP) were scraped as
    generic error pages, which also explains why some pages showed identical
    word_count/jargon_density/sentence_length values despite different URLs."""
    if hasattr(topics, "tolist"):
        topics = topics.tolist()
    if not topics:
        return False
    markers = ("404", "error page", "page not found")
    return any(any(m in str(t).lower() for m in markers) for t in topics)


# "Back to homepage" CTA text in the languages this corpus uses — catches 404
# pages whose topics list came back empty (so _is_404_topics alone misses them),
# e.g. belfius__index__nl__a46cceef97 (studentenkrediet-lening).
_HOMEPAGE_CTA_MARKERS = (
    "terug naar de homepagina", "retourner à la page d'accueil",
    "retour à l'accueil", "back to homepage", "go to homepage",
)


def _is_404_cta(topics, cta_text) -> bool:
    has_topics = bool(topics.tolist() if hasattr(topics, "tolist") else topics)
    if has_topics:
        return False  # only use this signal when topics came back empty
    cta = str(cta_text or "").strip().lower()
    return any(m in cta for m in _HOMEPAGE_CTA_MARKERS)


# Known cases our automatic heuristics can't catch generically — each is a
# confirmed content-integrity issue found by manually inspecting the scraped
# text, not just a guess. Document the reason so this list stays auditable.
MANUALLY_EXCLUDED_ASSET_IDS = {
    "belfius__index__nl__edea673d2c": (
        "URL is the 'Blue' account page, but the scraped text is actually the "
        "'Beats New' account page (mentions 'Beats New' 7x, 'blue' 0x) — a "
        "content/URL mismatch, likely the same SPA client-side-routing issue "
        "scraper.py's own comments already flagged as a known risk (confirmed "
        "happening for KBC)."
    ),
    "belfius__index__nl__82d24d183c": (
        "https://www.belfius.be/retail/nl/producten/betalen/zichtrekeningen/"
        "beats-new/index.aspx — confirmed bad by direct user check. Not caught "
        "by the automatic heuristics: the extracted text/topics/CTA looked "
        "internally coherent (real 'Beats New' content, no 404 markers), so "
        "whatever's wrong with this page isn't visible in the LLM-extracted "
        "fields alone."
    ),
}


def _drop_404_pages(df: pd.DataFrame) -> pd.DataFrame:
    if "topics" not in df.columns:
        return df

    is_topics_404 = df["topics"].apply(_is_404_topics)
    is_cta_404 = df.apply(lambda r: _is_404_cta(r.get("topics"), r.get("cta_text")), axis=1) \
        if "cta_text" in df.columns else False
    is_manual = df["asset_id"].isin(MANUALLY_EXCLUDED_ASSET_IDS)

    drop_mask = is_topics_404 | is_cta_404 | is_manual
    n_dropped = int(drop_mask.sum())
    if n_dropped:
        print(f"[data_loader] Dropped {n_dropped} page(s): "
              f"{int(is_topics_404.sum())} via topics, "
              f"{int((is_cta_404 & ~is_topics_404).sum()) if hasattr(is_cta_404, 'sum') else 0} via empty-topics+homepage-CTA, "
              f"{int(is_manual.sum())} manually confirmed content mismatches.")
    return df[~drop_mask].reset_index(drop=True)


@st.cache_data
def load_manual_annotations() -> tuple[pd.DataFrame, bool]:
    if MANUAL_ANNOTATIONS_PATH.exists():
        return pd.read_csv(MANUAL_ANNOTATIONS_PATH), False
    return pd.DataFrame(columns=["asset_id", "imagery_type", "primary_cta_visible", "price_in_viewport"]), True


def filter_mvp(df: pd.DataFrame) -> pd.DataFrame:
    """The in-scope subset for cross-bank comparison pages. Prefers the
    pipeline's own scope_role == 'mvp' when available (this already reflects
    any backup-bank activation) — falls back to the static MVP_BANKS list
    (e.g. in demo mode, or if deterministic.parquet hasn't been merged yet)."""
    if "scope_role" in df.columns and df["scope_role"].notna().any():
        return df[df["scope_role"] == "mvp"]
    return df[df["bank"].isin(MVP_BANKS)]


def compute_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Per-bank youth-record counts against the scope's target (10) and
    minimum-viable (5) thresholds, and which backup bank (if any) is
    configured to activate. Uses scope_role for the actual in-scope set
    when available, so a bank promoted from backup shows up correctly."""
    in_scope = filter_mvp(df)
    youth = in_scope[in_scope["audience_label"] == AUDIENCE_LABEL]
    counts = youth.groupby("bank").size().to_dict()

    banks_to_show = sorted(set(MVP_BANKS) | set(counts.keys()))

    rows = []
    for bank in banks_to_show:
        n = counts.get(bank, 0)
        meets_minimum = n >= MIN_VIABLE_RECORDS_PER_BANK
        meets_target = n >= TARGET_RECORDS_PER_BANK
        if not meets_minimum:
            status = "✗ below minimum"
        elif not meets_target:
            status = "⚠ at minimum, below target"
        else:
            status = "✓ meets target"

        backup = None
        if not meets_minimum:
            for info in BACKUP_BANKS.values():
                if bank in info["activates_if"]:
                    backup = info["bank"]

        rows.append({
            "Bank": bank,
            "Type": BANK_TYPE.get(bank, "—").title(),
            "Youth records": n,
            "Status": status,            
        })
    return pd.DataFrame(rows)


def scope_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Every bank actually present in the corpus, with its resolved
    scope_role — makes visible which banks are in the MVP, held as backup,
    or out of scope entirely (e.g. Argenta, Beobank from an earlier
    scraping iteration)."""
    if "scope_role" not in df.columns:
        return pd.DataFrame(columns=["Bank", "Scope role", "Pages"])
    per_asset = df.drop_duplicates("asset_id")
    counts = per_asset.groupby(["bank", "scope_role"]).size().reset_index(name="Pages")
    counts.columns = ["Bank", "Scope role", "Pages"]
    return counts.sort_values(["Scope role", "Bank"])