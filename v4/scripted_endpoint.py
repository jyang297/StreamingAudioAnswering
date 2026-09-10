"""Test-only HTTP response script. It does not demonstrate language understanding.

Only the exact Chai/Chang/stock scenarios below are handled. Rows are obtained
from the real PostgreSQL adapter, never synthesized by this endpoint fixture.
"""
import json

import httpx

from rag_poc.models import Query


def transport():
    def handle(request):
        request_body = json.loads(request.content)
        instruction = request_body["messages"][0]["content"]
        payload = json.loads(request_body["messages"][1]["content"])
        if "Construct a retrieval query" in instruction:
            text = payload["text"].lower()
            if text == "stock?":
                texts = [m["content"].lower() for m in payload["confirmed_context"] if m["role"] == "user"]
                text = next((x for x in reversed(texts) if "chai" in x or "chang" in x), "")
            name = "Chang" if "chang" in text else "Chai" if "chai" in text else None
            result = {"action": "retrieve", "query": {"name": name}} if name else {"action": "wait"}
        elif "Decide if any earlier query" in instruction:
            matches = [c for c in payload["candidates"] if c["query"] == payload["final_query"]]
            result = {"candidate_id": matches[0]["id"] if matches else None}
        else:
            rows = payload["evidence"][-1]["rows"] if payload["evidence"] else []
            result = {"action": "answer", "text": "SCRIPTED ANSWER FROM SQL: " + json.dumps(rows)}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}],
                                        "usage": {"total_tokens": 0}})
    return httpx.MockTransport(handle)
