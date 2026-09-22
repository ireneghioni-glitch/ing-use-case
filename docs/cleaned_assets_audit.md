# Cleaned Assets Audit

**Input:** `D:/Irene/Desktop/AI_&_Data_Science_training_BeCode/BeCode_Projects/ing-use-case/data/processed/cleaned_assets.jsonl`  
**Records:** 58  
**Status:** **PASS**  
**Critical findings:** 0

## 1. Required fields

| Field | Missing / Total |
|---|---:|
| `asset_id` | 0 / 58 |
| `bank` | 0 / 58 |
| `audience_label` | 0 / 58 |
| `language` | 0 / 58 |
| `text` | 0 / 58 |
| `cleaning_status` | 0 / 58 |

## 2. JSON parsing

No parse errors.

## 3. Cleaning status

| cleaning_status | Records |
|---|---:|
| insufficient_text | 2 |
| ok | 56 |

## 4. Language

| language | Records |
|---|---:|
| en | 1 |
| fr | 57 |

## 5. Bank

| bank | Records |
|---|---:|
| Belfius | 3 |
| ING | 22 |
| KBC | 7 |
| N26 | 13 |
| Revolut | 13 |

## 6. Duplicate asset_id

No duplicate asset_id values.

## 7. Short texts (< 50 words)

| asset_id | word_count |
|---|---:|
| `revolut__referrals__fr__bda1fece32` | 34 |
| `revolut__kids-savings-account__fr__8acfca6ef6` | 34 |
