# Transfer and standup quick start

This is the portable entry point. Runtime baseline: `e83b511`; the later handoff commit adds documentation and a static demo, without changing retrieval behavior. The user owns remote setup and push; no remote was configured in the local vault when this handoff was prepared.

## Hand the next agent these files

1. `COMPANY-AGENT-PROMPT.md` — copy its content as the initial instruction in the company project.
2. `COMPANY-AGENT-HANDOFF.md` — source map, integration boundaries, staged acceptance and rollback.
3. `INTERFACE-AND-SCHEDULING.md` and `rag_poc/` — implementation details; the handoff uses portable paths where historical notes contain Mac paths.
4. `evidence/` — frozen inputs, real outputs and known failures. These are development diagnostics, not production acceptance data.

For a full vault clone, locate `40-Exercises/Sandbox/LiveKitAnticipationPoC/v4/`. For a scoped export, locate `v4/` under the package root. Keep the parent `requirements.txt` together with v4: `requirements-v4.txt` alone does not install the SDK/test dependencies.

## Scope of what to push

The Git repository currently containing the PoC is the larger LearningVault repository. The configuration workspace used during development is not its Git root. Do not mistake a staging copy for the committed runtime source.

If you intend a dedicated PoC repository rather than transferring the whole vault history, export only the committed subtree below, unpack it into a new empty repository, then configure your chosen remote and push there. A subtree export contains no unrelated vault files or vault history. It includes tracked source, public-input evidence, documentation and the `.env.example` template, but no ignored runtime `.env`, database volume or downloaded CSV/model cache.

From the LearningVault Git root, after the handoff commit is present:

```sh
git archive --format=tar --prefix=livekit-anticipation-poc/ \
  --output=/tmp/livekit-anticipation-poc.tar \
  HEAD:40-Exercises/Sandbox/LiveKitAnticipationPoC requirements.txt v4
```

The prepared archive is an optional convenience, not a new remote repository. No remote URL is guessed. A full repo push transfers its existing history as well as the current subtree; the scoped export is available if that is not the intended scope.

## Reproduce after clone or unpack

From the PoC root containing `requirements.txt` and `v4/`:

```sh
python3 -m venv .venv-handoff
. .venv-handoff/bin/activate
python -m pip install -r requirements.txt -r v4/requirements-v4.txt
cd v4
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

Use Python 3.12 for the recorded research baseline. On Windows use WSL for the shell/Docker fixture scripts, or adapt activation commands; native Windows execution has not been tested. Do not replace the company application's lockfile with these research requirements. Real model calls, model downloads and database setup are separate opt-in steps in the handoff.

Clean tracked-source export test: 74 passed, 3 database tests skipped in 1.86 s, using the existing local Python environment. This verifies source portability, not a fresh operating-system install or company deployment. See `handoff-verification.json`.

## Standup demo

Open `demo/standup.html` directly in a browser. It has no CDN, external font, API call or microphone requirement. Use the arrow buttons or view selector; `Speaker notes` reveals the talk track, and source buttons reveal evidence links. The architecture walkthrough is an illustrative control sequence, clearly separate from the recorded test results.

- Seven English views; main presentation about 3–4 minutes.
- `demo/STANDUP-SCRIPT.md`: speaker script and likely questions.
- `demo/evidence-map.json`: source IDs and limits.
- To regenerate after editing `build_standup.py`: `python build_standup.py` from v4.
- Browser Print displays all views; printing/PDF export is optional and was not independently validated.

No local server is required. If a browser blocks local file navigation, serve only this directory with `python -m http.server 8768 --bind 127.0.0.1` and open `http://127.0.0.1:8768/demo/standup.html`. Do not use that workaround to bypass a browser security rejection; follow the rejection instead.

## What the presentation must not imply

No demonstrated real-voice speedup, production-safe similarity threshold, company integration, native preemptive combination, or Moshi/Stream RAG model reproduction. v3 remains experimental; legal queries can still drop constraints. A conservative wait skips Checker but the current Answerer can still rewrite incorrectly. The next step is adapting and validating the real company contract, not merely changing a database connection string.

Verification note: the page was visually and interactively checked over local HTTP before a later direct-file automation attempt was blocked by browser URL policy. Direct `file://` automated verification remains pending; no bypass was attempted. The HTML is self-contained and contains no external runtime resources.
