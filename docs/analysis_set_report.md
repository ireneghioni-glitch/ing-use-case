# Analysis Set Build Report

**Input:** `D:/Irene/Desktop/AI_&_Data_Science_training_BeCode/BeCode_Projects/ing-use-case/data/features/deterministic.parquet`  
**Output:** `D:/Irene/Desktop/AI_&_Data_Science_training_BeCode/BeCode_Projects/ing-use-case/data/features/analysis_set.parquet`  
**Cap per bank:** 10 youth records  
**Selection:** deterministic, stratified by language (round-robin)

## 1. Funnel

| Stage | Assets |
|---|---:|
| Full manifest (all assets) | 292 |
| MVP + youth only | 206 |
| Final analysis set | 45 |

## 2. Per-bank selection

| Bank | Available | Picked | Language split |
|---|---:|---:|---|
| Belfius | 21 | 10 | en: 1, fr: 5, nl: 4 |
| ING | 69 | 10 | en: 4, fr: 3, nl: 3 |
| KBC | 101 | 10 | en: 4, fr: 3, nl: 3 |
| N26 | 10 | 10 | en: 9, fr: 1 |
| Revolut | 5 | 5 | en: 2, fr: 1, nl: 2 |

## 3. Feature rows in output

| Feature | Rows |
|---|---:|
| jargon_density | 45 |
| mean_sentence_length | 45 |
| word_count | 45 |

## 4. Assets per bank × language in output

| Bank | Language | Assets |
|---|---|---:|
| Belfius | en | 1 |
| Belfius | fr | 5 |
| Belfius | nl | 4 |
| ING | en | 4 |
| ING | fr | 3 |
| ING | nl | 3 |
| KBC | en | 4 |
| KBC | fr | 3 |
| KBC | nl | 3 |
| N26 | en | 9 |
| N26 | fr | 1 |
| Revolut | en | 2 |
| Revolut | fr | 1 |
| Revolut | nl | 2 |
