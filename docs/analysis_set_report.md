# Analysis Set Build Report

**Input:** `D:/Irene/Desktop/AI_&_Data_Science_training_BeCode/BeCode_Projects/ing-use-case/data/features/deterministic.parquet`  
**Output:** `D:/Irene/Desktop/AI_&_Data_Science_training_BeCode/BeCode_Projects/ing-use-case/data/features/analysis_set_deterministic.parquet`  
**Cap per bank:** 10 youth records  
**Selection:** deterministic, stratified by language (round-robin)

## 1. Funnel

| Stage | Assets |
|---|---:|
| Full manifest (all assets) | 292 |
| MVP + youth only | 184 |
| Final analysis set | 35 |

## 2. Per-bank selection

| Bank | Available | Picked | Language split | Health |
|---|---:|---:|---|---|
| Belfius | 5 | 5 | fr: 1, nl: 4 | healthy |
| ING | 69 | 10 | en: 4, fr: 3, nl: 3 | healthy |
| KBC | 100 | 10 | en: 4, fr: 3, nl: 3 | healthy |
| N26 | 5 | 5 | en: 4, fr: 1 | healthy |
| Revolut | 5 | 5 | en: 2, fr: 1, nl: 2 | healthy |

## 3. Feature rows in output

| Feature | Rows |
|---|---:|
| jargon_density | 35 |
| mean_sentence_length | 35 |
| word_count | 35 |

## 4. Assets per bank × language in output

| Bank | Language | Assets |
|---|---|---:|
| Belfius | fr | 1 |
| Belfius | nl | 4 |
| ING | en | 4 |
| ING | fr | 3 |
| ING | nl | 3 |
| KBC | en | 4 |
| KBC | fr | 3 |
| KBC | nl | 3 |
| N26 | en | 4 |
| N26 | fr | 1 |
| Revolut | en | 2 |
| Revolut | fr | 1 |
| Revolut | nl | 2 |
