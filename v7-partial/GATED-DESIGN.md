# Length gate, long questions and two-question turns

2026-09-13, AI-authored. User requested length gating before Builder, longer questions and two questions spoken together. This is a separate successor replay; replay.py and its evidence remain unchanged.

The first gate counts English words in cumulative current text, ignoring punctuation. Default minimum: **3 words**, configurable with --minimum-words. This is an experimental default, not a calibrated optimum. No schema, LLM, embedding or cache access occurs for rejected partials. A reject is logged as `gated`, distinct from an LLM returning `wait`. Confirmed final text bypasses this speculative gate so short followups retain final processing. English tokenization is not a Chinese production policy.

Workload: 16 longest public questions (two per DB), eight synthetic turns joining two genuine same-DB questions, eight context/correction cases. Four snapshots each, 128 injections maximum. The prompt and 256-token output budget are unchanged, so this tests existing Builder behavior on expanded inputs without tuning toward the cases. Early input is built from an allowlist; expected full questions are scorer-only.

Compound snapshots: first word; complete first question; first question plus part of second; both complete. Check that the final normalized query preserves BOTH requests and that an early candidate for question one is not mistaken for coverage of the whole turn. This experiment deliberately retains the single-question-string output contract: it may express a compound request, but cannot independently schedule/retrieve two subqueries. Do not interpret valid JSON or one cache candidate as full coverage. An array of subqueries would require a separately recorded contract change if this test demonstrates the need.

Context cases repeat identical complete text as partial then final, allowing a preliminary final-flag comparison without punctuation changing. Single trials still include model variability. No real STT timing, saved latency or semantic hit rate is inferred.

Acceptance: short partials consume zero LLM calls; final bypass remains; real embeddings are scoped; every step including gate has elapsed_ms; failures and dropped compound intent are visible. Track gate rejection separately from LLM wait. Same previous evidence boundaries and CHARACTERIZATION/SPIKE apply. No SQL generation or automatic answer adoption.

Run replay_gated.py with the same arguments as replay.py and a new --output path. Compare gate thresholds offline on the fixed fixtures; do not manufacture counterfactual LLM outputs for gated snapshots. Full no-gate LLM A/B is not included in this budget.
