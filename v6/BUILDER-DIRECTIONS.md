---
ai_contribution: authored
date: 2026-09-13
status: design-record-experiments-not-run
---

# Lightweight Builder and retrieved SQL examples

## Accepted architecture boundary

The user rejects SQL generation inside every partial Builder call. The proposed lightweight Builder receives cumulative partial text and necessary confirmed conversation context, then returns a natural-language retrieval question or wait. It does not receive detailed database schema or generate SQL. A separate SQL Generator receives the detailed schema when necessary. This is a proposed successor design; existing v6 still generates SQL in Builder and remains unchanged.

Builder-generated natural-language questions, rather than raw early partials, drive the proposed speculative QA search. Complete STT retains a direct cache-search path that need not await Builder. Retrieved candidates are not automatically reusable answers. Scope, conditions, context and freshness still matter; false acceptance is more costly than misses.

## Direction A: retrieved examples help SQL generation

When a cache answer cannot be reused, selected historical question + SQL examples may help the downstream SQL Generator. They are examples, not ground truth for the new question. This adds context to an already-needed SQL call, not an obligatory second lightweight Builder call.

Cheap first experiment: offline text questions and the existing real SQLite fixtures. Compare the same SQL Generator with schema only versus schema plus top-3 same-database question/SQL examples retrieved using real embedding cosine similarity. Do not use hash similarity. Exclude the evaluation item's own question/SQL from the example index. Freeze model, schema, hints policy and decoding settings; interleave arm order. Reference SQL is available only to the scorer, never retrieval selection or online prompts.

Use a small 16-question smoke run (two per database, 32 SQL calls, no retries) only to identify failures and cost. Expand a frozen evaluation set after the harness works; this smoke run cannot substantiate an accuracy improvement. The existing 200/146 split is an unlabeled candidate allocation, not proven cache hits/misses. Independently establish answer non-reusability before making cache-miss-specific claims.

Record embedding, search, SQL generation, validation and execution time separately, along with token usage, invalid SQL, result agreement and regressions. Correctness on one database snapshot is not universal semantic equivalence. Include failed and timed-out cases. Separate quality benefit from added retrieval latency. A local embedding model can cache all 200 candidate vectors; do not assume a runtime or weights are installed.

## Direction B: control speculative expensive work

Study whether candidate identity stability, similarity trajectory for the same candidate and changes in requested conditions help decide when to launch expensive SQL/RAG generation. Do not gate on average top-k similarity or treat high similarity as semantic completeness. Builder call frequency is itself a major cost. Observe signals before using them for control.

An isolated lightweight-Builder experiment should compare raw partial retrieval as a diagnostic baseline, Builder-normalized retrieval, and full-question retrieval as an end-of-turn reference. Full-question retrieval is not available early. Use real embeddings; separately score invented/missing conditions, wait decisions, correct candidate retrieval and false answer acceptance. Synthetic text prefixes must be labeled; they cannot establish actual voice latency. Do not send the full future question or benchmark evidence to a partial Builder.

## Local feasibility and limits

Existing complex-data contains 346 corrected questions/SQL across eight real databases and a 200-candidate split. v6 has a provider-injectable endpoint, per-call timing and an independent SQLite result scorer. No microphone, Docker, Jetson or LiveKit integration is required for the first quality comparison. Endpoint/model availability and embedding runtime have not been verified for this new experiment. No model calls have been made for it.

User confirmed the next experiment: lightweight natural-language Builder with partial injection followed by embedding cache search. Implementation and results live in ../v7-partial/. Retrieved SQL example generation remains parked. Mandatory LiveKit preemptive-generation testing in NEXT-VERSION.md remains required and is not replaced by either offline experiment.

## Handoff and evidence boundary

Reuse v6/vibe-discipline/index.md and its existing design/learning records. This document records accepted responsibilities and proposed experiments, not a newly implemented feature or demonstrated learner mastery. Before implementation, resolve the selected experiment and carry its concrete contracts into the existing delivery workflow. No previous evidence is overwritten; no new empirical benefit is claimed.
