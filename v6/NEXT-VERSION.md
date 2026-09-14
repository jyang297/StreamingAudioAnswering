---
ai_contribution: authored
updated: 2026-09-13
status: required-experiment-not-implemented
---

# Next version: mandatory preemptive-generation experiment

User decision (2026-09-13): “preemptive generation 对于实践非常关键…必须在下个版本进行测试…用side chat或者其他手段了解细节.” This is a required next-version experiment, not a claim that v6 implements or validates it.

Side chat: LiveKit preemptive generation 机制与下一版实验
Thread ID: 01a09d90-1d63-72c2-997d-fb5c7073b6a7 (local, LearningVault+).
The side chat investigates matching SDK source, explains the mechanism in Chinese, and prepares experiment details. It does not change product code or initiate paid calls.

## Hypothesis to investigate

Start one SQL/RAG task after usable STT text becomes available but before the user turn is confirmed. If the final request and relevant history/tools/database scope are unchanged, preserve that task. If they change, cancel or regenerate. Unlike the current v6 policy, the intended experiment must test whether an unconditional second final Builder and semantic Checker can be avoided for identical effective inputs. This does not certify answer correctness or remove ordinary evidence checks.

Do not assume a provider's STT final event equals a complete user turn. Measure the available window; short turns might provide little or none. Verify whether LiveKit actually starts the custom SQL/RAG work preemptively; merely enabling LLM preemption does not prove that downstream work starts early.

## Required experimental coverage

- Comparable baseline with preemption disabled; same inputs, model, schema and endpoint settings.
- Unchanged text/context: observe retention of one in-flight/completed task and count duplicate requests.
- Appended/corrected text and context/tool changes: observe invalidation and prevent stale output.
- Barge-in/cancellation and no usable early window: preserve turn ownership and report wasted work.
- Separate cache-hit, generated-SQL and external-RAG paths; no audio cache.
- Distinguish SDK event replay from real STT/Vertex measurements. Neither substitutes for the other.

## Required observations

Actual user speech end; interim/final STT timestamps and cumulative text revision; turn confirmation; LLM/tool/SQL/RAG request start; first answer token; first informative audio; retained/cancelled/restarted request IDs; incorrect reuse and extra endpoint usage. Do not treat filler speech as an informative answer.

## Pending mechanism decisions

Confirm installed/pinned SDK version and its relevant source, STT final semantics, hooks for starting custom work, changes in on_user_turn_completed that trigger regeneration, external request cancellation, and the exact effective-input identity. No fixed 150ms window, speedup target or production compatibility is accepted yet.

References to verify against the chosen SDK: https://docs.livekit.io/agents/logic/turns/tuning/ ; https://docs.livekit.io/agents/multimodality/audio/ ; https://github.com/livekit/agents .

v6 remains the multi-table baseline. Its original test evidence and implementation scope are unchanged.
