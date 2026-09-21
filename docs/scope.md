## Final scope — 2026-09-21

**Banks in the MVP (5 total):**
- **ING** — subject of the study
- **KBC** — traditional competitor
- **Belfius** — traditional competitor
- **Revolut** — digital challenger
- **N26** — digital challenger

**Comparison design:**
- **Primary:** cross-bank comparison of youth-oriented pages (ING vs KBC vs Belfius vs Revolut vs N26).
- **Within-bank comparison (youth vs adult):** excluded from the MVP by team decision on 2026-09-21.

**Rationale for excluding within-bank comparison:**
- The team decided to focus the POC exclusively on youth-oriented communication.
- Consequence acknowledged: the POC describes communication patterns on youth pages, but does not compare them to the same banks' general-audience communication. It therefore cannot isolate which observed patterns are youth-specific adaptations versus brand-wide choices.

**Depth rule:**
- Target: 10 youth records per bank.
- Minimum viable: 5 youth records per bank (below 5, patterns are anecdotal).
- Total MVP target: 5 banks × 10 = 50 youth records.

**Coverage acceptance criterion:**
- Each MVP bank must have ≥5 `youth_18_25` records in the manifest.
- If a bank fails this threshold, either:
  - (a) activate a **backup bank** from the appropriate category (see below), or
  - (b) document the shortfall as an acknowledged limitation in the final report.

**Backup banks (configured, activated only if an MVP bank fails coverage):**

| Category | Backup bank | Activates if… |
|----------|-------------|---------------|
| **Traditional** | BNP Paribas Fortis | KBC or Belfius falls below 5 youth records |
| **Digital** | bunq | Revolut or N26 falls below 5 youth records |

*Status note (2026-09-21):* BNP Paribas Fortis has already been scraped as part of an earlier iteration (9 records currently in the manifest). It remains designated as a backup and is not part of the MVP five. If coverage of KBC or Belfius fails, BNP is ready to promote into the MVP without re-scraping.

**Out of scope (acknowledged):**
- Within-bank youth vs adult comparison (removed 2026-09-21).
- Conversion, ROI, or sales impact measurement (no internal data available).
- Ad-platform analysis (website-only MVP).
- Additional challengers considered but not retained: Hello bank! (hybrid, not a pure challenger — kept as a future extension), Nickel, Santander Openbank, Trade Republic.