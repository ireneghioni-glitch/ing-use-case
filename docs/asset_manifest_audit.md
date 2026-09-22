# Processed Asset Manifest Audit

**Scope:** youth-only MVP, 5 banks, backups configured (2026-09-21).

**Input:** `data/processed/asset_manifest.jsonl`  
**Records:** 292  
**Status:** **PASS WITH WARNINGS**  
**Critical findings:** 0  
**Warnings:** 3

## Coverage by bank

| Bank | Records |
|---|---:|
| Argenta | 21 |
| BNP Paribas Fortis | 44 |
| Belfius | 21 |
| Beobank | 13 |
| ING | 69 |
| KBC | 101 |
| N26 | 10 |
| Revolut | 5 |
| bunq | 8 |

## Coverage by language

| Language | Records |
|---|---:|
| en | 45 |
| fr | 133 |
| nl | 114 |

## Coverage by audience

| Audience | Records |
|---|---:|
| youth_18_25 | 292 |

## Coverage by bank and audience

| Bank | Youth 18-25 | General adult | Other/missing | MVP? |
|---|---:|---:|---:|:---:|
| Argenta | 21 | 0 | 0 | backup |
| BNP Paribas Fortis | 44 | 0 | 0 | backup |
| Belfius | 21 | 0 | 0 | yes |
| Beobank | 13 | 0 | 0 | backup |
| ING | 69 | 0 | 0 | yes |
| KBC | 101 | 0 | 0 | yes |
| N26 | 10 | 0 | 0 | yes |
| Revolut | 5 | 0 | 0 | yes |
| bunq | 8 | 0 | 0 | backup |

## Records per MVP bank

| Bank | Records |
|---|---:|
| Belfius | 21 |
| ING | 69 |
| KBC | 101 |
| N26 | 10 |
| Revolut | 5 |

## JSON parsing

No JSON parsing errors.

## Schema conformance

All records conform to `AssetMetadata`.

## Critical artifact problems

No critical artifact problems.

## Duplicates and shared content

- Shared HTML path `data/raw/ing_youth-turning-18.html` on lines [18, 48].
- Shared HTML path `data/raw/kbc_job-d-etudiant-compte-a-vue-html.html` on lines [71, 138].
- Shared HTML path `data/raw/kbc_jongeren-zijn-de-influencers-van-de-beleggende-generaties-html.html` on lines [79, 164].
- Shared HTML path `data/raw/kbc_jongeren-html.html` on lines [82, 120].
- Shared HTML path `data/raw/kbc_digitaal-html.html` on lines [84, 127].
- Shared HTML path `data/raw/kbc_du-kot-a-l-opportunite-investir-dans-le-logement-etudiant-html.html` on lines [153, 160].
- Shared HTML path `data/raw/kbc_een-studentenkamer-voor-uw-kind-investering-of-emotionele-keuze-html.html` on lines [158, 161].
- Shared HTML path `data/raw/belfius_index-aspx.html` on lines [171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189].
- Shared HTML path `data/raw/revolut_revolut-junior.html` on lines [193, 194].
- Shared HTML path `data/raw/argenta_de-jongh-gits-bv-3136-html.html` on lines [198, 209].
- Shared HTML path `data/raw/argenta_de-jongh-gits-bv-3728-html.html` on lines [199, 210].
- Shared HTML path `data/raw/bnp_fortis_hello4you.html` on lines [254, 290].
- Shared HTML path `data/raw/bnp_fortis_student.html` on lines [256, 288].
- Identical HTML content for assets: ing__youth-turning-18__en__98560fa85b, ing__youth-turning-18__fr__92321d3632.
- Identical HTML content for assets: kbc__job-d-etudiant-compte-a-vue__fr__124714f4d2, kbc__job-d-etudiant-compte-a-vue__fr__e6dbb17142.
- Identical HTML content for assets: kbc__jongeren-zijn-de-influencers-van-de-beleggende-generaties__nl__9bd8728037, kbc__jongeren-zijn-de-influencers-van-de-beleggende-generaties__fr__6609cb7e08.
- Identical HTML content for assets: kbc__jongeren__nl__4c539f0278, kbc__jongeren__nl__7da169afba.
- Identical HTML content for assets: kbc__digitaal__nl__6ece647612, kbc__digitaal__fr__fc97c9cf1a.
- Identical HTML content for assets: kbc__du-kot-a-l-opportunite-investir-dans-le-logement-etudiant__fr__7b67ff6bbb, kbc__du-kot-a-l-opportunite-investir-dans-le-logement-etudiant__fr__9b6fb314bc.
- Identical HTML content for assets: kbc__een-studentenkamer-voor-uw-kind-investering-of-emotionele-keuze__fr__f77e61856b, kbc__een-studentenkamer-voor-uw-kind-investering-of-emotionele-keuze__nl__b955e4251e.
- Identical HTML content for assets: belfius__index__nl__edea673d2c, belfius__index__fr__e7fecb8cf9, belfius__index__fr__4f3f8932fd, belfius__index__fr__4290b60945, belfius__index__fr__440fcf618f, belfius__index__fr__fd5987fc27, belfius__index__fr__83f7302b82, belfius__index__fr__63bc8066bc, belfius__index__nl__82d24d183c, belfius__index__nl__a46cceef97, belfius__index__en__e02ac2a7b7, belfius__index__nl__93cab218c7, belfius__index__nl__4bd9ae02f7, belfius__index__nl__bac2ff92e4, belfius__index__nl__e1b37d6814, belfius__index__nl__d8a6e3b460, belfius__index__nl__c89232c14a, belfius__index__nl__2eb73bd97b, belfius__index__nl__adcec3cf50.
- Identical HTML content for assets: revolut__revolut-junior__fr__88ba5a908e, revolut__revolut-junior__nl__373f39897d.
- Identical HTML content for assets: argenta__de-jongh-gits-bv-3136__fr__8452abc664, argenta__de-jongh-gits-bv-3136__nl__e4eaa2a966.
- Identical HTML content for assets: argenta__de-jongh-gits-bv-3728__fr__e1dd00c370, argenta__de-jongh-gits-bv-3728__nl__7552a3e0be.
- Identical HTML content for assets: bnp-paribas-fortis__hello4you__en__a5d165c0b3, bnp-paribas-fortis__hello4you__nl__5eabd1dd5c.
- Identical HTML content for assets: bnp-paribas-fortis__student__en__7ca0e36644, bnp-paribas-fortis__student__nl__27aa3c903c.

## Warnings

- Shared HTML paths: 13 group(s)
- Identical HTML content: 13 group(s)
- Banks found in manifest but not declared in scope: Argenta, Beobank
