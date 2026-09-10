# Company integration handoff: anticipatory retrieval in Python LiveKit

Status: experimental integration reference, 2026-09-10. This handoff is for an agent working in an authorized company repository after the research repository has been cloned. It is not a production release or a request to upload company material to this research repository.

## Entry points after cloning

From the research repository root, the current experiment is `40-Exercises/Sandbox/LiveKitAnticipationPoC/v4/`. If you use the scoped PoC export instead of the full vault clone, the package root contains `requirements.txt` and `v4/`; begin at `v4/`. All paths below are relative to v4 unless marked otherwise. Start with this handoff, `README.md`, `INTERFACE-AND-SCHEDULING.md`, then the implementation. Historical documents contain original machine paths; use the relative paths here for migration.

| Responsibility | Files to inspect |
|---|---|
| Turn ownership, scheduling, candidate lifecycle, fallback | `rag_poc/pipeline.py` |
| Query, Plan, Evidence and catalog schema | `rag_poc/models.py` |
| Builder versions | `rag_poc/builder_prompts.py` |
| HTTP, Builder, three-role contracts, exact/LLM Checker, Answerer | `rag_poc/endpoints.py` |
| Actual embedding/cosine Checker | `rag_poc/semantic.py` |
| Parameterized sample database retrieval | `rag_poc/database.py` |
| SDK hooks and replay-only assumptions | `rag_poc/livekit_adapter.py` |
| CLI defaults and structured timing | `rag_poc/cli.py`, `rag_poc/timing.py` |
| Regression boundaries | `test_pipeline.py`, `test_triggers.py`, `test_candidate_boundaries.py`, `test_builder_versions.py` |

## What to carry forward

The architecture uses the existing **single STT stream**. While the user speaks, cumulative transcript snapshots may cause a text-model Builder to emit an executable query. Retrieval can run before end of turn. Once the SDK commits the final user turn, obtain a final query and ask a Checker which earlier query, if any, is applicable. Reuse only that selected current-turn task; otherwise use regular retrieval. Answer generation retains responsibility for insufficient evidence and any bounded rewrite.

```text
existing STT -> cumulative snapshot -> scheduler -> Builder -> query -> early retrieval task
                                                  | wait: no candidate
SDK final turn -> final text + confirmed history -> final Builder / valid same-input handoff
                                                  | wait: no_query; no Checker
                                                  v
                                        Checker(candidate queries)
                                          | selected: bounded wait / reuse
                                          | none/unusable: regular retrieval
                                                  v
                              current-turn evidence -> existing answer/tool/TTS path
```

The last line is the **target integration**, not a claim that the current replay provider preserves company tools. The repository's `PipelineLLM` instead owns a separate Answerer loop and returns one full text chunk.

Keep three experimental decisions independent:

- Scheduler: `time`, `text`, `hybrid`, with `legacy` retained only as an old comparison. New strategies have one active partial Builder and one replaceable latest pending snapshot.
- Builder: v1 remains the default; v2/v3 are opt-in experiments. None is proven safe on company requests.
- Checker: LLM remains the default; exact and semantic are separate comparison arms. Do not silently compose them or change the default based on these development sets. Semantic means real model embeddings and cosine, never hash/lexical stand-ins; there is no calibrated production threshold.

CLI defaults: speculation off; when explicitly enabled, time strategy, 150 ms, text change threshold 3 units, at most 6 partial Builder requests, 2 retained valid candidates, and 50 ms same-input Builder handoff at EOT. **The Python `Pipeline` constructor differs: it defaults to speculation on and legacy strategy. Pass explicit settings in integration code.** These numbers are experimental starting values, not latency or accuracy guarantees.

## LiveKit integration contract

First inspect the company's installed Python/LiveKit versions, provider classes, turn detection, interruption handling and tools. The PoC was exercised against `livekit-agents==1.8.0`; do not pin or upgrade the company project to that version automatically. Prefer supported public hooks in its actual version and record any interface differences.

| Boundary | Current PoC mechanism | Required company adaptation / invariant |
|---|---|---|
| STT observation | `PipelineAgent.stt_node` wraps `Agent.default.stt_node` and yields original events onward | Observe the existing provider; do not launch another STT or consume events needed by the SDK. Preserve provider errors and lifecycle. |
| Snapshot construction | START resets; INTERIM replaces current interim; FINAL appends a confirmed segment and clears interim | Verify whether the real provider emits segment text or cumulative text, final retransmissions, stable segment IDs and revisions. A FINAL segment is not necessarily end of turn. Avoid duplicated words/segments. |
| Turn finalization | `on_user_turn_completed(turn_ctx, new_message)` calls `finish(new_message.text_content)` | Use the SDK's committed final text as authority, not the last partial. Freeze candidate IDs and queries for the Checker. |
| Confirmed context | Replay manually appends user and assistant messages after an assistant completion event | Bind to the company session's committed conversation state. Exclude partials, speculative answers, internal bundle markers and unsent drafts. Define treatment of interrupted/partially spoken assistant messages from actual SDK events. |
| Evidence injection | Hook inserts `RAG_BUNDLE:<uuid>`; custom `PipelineLLM` looks up in-memory evidence | This marker contains **no evidence** and works only with that custom provider. For the company's existing LLM, implement explicit current-turn evidence injection or a typed application-state/tool contract. Do not pass an opaque marker to an ordinary plugin. |
| Answer/tool/TTS delivery | PoC Answerer returns one complete text chunk; no TTS in replay | Preserve the existing answer model, tools, tool-choice rules, streaming and TTS. `PipelineLLM` accepting a `tools` parameter does not mean it executes company tools. |
| Native preemptive generation | Disabled in the replay session | Keep it disabled for the first anticipatory-retrieval integration arm. Bundle readiness and context mutation are not compatible by assumption. If baseline already enables it, preserve that original baseline and report the setting difference. A later combined arm needs separate lifecycle tests. |

