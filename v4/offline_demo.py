"""Real SQL/SDK demonstration with explicit scripted JSON endpoint responses."""
import argparse
import asyncio
import json

import httpx

from rag_poc.database import PostgresCatalog
from rag_poc.endpoints import Answerer, Builder, JSONEndpoint, LLMChecker
from rag_poc.livekit_adapter import replay_session
from rag_poc.pipeline import Pipeline
from scripted_endpoint import transport


async def run(credential_file):
    results = []
    for speculate in (False, True):
        db = await PostgresCatalog.connect(credential_file=credential_file)
        try:
            async with httpx.AsyncClient(transport=transport()) as client:
                ep = JSONEndpoint(base_url="http://scripted.test/v1", model="NO-REAL-LLM", client=client)
                p = Pipeline(Builder(ep), LLMChecker(ep), db, Answerer(ep),
                             speculate=speculate, min_interval=0)
                result = await replay_session(p, [
                    {"partials": ["Chai"], "final": "Chai", "gap_ms": 40},
                    {"partials": ["stock?"], "final": "stock?", "gap_ms": 40},
                    {"partials": ["Chai"], "final": "Chang", "gap_ms": 40},
                ])
                result.update(speculate=speculate, database_metrics=db.metrics,
                    endpoint_contract_metrics=ep.metrics,
                    boundary="REAL PostgreSQL and LiveKit; SCRIPTED HTTP responses and STT; no model or audio latency")
                results.append(result)
        finally:
            await db.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--credential-file", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.credential_file))
