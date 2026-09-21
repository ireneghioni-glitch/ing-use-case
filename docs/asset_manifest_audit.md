# Processed Asset Manifest Audit

**Input:** `data/processed/asset_manifest.jsonl`  
**Records:** 54  
**Status:** **PASS WITH WARNINGS**  
**Critical findings:** 0  
**Warnings:** 4

## Coverage by bank

| Bank | Records |
|---|---:|
| BNP Paribas Fortis | 9 |
| Belfius | 3 |
| ING | 22 |
| KBC | 7 |
| Revolut | 13 |

## Coverage by language

| Language | Records |
|---|---:|
| en | 2 |
| fr | 52 |

## Coverage by audience

| Audience | Records |
|---|---:|
| general_adult | 6 |
| youth_18_25 | 48 |

## Audience coverage by bank

| Bank | Youth 18-25 | General adult | Other/missing |
|---|---:|---:|---:|
| BNP Paribas Fortis | 9 | 0 | 0 |
| Belfius | 3 | 0 | 0 |
| ING | 16 | 6 | 0 |
| KBC | 7 | 0 | 0 |
| Revolut | 13 | 0 | 0 |

## Recommended MVP scope

| Bank | Records |
|---|---:|
| ING | 22 |
| KBC | 7 |
| Revolut | 13 |

## JSON parsing

No JSON parsing errors.

## Schema conformance

All records conform to `AssetMetadata`.

## Critical artifact problems

No critical artifact problems.

## Duplicates and shared content

- Shared HTML path `data/raw/revolut_revolut-kids-and-teens-benefits.html` on lines [38, 39].
- Identical HTML content for assets: revolut__revolut-kids-and-teens-benefits__en__1ca08dc936, revolut__revolut-kids-and-teens-benefits__fr__ce4736177c.

## Warnings

- Shared HTML paths: 1 group(s)
- Identical HTML content: 1 group(s)
- MVP bank KBC has no general_adult assets; within-bank youth/adult comparison is incomplete
- MVP bank Revolut has no general_adult assets; within-bank youth/adult comparison is incomplete
