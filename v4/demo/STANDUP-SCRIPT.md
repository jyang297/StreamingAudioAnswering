# Standup script — LiveKit anticipatory retrieval

Suggested delivery: about 3–4 minutes, plus questions. Slides are self-contained and offline; no API or microphone needed. Use arrow controls, source buttons and speaker notes. The architecture stepper is illustrative, not a live run.

## 1. Start retrieval before the turn ends.

We now have a local experiment for moving retrieval earlier in the current user turn. We keep the existing cascaded architecture. This is not a next-question answer cache, and we have not yet demonstrated faster real voice responses.

Evidence: [E01](../rag_poc/pipeline.py), [E02](../rag_poc/livekit_adapter.py), [E03](../rag_poc/cli.py)

## 2. One transcript stream. Two decision moments.

There is no second STT. Partial text goes to the Builder, not directly to the Checker. At end of turn we check the final executable query against valid candidates and wait only for the selected retrieval. Final wait skips Checker, but the current Answerer can still rewrite; that remains a known failure boundary.

Evidence: [E01](../rag_poc/pipeline.py), [E02](../rag_poc/livekit_adapter.py)

## 3. Spend work where there is a useful window.

A short question may offer almost no useful prediction window. Follow-ups can be one word but still need correct history resolution. We added coalescing and bounded work so that partial transcripts do not create an unbounded queue. These are scheduling mechanisms, not measured latency wins.

Evidence: [E01](../rag_poc/pipeline.py), [E02](../rag_poc/livekit_adapter.py), [E03](../rag_poc/cli.py)

## 4. What the tests actually establish.

The portable source passes 74 local tests, with database tests explicitly skipped. In the paired Builder run, v3 reduced unsupported approximations, but did not improve strict field matches. Separately, real embedding similarity at point nine nine still accepted two wrong candidates. None of these datasets is a production holdout.

Evidence: [E04](../evidence/builder-fidelity-20260910/README.md), [E05](../evidence/semantic-20260910/README.md), [E06](../evidence/triggers-20260910/README.md), [E07](../handoff-verification.json)

## 5. Valid JSON can still be the wrong query.

The important finding is not merely that prompt v3 has fewer formatting errors. On this case v2 was rejected, while v3 produced a valid query that silently lost the package constraint. We need to keep request fidelity, candidate applicability and answer sufficiency separate.

Evidence: [E04](../evidence/builder-fidelity-20260910/README.md), [E01](../rag_poc/pipeline.py)

## 6. Borrow mechanisms; keep the differences explicit.

MoshiRAG motivates asynchronous knowledge access in ongoing speech interaction. Stream RAG is the closer inspiration for early query generation and later verification. Our implementation adapts these ideas to a cascaded LiveKit system; it does not reproduce their models or inherit their reported gains.

Evidence: [R01](https://arxiv.org/html/2510.02044v1#S3), [R02](https://arxiv.org/html/2604.12928v3#S3), [R03](https://docs.livekit.io/agents/logic/nodes/), [R04](https://docs.livekit.io/reference/agents/turn-handling-options/), [E02](../rag_poc/livekit_adapter.py)

## 7. Move the experiment into the real stack.

The handoff is ready for another agent to adapt this to our internal LiveKit project. The next concrete work is the domain contract and a small labeled evaluation set. We should preserve the existing answer and tool path, introduce feature flags, then measure usefulness on authorized recordings before enabling it for users.

Evidence: [U01](../COMPANY-AGENT-HANDOFF.md), [E03](../rag_poc/cli.py), [E04](../evidence/builder-fidelity-20260910/README.md), [E06](../evidence/triggers-20260910/README.md)

## Questions to anticipate

- **Is this next-question prediction?** No. It anticipates retrieval within the current turn; short follow-ups use committed history.
- **Do we need an audio LLM or second STT?** This implementation uses one STT and text endpoints. It is an adaptation, not a Moshi model deployment.
- **How much faster is it?** No reliable real-voice speedup is established. Early work helps only when useful overlap exceeds added overhead.
- **Can we ship semantic .99?** No. Two of eight negative pairs were falsely accepted in the small diagnostic.
- **Does v3 solve missing conditions?** No. A valid Query can still omit a required filter; the latest evidence includes that counterexample.
- **Can we replace the company LLM with PipelineLLM?** Not directly. Preserve tools and streaming; adapt the evidence-consumption boundary.
