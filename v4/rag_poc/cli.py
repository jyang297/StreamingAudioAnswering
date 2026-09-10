import argparse
import asyncio
import json
import logging
from pathlib import Path

from .database import PostgresCatalog
from .endpoints import Answerer, Builder, ExactChecker, JSONEndpoint, LLMChecker
from .livekit_adapter import replay_session
from .pipeline import Pipeline
from .timing import span


async def run(args):
    endpoint = JSONEndpoint.from_env()  # Missing config fails before any DB/network request.
    db = None
    embeddings = None
    try:
        with span("database_connect"):
            db = await PostgresCatalog.connect(credential_file=args.credential_file)
        if args.checker == "semantic":
            from .semantic import LocalEmbeddings, SemanticChecker
            if args.semantic_threshold is None:
                raise ValueError("--semantic-threshold is required; no calibrated default exists")
            embeddings = LocalEmbeddings.load(args.embedding_cache)
            with span("embedding_warmup"):
                await embeddings.encode(["Retrieve catalog products."])
            checker = SemanticChecker(embeddings, threshold=args.semantic_threshold)
        else:
            checker = LLMChecker(endpoint) if args.checker == "llm" else ExactChecker()
        pipeline = Pipeline(Builder(endpoint, prompt_version=args.builder_prompt), checker, db, Answerer(endpoint),
                            speculate=args.speculate, trigger_policy=args.trigger_policy,
                            min_interval=args.trigger_ms / 1000, change_threshold=args.change_units,
                            max_builder_calls=args.max_builder_calls, builder_grace=args.builder_handoff_ms / 1000)
        turns = (json.loads(Path(args.turns_file).read_text()) if args.turns_file else
                 [{"partials": args.partial, "final": args.text, "gap_ms": args.gap_ms}])
        result = await replay_session(pipeline, turns)
        result.update(builder_prompt=args.builder_prompt, trigger_config={"policy":args.trigger_policy,"window_ms":args.trigger_ms,
            "change_units":args.change_units,"max_builder_calls":args.max_builder_calls,
            "builder_handoff_ms":args.builder_handoff_ms}, checker_metrics=getattr(checker, "metrics", []), checker_type=args.checker, step_timings=pipeline.timings, endpoint_metrics=endpoint.metrics, database_metrics=db.metrics,
            boundary="Real configured text endpoint + local PostgreSQL; scripted STT, no TTS/audio latency")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        try:
            if db:
                with span("database_close"):
                    await db.close()
        finally:
            try:
                if embeddings is not None:
                    with span("embedding_cleanup"):
                        await embeddings.close()
            finally:
                with span("endpoint_close"):
                    await endpoint.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="What is the price of Chai?")
    parser.add_argument("--partial", action="append", default=[])
    parser.add_argument("--turns-file")
    parser.add_argument("--gap-ms", type=float, default=150)
    parser.add_argument("--credential-file", help="This task's generated DB credential file only")
    parser.add_argument("--checker", choices=["exact", "llm", "semantic"], default="llm")
    parser.add_argument("--speculate", action="store_true", help="Default is the regular retrieval baseline")
    parser.add_argument("--semantic-threshold", type=float)
    parser.add_argument("--embedding-cache", default="/private/tmp/livekit-semantic-models")
    parser.add_argument("--trigger-policy", choices=["legacy","time","text","hybrid"], default="time")
    parser.add_argument("--trigger-ms", type=float, default=150)
    parser.add_argument("--change-units", type=int, default=3)
    parser.add_argument("--max-builder-calls", type=int, default=6)
    parser.add_argument("--builder-handoff-ms", type=float, default=50)
    parser.add_argument("--builder-prompt", choices=["v1", "v2", "v3"], default="v1")
    args = parser.parse_args()
    timing_logger = logging.getLogger("rag_poc.timing")
    timing_logger.setLevel(logging.INFO)
    timing_logger.propagate = False
    if not timing_logger.handlers:
        handler = logging.StreamHandler()  # stderr; stdout remains the result JSON.
        handler.setFormatter(logging.Formatter("%(message)s"))
        timing_logger.addHandler(handler)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
