# Checkpoint · 2026-09-10

Frozen implementation commit: `34e09db` (parent includes timing instrumentation and real DeepSeek trials). Keep exact, LLM and real dense semantic Checker as separate experimental arms. No hybrid Checker or scheduling optimization has been implemented. Python LiveKit1.8.0 + scripted STT, DeepSeek API Builder/Answerer/LLMChecker, Docker PostgreSQL77-row public catalog; localCPU multilingual MiniLM384D realcosine semantic arm. No Jetson, microphone recognition or TTS latency measurements.

User priority: false positive (wrong-query reuse) is much more costly than false negative (fallback retrieval). Do not choose thresholds by aggregate accuracy or knowingly relax correctness to improve hit rate. Numerical production error budget remains unspecified. Answer sufficiency/rewrite stays Answer LLM responsibility, not an excuse for permissive query acceptance.

Evidence: `evidence/deepseek-20260910/` and `evidence/semantic-20260910/`. 47 local tests passed, 12 frozen-query diagnostic cases: exact10/12, LLM12/12, semantic8/12 at.99; these are deliberately selected development examples, not calibrated accuracy. Real semantic mean-pooling ONNX model pinned to revisionfaf4aa4225822f3bc6376869cb1164e8e3feedd0; no hash/lexical substitute. Per-step timings logged; overlap/nesting prevents summation. Original speculation did not demonstrate general end-to-end speedup.

Known open issues: duplicate Builder work around EOT; strict serialized Query equality has representation misses; high cosine does not ensure query coverage; single-process native embedding worker lacks hard kill; 77-row local SQL not representative of companyCloudSQL/fullKB; unknown realASR timing and question mix. Existing preemptive_generation disabled to isolate custom pipeline. No production rollout.

Next stage authorized: source-grounded search for architectural alternatives. Preserve this checkpoint and compare separate routes before implementation; candidate techniques are research proposals, not accepted changes.
