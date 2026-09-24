import streamlit as st

from utils.config import MVP_BANKS, BANK_TYPE
from utils.data_loader import load_features
from utils.style import inject_css 

st.set_page_config(page_title="Visual Comparator", page_icon="🖼️", layout="wide")
inject_css() 
st.title("Visual Comparator")
st.caption("Pick 2–3 banks and compare their youth-oriented pages side by side.")

df, is_demo = load_features()
if is_demo:
    st.warning("Showing **demo data** — screenshots aren't available in demo mode.", icon="⚠️")

available_banks = sorted(df["bank"].unique().tolist())
has_scope_role = "scope_role" in df.columns

SCOPE_BADGE = {"backup": " 🔁 backup bank", "out_of_scope": " ⛔ out of scope"}

selected_banks = st.multiselect(
    "Banks to compare",
    options=available_banks,
    default=[b for b in MVP_BANKS if b in available_banks][:3],
    max_selections=3,
)

if not selected_banks:
    st.info("Select at least one bank above.")
    st.stop()

KEY_FEATURES = ["tone", "value_proposition_clarity", "cta_clarity", "cta_text", "primary_cta_visibility"]

cols = st.columns(len(selected_banks))
for col, bank in zip(cols, selected_banks):
    with col:
        bank_pages = df[df["bank"] == bank]

        badge = ""
        if has_scope_role and not bank_pages.empty:
            role = bank_pages["scope_role"].iloc[0]
            badge = SCOPE_BADGE.get(role, "")

        st.subheader(f"{bank}{badge}")
        st.caption(BANK_TYPE.get(bank, "—").title())

        if bank_pages.empty:
            st.info("No pages for this bank yet.")
            continue

        page = bank_pages.sample(1, random_state=1).iloc[0]

        screenshot = page.get("screenshot_path")
        if screenshot and not is_demo:
            try:
                st.image(screenshot, use_container_width=True)
            except Exception:
                st.info("Screenshot not found on disk.")
        else:
            st.info("Screenshot preview unavailable in demo mode.")

        st.markdown(f"**URL:** {page.get('url', '—')}")
        for feature in KEY_FEATURES:
            value = page.get(feature, "—")
            st.markdown(f"**{feature.replace('_', ' ').title()}:** {value}")

st.divider()
st.caption(
    "One representative page per selected bank is shown. Use the "
    "Traditional vs Digital Challenger page for aggregate patterns across all pages."
)