# Data Audit — `campaign_asset.jsonl`

**Total records:** 35


## 1. Conformance to schema

**Required fields (from AssetMetadata):** asset_id, bank, bank_type, channel, audience_label, url, language, collected_at, raw_html_path


### Missing fields

| Field | Missing / Total |
|-------|-----------------|
| `asset_id` | 35 / 35 |
| `bank_type` | 35 / 35 |
| `channel` | 35 / 35 |
| `audience_label` | 35 / 35 |
| `language` | 35 / 35 |
| `collected_at` | 35 / 35 |
| `raw_html_path` | 35 / 35 |

### Validation errors

**35 records failed Pydantic validation.**

First 5 errors:

- `[record 0]` https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes
  - `('asset_id',)`: Field required
  - `('bank_type',)`: Field required
- `[record 1]` https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/comptes-bancaires/compte-a-vue/compte-jeune
  - `('asset_id',)`: Field required
  - `('bank_type',)`: Field required
- `[record 2]` https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/jeune-travailleur
  - `('asset_id',)`: Field required
  - `('bank_type',)`: Field required
- `[record 3]` https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/jeune-travailleur/premier-logement
  - `('asset_id',)`: Field required
  - `('bank_type',)`: Field required
- `[record 4]` https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/argent-de-poche
  - `('asset_id',)`: Field required
  - `('bank_type',)`: Field required

## 2. Coverage by bank

| Bank | Records |
|------|---------|
| bnp_fortis | 9 |
| ing | 6 |
| kbc | 7 |
| belfius | 3 |
| revolut | 5 |
| ing_adult | 5 |

## 3. Screenshots

- Present: **35**
- Missing: **0**
- No path: **0**


## 4. Role coverage

| Bank | Roles |
|------|-------|
| bnp_fortis | UNKNOWN: 9 |
| ing | UNKNOWN: 6 |
| kbc | UNKNOWN: 7 |
| belfius | UNKNOWN: 3 |
| revolut | UNKNOWN: 5 |
| ing_adult | UNKNOWN: 5 |