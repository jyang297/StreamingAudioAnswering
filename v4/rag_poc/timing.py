"""Structured monotonic timing; no transcript, query, response, or credential data."""
import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
import logging
import time
import uuid

_context = ContextVar("rag_timing_context", default={})
_sink = ContextVar("rag_timing_sink", default=None)
logger = logging.getLogger("rag_poc.timing")

@contextmanager
def span(step, *, sink=None, **fields):
    parent = _context.get()
    entry = {**parent, **fields, "step": step, "span_id": uuid.uuid4().hex[:12],
             "parent_span_id": parent.get("span_id"), "status": "ok"}
    token = _context.set(entry)
    sink_token = _sink.set(sink) if sink is not None else None
    started = time.perf_counter()
    logger.info(json.dumps({**entry, "event": "start", "time_spent_ms": 0}))
    try:
        yield entry
    except asyncio.CancelledError:
        entry["status"] = "cancelled"
        raise
    except Exception as exc:
        entry.update(status="error", error_type=type(exc).__name__)
        raise
    finally:
        entry.update(event="end", time_spent_ms=round((time.perf_counter()-started)*1000, 3))
        logger.info(json.dumps(entry))
        if _sink.get() is not None:
            _sink.get().append(dict(entry))
        _context.reset(token)
        if sink_token is not None:
            _sink.reset(sink_token)

def timed(step):
    def decorate(fn):
        @wraps(fn)
        async def wrapped(self, *args, **kwargs):
            fields = {"turn": self.turn}
            if step == "speculative_builder_task" and args:
                fields["candidate"] = args[0].id
            with span(step, sink=self.timings, **fields):
                return await fn(self, *args, **kwargs)
        return wrapped
    return decorate