Per-turn state must include ownership of candidate IDs, transcript/context revisions, tasks and evidence. Current local revision counters are not a complete provider revision protocol. Old or cancelled work must never publish into another turn. Candidate eviction must not cancel a retrieval task still shared by another valid candidate. Cancellation of an await does not guarantee a remote model request or native embedding computation stops.

Only the selected retrieval may be awaited, with bounded deadlines and a normal fallback; never join all speculative work. Verify cancellation and completion ownership again before evidence consumption. Production barge-in, resumed speech, overlapping turns, provider FINAL retransmissions and reconnects have **not** been validated by this PoC. Disable speculative consumption when lifecycle ownership cannot be established rather than treating a sequential replay test as coverage.

## Replace the domain contract as a unit

The 77-row public Northwind catalog is a reproducible fixture, not company knowledge. Its full-row SQL results make some price/stock questions share a Query; a document retriever may return different evidence for each attribute.

Change the following together, under one reviewed interface contract:

1. Retrieval capabilities and authorization boundaries: allowed indexes/tables, tenant/user access, filters, top-k, freshness and evidence identity.
2. Query schema, validation and canonical representation in `models.py`.
3. Builder schema descriptions and prompts; preserve intended entity, requested attributes, negations, ranges and contextual references.
4. Retrieval adapter, parameter binding, result/error representation and deadlines.
5. Checker input representation and exact/semantic serialization; re-evaluate thresholds after any representation change.
6. Answer evidence formatting, source attribution and the allowed rewrite interface.

Do not merely replace a connection string with Cloud SQL and keep catalog semantics. Do not let model output become executable SQL. Define whether broad retrieval is permitted: it needs a coverage argument and downstream constraint enforcement. With the current conservative contract, unsupported requirements mean `wait`; prompt instructions alone do not enforce fidelity.

A final `wait` returns `no_query` and skips Checker, **but Answerer still runs and may request a rewrite**. A prior replay rewrote a follow-up to the wrong entity. Query equality or high similarity cannot recover a condition omitted by both early and final Builders. Before enabling consumption, explicitly define the company's no-query behavior, such as preserving the established regular retrieval/clarification path; any change from the PoC Answerer contract must have its own tests.

## Reproduce the research baseline without machine paths

Run these in an isolated research environment, not by overwriting the company application's dependency lockfile. Python 3.12 was used locally.

```sh
# From the cloned research repository root:
cd 40-Exercises/Sandbox/LiveKitAnticipationPoC
python3 -m venv .venv-handoff
. .venv-handoff/bin/activate
python -m pip install -r requirements.txt -r v4/requirements-v4.txt
cd v4
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

The parent `requirements.txt` supplies SDK/test dependencies; `requirements-v4.txt` alone is insufficient. The last recorded run was 74 passed and 3 database tests skipped; newly reproduced results should be recorded separately, not represented as historical results.

For optional real semantic evaluation, additionally install `requirements-semantic.txt` and provide a local `--embedding-cache` path explicitly; the old CLI default is a machine-specific temporary directory. The pinned ONNX MiniLM model and serialization are documented in `evidence/semantic-20260910/README.md`. Model download/network availability must be established before timing the online arm.

Real calls are separate from the default regression run. Use `.env.example` only to create a missing local `.env`; never overwrite existing configuration. Fixed `v4/.env` loading uses process variables first and does not search parent folders. Do not copy private credentials between repositories. The explicit compatible-endpoint configuration is in `config.example.sh`; company endpoint selection must comply with company requirements rather than inherit the personal DeepSeek provider.

For an optional **local public fixture** run, inspect `postgres-fixture/README.md` before setup: its scripts create/reset fixture objects. Do not execute those scripts against a company database. Once that isolated service is prepared, from v4:

```sh
python -m rag_poc.cli --credential-file postgres-fixture/.env \
  --text 'What is the price of Chai?' > baseline.json 2> baseline-timing.jsonl
