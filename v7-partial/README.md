# Lightweight Builder partial replay

**Current continuation entry (2026-09-14): [experiment summary and company handoff](HANDOFF.md).**

AI-authored experiment, 2026-09-13. User approved: lightweight natural-language Builder, then embedding search; no SQL in Builder. v6 remains unchanged. This is a CHARACTERIZATION/SPIKE, not a production integration.

## Frozen design

- Builder receives only cumulative current text, confirmed conversation history, and whether this is the final replay snapshot. No DB schema, cache questions, reference SQL, benchmark evidence or future question enters its prompt.
- Output is exactly `{action: search, question: nonempty string}` or `{action: wait, question: null}`. A search is a hypothesis, not permission to reuse an answer.
- Same-database cosine search uses the existing pinned multilingual MiniLM ONNX embedding model. No hash or lexical fallback. Index contains 200 public candidate questions; SQL remains in the source fixture but is not needed by this experiment.
- Compare raw snapshot retrieval with normalized retrieval; full-question retrieval is an end-of-turn reference, never early input.
- 16 deterministic public source questions (one cache replay and one held-out question per DB), plus eight explicitly synthetic contextual followups/late corrections. Three snapshots each, 72 calls maximum, 256 output tokens, no retries. Fixed prompt; do not tune it against results in this run.
- Sequential replay tests content only. It does not simulate speech arrival or concurrency and cannot measure saved voice latency. Cheap scheduling is deferred; currently every selected snapshot calls Builder, including meaningless prefixes to observe wait behavior.
- Log model load, index embedding, each query embedding, cosine search, Builder call and total stage time. Persist every response and failure incrementally. No SQL execution, answer generation or auto-acceptance.

## Evaluation boundaries

Exact cache replays are retrieval sanity checks, not semantic paraphrase accuracy. Held-out records have no answer-hit label. Synthetic context cases are AI-authored diagnostic fixtures. Final-reference candidate agreement is not correctness. Similarity trajectories never authorize answers. Review normalized questions for invented/missing entities, dates, negation and metrics; no automated judge claims semantic correctness.

## Run

Install `requirements.txt` in an isolated environment. Supply the existing v4 `.env` explicitly with `--env-file` (loaded by the client; never printed). Process environment takes precedence. Existing DeepSeek defaults match v4; overrides use `RAG_LLM_BASE_URL`, `RAG_LLM_MODEL`, `RAG_LLM_API_KEY_ENV`, `RAG_LLM_THINKING`. Do not commit credentials.

`python replay.py --data-root ../complex-data --model-path /path/to/pinned/onnx/snapshot --env-file /path/to/v4/.env --output evidence/run-name`

Output directories must be new. The embedding model revision is `faf4aa4225822f3bc6376869cb1164e8e3feedd0` of `qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q`. Existing local model files are used without downloads. Model weights and environment are not copied into Git.

## Design and learning handoff

This reopens only the Builder responsibility branch from ../v6/BUILDER-DIRECTIONS.md. READY WITH ASSUMPTIONS: public text replay, existing authorized DeepSeek configuration, synthetic context coverage, no company-performance claim. Existing v6 implementation evidence remains scoped to v6. User's architecture judgment is recorded; independent implementation mastery is unassessed. Next: inspect actual outputs and decide whether normalization benefit justifies Builder time before scheduling or SQL integration. Mandatory LiveKit preemption in ../v6/NEXT-VERSION.md remains pending.

## Successor experiment

[Length gate with long and compound questions](GATED-DESIGN.md) uses replay_gated.py, preserving this first experiment and its results. See GATED-RESULTS.md after completion.
