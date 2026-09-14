# Partial replay: first observed results

AI-authored, 2026-09-13. Run: [partial-20260913](evidence/partial-20260913/summary.json). Actual DeepSeek model `deepseek-v4-flash`; real local multilingual MiniLM ONNX embeddings. No mock LLM, hash similarity, SQL execution or automatic answer acceptance.

## Measurements

24 scenarios × 3 sequential text snapshots = **72 real LLM calls**, **0 HTTP/contract errors**, **15,976 reported tokens**. Token totals are not a dollar cost estimate. 16 public-data questions and eight synthetic context scenarios; not a representative accuracy benchmark.

| Step | Median | p95, nearest rank |
|---|---:|---:|
| Builder LLM | 988.18 ms | 1,467.52 ms |
| Query embedding | 7.19 ms | 16.39 ms |
| Scoped cosine search | 0.064 ms | 0.148 ms |
| Snapshot total (both diagnostic arms) | 1,005.05 ms | 1,473.55 ms |

One-time model load: 896.95 ms. Embedding 200 candidates: 5,142.16 ms. Cache contains 200 questions across eight DBs; each search considers only its own DB subset. These measurements are not Cloud SQL/Chroma network timings. FastEmbed 0.7.4 uses mean pooling for this model; do not compare with older CLS runs as though identical. Full package versions are in runtime-lock.txt.

| Stage | wait | search |
|---|---:|---:|
| First single-word snapshot | 24 | 0 |
| Intermediate snapshot | 20 | 4 |
| Complete text with final=true | 0 | 24 |

Only **4/48 non-final calls** produced a retrieval question. All 44 waits still incurred a remote call, using 9,459 reported tokens in aggregate. This supports prioritizing call scheduling, but does not establish which gate will work or its latency gain.

## Concrete observations

1. **Missing scope despite grammatical completion:** california_schools:82, intermediate `What is the grade span offered` became `What is the grade span offered?`. The later input identifies the school with the highest longitude. The early sentence lacks that identifying condition; a valid output contract does not establish query usefulness.
2. **Context resolution works in individual fixtures:** `And Batman?` after Abomination's superpower becomes `What is Batman's superpower?`; `And 2012?` carries the previous consumption metric and SME segment with the new year. This is observed behavior, not a general success rate.
3. **Important correction preserved, candidate unchanged:** synthetic:7 changes older-than-60 to younger-than-60. Builder preserves the correction, yet cache candidate 1171 remains top ranked and cosine rises **0.7024 → 0.7328**. Its actual question asks about under-age patients examined in 1990–1993, not either age-60 request. Stable candidate identity and rising score do not demonstrate applicability. These scores also do not disprove a separately calibrated high-threshold checker; none was tested.
4. **No demonstrated cache benefit on exact replays:** for the eight cached original questions at final input, raw and normalized search both retrieve the target at rank 1 (8/8). This is a sanity check, not semantic hit accuracy. The eight held-out questions have no hit labels and cannot support a cache-hit rate.
5. **Final flag/punctuation confound:** `And Batman` waits whereas `And Batman?` with final=true searches. Because both punctuation and the final flag change, this experiment cannot attribute the difference to either. Next testing should hold text fixed while changing final, rather than immediately tuning the prompt.

## Evidence and next decision

[All outputs](evidence/partial-20260913/output-review.md), [stage timings](evidence/partial-20260913/timing.jsonl), [analysis](evidence/partial-20260913/analysis.json), [frozen prompt and hashes](evidence/partial-20260913/manifest.json).

This completes the authorized first partial-injection smoke experiment. It does **not** establish voice latency savings, semantic cache acceptance accuracy, a useful threshold, or production readiness. Synthetic scenarios have been inspected by the assistant, not independently labeled. No model-based judge was used. Prompt remained fixed throughout the run. No additional LLM calls are scheduled.

Next useful experiments: isolate final-flag effects, then compare fewer Builder triggers under real STT timing. Preserve the direct full-STT cache path. Retrieved SQL examples and LiveKit preemptive generation remain separate pending branches. v6 stays unchanged. Code and documents are local working-tree additions; no commit or push was requested.