python -m rag_poc.cli --credential-file postgres-fixture/.env \
  --speculate --builder-prompt v1 --checker llm --trigger-policy time \
  --partial 'What is the price of Chai?' --gap-ms 2000 \
  --text 'What is the price of Chai?' > speculative.json 2> speculative-timing.jsonl
```

These commands make real configured model/DB calls. Replay gaps are synthetic and do not establish voice latency. Do not automatically rerun all stored model evaluations: they can make hundreds of calls. No Jetson or local audio model is required.

## Staged company delivery and acceptance

| Stage | Deliverable and acceptance before advancing | Rollback |
|---|---|---|
| 0. Inspect and baseline | Read company AGENTS instructions and actual dependency lockfile. Map STT/EOT/context/LLM/tools/TTS interfaces; record existing baseline settings and tests. Identify authorized endpoint/data and unresolved requirements. No runtime behavior change. | Discard documentation branch; original runtime unchanged. |
| 1. Contract and controlled adapter tests | Add explicit feature flag default off, domain contract, transcript adapter and fake controllable dependencies. Pass tests for cumulative/revised transcripts, duplicate final segments, final-only turns, wait, shared tasks, deadlines, late results, context isolation and supported interruption lifecycle. Existing application tests still pass. | Flag off restores original route, without creating speculative tasks or extra model calls. |
| 2. Shadow integration | Use authorized test sessions first. Compute candidates and decisions without inserting their evidence into answers or executing side effects. Verify attribution, budgets, original tools/TTS and baseline answers remain intact; record scheduling cost. Protect company transcripts and evidence in local/company logs. | Disable shadow flag; drain/cancel owned tasks; no markers or stale evidence remain. |
| 3. Frozen offline quality evaluation | Use authorized, independently labeled company transcripts with long questions, short independent questions, brief follow-ups, entity switches, late negations and unsupported constraints. Freeze schema/prompts/checker per run. Report Builder fidelity, Checker false acceptance and Answerer correctness separately. Compare identical inputs against regular retrieval. Set explicit acceptable error/latency/cost limits with the project owner before controlled enablement. | Keep consumption disabled; preserve failed examples as evaluation evidence; do not retune on the held-out set. |
| 4. Controlled opt-in consumption | Enable only the test cohort/configuration whose acceptance limits were met. Verify real STT/TTS EOT-to-first-audio latency, tail latency, answer quality, costs and interruptions. Confirm a tested kill switch and ordinary retrieval fallback. | Immediately disable consumption if agreed limits fail, ownership becomes uncertain, or tools/TTS regress; retain original baseline path. |

Do not invent an acceptable false-positive rate for the team. The stated priority is much higher cost for wrong reuse than for missed reuse. A useful report includes FP per negative, FP per accepted reuse, missed valid reuse, evidence ready before EOT, selected-task wait, demand/rewrite frequency, Builder/Checker calls and tokens, and end-to-end answer quality. Observe actual user-speech end, SDK EOT and first audio separately where available. Parent/child or concurrent timing spans must not be added to claim speedup.

## Evidence and honest limits

| Evidence | What it supports | What it does not support |
|---|---|---|
| `evidence/deepseek-20260910/` | Real configured endpoint/local SQL through scripted SDK replay | Real ASR, microphone, TTS or voice latency improvement |
| `evidence/semantic-20260910/` | Real ONNX cosine comparison; two false accepts at .99 on 12 frozen query cases | Production-safe threshold or proof that semantic outperforms LLM |
| `evidence/builder-expanded-20260910/` | 100 parameterized development cases, 240 calls; fewer missed retrieval opportunities with v2, some duplicate outputs | 100 independent mechanisms, held-out production accuracy, Checker FP or answer correctness |
| `evidence/builder-challenge-20260910/` | 24 challenge cases, 72 calls exposing constraint errors | Production error-rate estimate |
| `evidence/builder-fidelity-20260910/` | 36 inputs, 108 v2/v3 calls; unsupported-demand approximations decreased from 5 to 2 in the main sample | Guaranteed constraint preservation; one illegal-output rejection became a legal query that dropped a requirement |
| Local deterministic regression | Contracts, bounded scheduling, shared-task and controlled cancellation behaviors | Production concurrency, GCP readiness or complete voice integration |

The sets overlap and serve different purposes. Do not sum them into a pooled accuracy number. Default v1 is retained for continuity, not because it has established superior quality. Native preemptive generation, Krites answer caching, vCache and next-turn answer precomputation are not implemented optimizations in this delivery.

References explain inspiration rather than establish this implementation's performance: [Stream RAG §3](https://arxiv.org/html/2510.02044v1#S3) separates retrieval decisions from response generation; [MoshiRAG §3](https://arxiv.org/html/2604.12928v3#S3) motivates asynchronous retrieval in real-time interaction. This text-STT PoC does not reproduce their trained audio-model mechanisms. Consult the installed SDK plus [LiveKit nodes](https://docs.livekit.io/agents/logic/nodes/) for the target hook contract.
