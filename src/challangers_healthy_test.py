import polars as pl
from src.config import PROCESSED_DIR

CLEANED_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"
df = pl.read_ndjson(CLEANED_PATH).select(["asset_id", "bank", "text"])

for bank in ["N26", "Revolut"]:
    print(f"\n=== {bank} ===")
    bank_df = df.filter(pl.col("bank") == bank)
    print(f"Total: {len(bank_df)}")

    for row in bank_df.iter_rows(named=True):
        text = (row["text"] or "").lower()
        words = len(text.split())
        matches = [p for p in ["page not found", "pagina niet gevonden",
                                "pagina niet beschikbaar", "page non trouvée",
                                "page introuvable", "404"] if p in text]
        status = "❌ 404" if matches else ("⚠️ short" if words < 100 else "✅ ok")
        print(f"  {row['asset_id'][:60]:60} | {words:5}w | {status} {matches}")