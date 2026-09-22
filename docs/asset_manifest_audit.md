# Processed Asset Manifest Audit

**Scope:** youth-only MVP, 5 banks, backups configured (2026-09-21).

**Input:** `data/processed/asset_manifest.jsonl`  
**Records:** 58  
**Status:** **PASS WITH WARNINGS**  
**Critical findings:** 0  
**Warnings:** 3

## Coverage by bank

| Bank | Records |
|---|---:|
| Belfius | 3 |
| ING | 22 |
| KBC | 7 |
| N26 | 13 |
| Revolut | 13 |

## Coverage by language

| Language | Records |
|---|---:|
| en | 1 |
| fr | 57 |

## Coverage by audience

| Audience | Records |
|---|---:|
| general_adult | 6 |
| youth_18_25 | 52 |

## Coverage by bank and audience

| Bank | Youth 18-25 | General adult | Other/missing | MVP? |
|---|---:|---:|---:|:---:|
| Belfius | 3 | 0 | 0 | yes |
| ING | 16 | 6 | 0 | yes |
| KBC | 7 | 0 | 0 | yes |
| N26 | 13 | 0 | 0 | yes |
| Revolut | 13 | 0 | 0 | yes |

## Records per MVP bank

| Bank | Records |
|---|---:|
| Belfius | 3 |
| ING | 22 |
| KBC | 7 |
| N26 | 13 |
| Revolut | 13 |

## JSON parsing

No JSON parsing errors.

## Schema conformance

All records conform to `AssetMetadata`.

## Critical artifact problems

No critical artifact problems.

## Duplicates and shared content

- Shared HTML path `data/raw/revolut_revolut-kids-and-teens-benefits.html` on lines [38, 39].
- Identical HTML content for assets: revolut__referrals__fr__bda1fece32, revolut__kids-savings-account__fr__8acfca6ef6.
- Identical HTML content for assets: revolut__revolut-kids-and-teens-benefits__en__1ca08dc936, revolut__revolut-kids-and-teens-benefits__fr__ce4736177c.

## Warnings

- Shared HTML paths: 1 group(s)
- Identical HTML content: 2 group(s)
- MVP bank Belfius has only 3 youth records (need 5); consider activating a backup bank (BNP Paribas Fortis for traditional, bunq for neo).
