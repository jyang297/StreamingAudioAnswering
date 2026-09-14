# Length-gated long/compound replay results

2026-09-13, AI-authored. [Design](GATED-DESIGN.md). Prior runner and evidence remain unchanged. New evidence: [summary](evidence/gated-long-compound-20260913/summary.json), [all outputs](evidence/gated-long-compound-20260913/output-review.md), [timings](evidence/gated-long-compound-20260913/timing.jsonl).

## What ran

32 scenarios, four cumulative snapshots each: 16 public questions of 22–44 words, eight synthetic turns combining two real same-database questions, eight context/correction scenarios. Real DeepSeek and the same real embedding model; fixed original Builder prompt. Three-word gate before both LLM and diagnostic embedding paths, with final bypass. No SQL generation or automatic answer adoption.

128 injections: **36 locally gated**, **92 actual LLM calls**, **36 LLM waits**, **56 searches**, **0 HTTP/contract errors**. Reported tokens: **22,068**. All 36 gated records have neither LLM usage nor embedding search. Six local boundary tests pass. Relative to sending all 128 selected snapshots, the gate avoids 36 calls (28.1%); their counterfactual LLM responses and token costs were not measured.

Gate median **0.013 ms**, p95 **0.080 ms**. LLM median **790.31 ms**, p95 **1,110.81 ms**. Query embedding median **14.55 ms**, p95 **51.55 ms**. Mixed snapshot latency includes skipped stages and both diagnostic arms; it is not a production speedup metric. Endpoint timing differs from the first run; workloads and timing changed, so do not attribute the difference to the gate.

| Snapshot | Locally gated | LLM wait | LLM search |
|---|---:|---:|---:|
| First word | 32 | 0 | 0 |
| Intermediate 1 | 2 | 15 | 15 |
| Intermediate 2 | 2 | 21 | 9 |
| Final | 0 | 0 | 32 |

## Findings

**The length gate performs the intended cheap rejection.** All first-word snapshots avoid remote calls. It also blocks `And Batman?` and `And 2012?` as partials; final bypass preserves processing. That is an explicit tradeoff, not evidence that short followups lack meaning. Three words is not an optimized threshold. Offline counting on these same fixtures yields 36/39/43/45 rejected snapshots at minimum lengths 3/4/5/6; this does not measure correctness under alternative thresholds.

**Longer text alone does not ensure useful early generation.** Of 32 non-final long-question snapshots passing the gate, 27 produce LLM wait and five produce a query. The remaining 16 non-final long snapshots are first-word gate rejects. Some queries are plausible current intents but may lose later constraints. No real speaking timeline was used, so available overlap remains unknown.

**Two questions expose a premature relationship.** In compound:california_schools, first question asks which state special schools have most K-12 enrollees. The partial second question is `What is the grade span offered`. Builder merges it into `what grade span do they offer?`, binding the second question to the first question's schools. Later speech specifies the school with the highest longitude. The full output then preserves the independent school criterion. Early grammatical completion invented a relationship not yet established by the user.

**Full compound outputs retain both visible requests in these eight inspected cases**, but this is an assistant inspection, not independently adjudicated semantic accuracy. They remain one combined query string and one embedding search; the system does not independently retrieve or track coverage for the two questions.

**A complete first question can be lost behind a waiting second question.** Seven of eight compound intermediate-2 snapshots return wait although the first question is complete; the eighth is the school relationship case above. The stateless single-result contract cannot represent `first subquestion ready, second subquestion pending`. No runtime candidate eviction occurred here because the runner does not manage in-flight tasks; this is an output-contract limitation, not a measured scheduler bug.

## Next design decision

Keep the cheap configurable gate. Consider a separate Builder contract with multiple subquestions and readiness per subquestion if the product should retain useful work for a complete first question while the second is incomplete. Full-turn applicability must verify coverage of all requested subquestions before adopting an answer. This change is proposed, not implemented. Do not fix compound inputs by claiming the first cache candidate answers everything.

No extra model calls are pending. No voice speedup, cache accuracy or company compatibility is claimed. Changes are local working-tree additions; no commit/push. Original first-run evidence is preserved.
