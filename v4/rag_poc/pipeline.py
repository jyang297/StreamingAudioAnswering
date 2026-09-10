from __future__ import annotations

import asyncio
import copy
import time
import math
import re
from difflib import SequenceMatcher
from dataclasses import dataclass, field

from .models import Evidence, Plan, Query
from .timing import span, timed


@dataclass
class Candidate:
    id: int
    turn: int
    text: str
    plan: Plan | None = None
    builder: asyncio.Task | None = None
    retrieval: asyncio.Task | None = None
    error: str | None = None
    superseded: bool = False
    revision: int = 0


@dataclass
class Bundle:
    turn: int
    text: str
    context: list[dict]
    path: str
    evidence: list[Evidence] = field(default_factory=list)
    phase_ms: float = 0
    answer: str | None = None
    rewrites: int = 0


def normalized(text):
    return " ".join(text.split())


def text_units(text):
    # Scheduling units only, NOT semantic similarity: Han characters, words, punctuation.
    return re.findall(r"[\u3400-\u9fff]|[^\W_]+|[^\w\s]", text, re.UNICODE)


def changed_units(before, after):
    matcher = SequenceMatcher(None, text_units(before), text_units(after), autojunk=False)
    return sum(max(i2-i1, j2-j1) for op,i1,i2,j1,j2 in matcher.get_opcodes() if op != "equal")


class Pipeline:
    """Bounded ordered-turn spike. All speculative tasks are local to one turn.

    No next-turn prediction, semantic accuracy promise or provider ID inference.
    Checks happen before waiting for applicable retrieval, never after waiting
    for every previous retrieval job.
    """
    def __init__(self, builder, checker, retriever, answerer, *, speculate=True,
                 max_candidates=2, min_interval=0.15, builder_grace=0.05,
                 final_timeout=20.0, answer_timeout=20.0, max_rewrites=1,
                 trigger_policy="legacy", change_threshold=3, max_builder_calls=6):
        if trigger_policy not in {"legacy", "time", "text", "hybrid"}:
            raise ValueError("invalid trigger policy")
        if not math.isfinite(min_interval) or min_interval < 0 or not math.isfinite(builder_grace) or builder_grace < 0:
            raise ValueError("invalid trigger time budget")
        if type(change_threshold) is not int or change_threshold < 1 or type(max_builder_calls) is not int or max_builder_calls < 1 or max_candidates < 1:
            raise ValueError("invalid trigger count budget")
        self.trigger_policy, self.change_threshold = trigger_policy, change_threshold
        self.max_builder_calls = max_builder_calls
        self.pending_snapshot = None
        self.pending_since = None
        self.dispatch_timer = None
        self.active_candidate = None
        self.last_submitted_text = ""
        self.latest_text = ""
        self.revision = 0
        self.builder_requests = 0
        self.builder, self.checker = builder, checker
        self.retriever, self.answerer = retriever, answerer
        self.speculate, self.max_candidates = speculate, max_candidates
        self.min_interval, self.builder_grace = min_interval, builder_grace
        self.final_timeout, self.answer_timeout = final_timeout, answer_timeout
        self.max_rewrites = max_rewrites
        self.turn = 0
        self.phase = "idle"
        self.context = []
        self.candidates = []
        self.tasks = set()
        self.seen = set()
        self.last_start = float("-inf")
        self.builder_slots = asyncio.Semaphore(1)
        self.retrieval_slots = asyncio.Semaphore(2)
        self.trace = []
        self.timings = []
        self.origin = time.perf_counter()
        self.accepting_candidates = False

    def event(self, name, **data):
        self.trace.append({"event": name, "turn": self.turn,
                           "at_ms": (time.perf_counter() - self.origin) * 1000, **data})

    def spawn(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)

        def done(t):
            self.tasks.discard(t)
            if not t.cancelled():
                t.exception()  # Consume failures of abandoned speculative work.

        task.add_done_callback(done)
        return task

    def cancel_candidates(self):
        for candidate in self.candidates:
            for task in (candidate.builder, candidate.retrieval):
                if task and not task.done():
                    task.cancel()

    def start_turn(self, context):
        if self.phase == "closed":
            raise RuntimeError("pipeline closed")
        if self.phase in ("finalizing", "answering"):
            raise RuntimeError("overlapping turns are outside this ordered replay")
        self.stop_dispatch()
        self.cancel_candidates()
        self.pending_snapshot = self.pending_since = self.active_candidate = None
        self.last_submitted_text = self.latest_text = ""
        self.revision = self.builder_requests = 0
        self.turn += 1
        self.context = copy.deepcopy(context)
        self.candidates, self.seen = [], set()
        self.last_start = float("-inf")
        self.phase = "listening"
        self.accepting_candidates = True
        self.event("turn_start")

    def stop_dispatch(self):
        if self.dispatch_timer is not None:
            self.dispatch_timer.cancel()
            self.dispatch_timer = None
        self.pending_snapshot = self.pending_since = None

    def observe(self, text):
        if self.trigger_policy != "legacy":
            return self.observe_latest(text)
        return self.observe_legacy(text)

    def observe_latest(self, text):
        text = normalized(text)
        if self.phase != "listening" or not self.speculate or text == self.latest_text:
            return None
        self.latest_text = text
        self.revision += 1
        if not text or text == self.last_submitted_text:
            self.stop_dispatch()
            return None
        if self.pending_since is None:
            self.pending_since = time.perf_counter()
        self.pending_snapshot = (text, self.revision)
        self.event("snapshot_updated", revision=self.revision,
                   changed_units=changed_units(self.last_submitted_text, text))
        return self.dispatch_latest()

    def dispatch_latest(self):
        if self.dispatch_timer is not None:
            self.dispatch_timer.cancel()
        self.dispatch_timer = None
        if self.phase != "listening" or self.pending_snapshot is None:
            return None
        if self.active_candidate and self.active_candidate.builder and not self.active_candidate.builder.done():
            return None  # Completion callback retries the single newest pending snapshot.
        if self.builder_requests >= self.max_builder_calls:
            self.event("builder_budget_exhausted", requests=self.builder_requests)
            self.stop_dispatch()
            return None
        text, revision = self.pending_snapshot
        now = time.perf_counter()
        anchor = self.last_start if self.builder_requests else self.pending_since
        remaining = max(0, self.min_interval - (now-anchor))
        delta = changed_units(self.last_submitted_text, text)
        ready = ((self.trigger_policy in {"time", "hybrid"} and remaining == 0) or
                 (self.trigger_policy in {"text", "hybrid"} and delta >= self.change_threshold))
        if not ready:
            if self.trigger_policy in {"time", "hybrid"}:
                self.dispatch_timer = asyncio.get_running_loop().call_later(remaining, self.dispatch_latest)
            return None
        self.stop_dispatch()
        self.last_start, self.last_submitted_text = now, text
        self.builder_requests += 1
        candidate = Candidate(self.builder_requests, self.turn, text, revision=revision)
        self.candidates.append(candidate)
        self.active_candidate = candidate
        self.event("trigger_fired", policy=self.trigger_policy, candidate=candidate.id,
                   revision=revision, changed_units=delta)
        candidate.builder = self.spawn(self.build_candidate(candidate, copy.deepcopy(self.context)))
        owner = self.turn
        def done(task):
            if owner == self.turn and self.phase == "listening":
                self.dispatch_latest()
        candidate.builder.add_done_callback(done)
        return candidate

    def observe_legacy(self, text):
        text = normalized(text)
        now = time.perf_counter()
        if (self.phase != "listening" or not self.speculate or not text or text in self.seen
                or len(self.candidates) >= self.max_candidates
                or now - self.last_start < self.min_interval or len(self.tasks) >= 6):
            return None
        self.seen.add(text)
        self.last_start = now
        candidate = Candidate(len(self.candidates) + 1, self.turn, text)
        self.candidates.append(candidate)
        context = copy.deepcopy(self.context)
        candidate.builder = self.spawn(self.build_candidate(candidate, context))
        return candidate

    @timed("speculative_builder_task")
    async def build_candidate(self, candidate, context):
        try:
            with span("builder_queue_wait"):
                await self.builder_slots.acquire()
            try:
                if candidate.turn != self.turn or self.phase not in ("listening", "finalizing"):
                    return
                previous = [c.plan.query.json() for c in self.candidates if c.plan and c.plan.query]
                self.event("builder_start", candidate=candidate.id)
                with span("partial_query_builder"):
                    plan = await self.builder.build(candidate.text, context, previous, final=False)
            finally:
                self.builder_slots.release()
            if (candidate.turn != self.turn or self.phase not in ("listening", "finalizing")
                    or not self.accepting_candidates or candidate.superseded):
                return
            candidate.plan = plan
            self.event("builder_done", candidate=candidate.id, action=plan.action)
            if plan.query:
                # Equivalent structured queries share one retrieval task.
                same = next((c for c in self.candidates if c is not candidate and not c.superseded and c.plan
                             and c.plan.query == plan.query and c.retrieval and not c.retrieval.cancelled()), None)
                candidate.retrieval = same.retrieval if same else self.spawn(self.search(plan.query))
                if self.trigger_policy != "legacy":
                    valid = [c for c in self.candidates if c.plan and c.plan.query and not c.superseded]
                    for old in valid[:-self.max_candidates]:
                        old.superseded = True
                        if old.retrieval and not old.retrieval.done() and not any(
                                c is not old and not c.superseded and c.retrieval is old.retrieval for c in self.candidates):
                            old.retrieval.cancel()
                        self.event("candidate_evicted", candidate=old.id)
        except Exception as exc:
            candidate.error = type(exc).__name__
            self.event("builder_error", candidate=candidate.id, error=candidate.error)

    @timed("retrieval_task")
    async def search(self, query):
        with span("retrieval_queue_wait"):
            await self.retrieval_slots.acquire()
        try:
            with span("database_search"):
                return await self.retriever.search(query)
        finally:
            self.retrieval_slots.release()

    async def bounded(self, coroutine, timeout):
        task = self.spawn(coroutine)
        done, _ = await asyncio.wait({task}, timeout=max(0, timeout))
        if not done:
            task.cancel()
            raise TimeoutError("phase deadline")
        return task.result()

    @timed("final_resolution")
    async def finish(self, text):
        if self.phase != "listening":
            raise RuntimeError("finish requires an active input turn")
        self.phase = "finalizing"
        self.stop_dispatch()
        started = time.perf_counter()
        self.event("final_received")
        try:
            bundle = await self.bounded(self.resolve_final(text), self.final_timeout)
        except TimeoutError:
            bundle = Bundle(self.turn, text, copy.deepcopy(self.context), "final_timeout")
        except Exception as exc:
            self.event("final_error", error=type(exc).__name__)
            bundle = Bundle(self.turn, text, copy.deepcopy(self.context), "final_error")
        finally:
            self.accepting_candidates = False
            self.cancel_candidates()
        bundle.phase_ms = (time.perf_counter() - started) * 1000
        self.phase = "ready"
        self.event("final_ready", path=bundle.path, phase_ms=bundle.phase_ms)
        return bundle

    async def resolve_final(self, text):
        owner = self.turn
        # Only wait briefly for unknown Builder outputs, never for all retrievals.
        pending = {c.builder for c in self.candidates if c.builder and not c.builder.done()
                   and (self.trigger_policy == "legacy" or c.text == normalized(text))}
        if self.trigger_policy != "legacy":
            for c in self.candidates:
                if c.builder and not c.builder.done() and c.text != normalized(text):
                    c.superseded = True
                    c.builder.cancel()
        if pending and self.builder_grace > 0:
            with span("builder_grace_wait"):
                await asyncio.wait(pending, timeout=self.builder_grace)
        if self.trigger_policy != "legacy":
            for c in self.candidates:
                if c.builder and not c.builder.done():
                    c.superseded = True
                    c.builder.cancel()
                    self.event("builder_handoff_timeout", candidate=c.id)
        identical = next((c for c in self.candidates if not c.superseded and c.plan and c.plan.query
                          and c.text == normalized(text)), None)
        if identical:
            with span("final_query_reuse", candidate=identical.id):
                final_plan = identical.plan
        else:
            with span("final_query_builder"):
                final_plan = await self.builder.build(text, copy.deepcopy(self.context), [], final=True)
        if owner != self.turn or self.phase != "finalizing":
            raise RuntimeError("obsolete final query")
        bundle = Bundle(owner, text, copy.deepcopy(self.context), "no_query")
        if final_plan.query is None:
            return bundle
        # Freeze the candidate set before Checker awaits: late Builder output
        # cannot launch duplicate speculative retrieval alongside final demand.
        self.accepting_candidates = False
        candidates = [c for c in self.candidates if c.turn == owner and not c.superseded and c.plan and c.plan.query
                      and c.retrieval and not c.retrieval.cancelled() and
                      not (c.retrieval.done() and c.retrieval.exception() is not None)]
        views = [{"id": c.id, "query": c.plan.query.json(), "completed": c.retrieval.done()}
                 for c in candidates]
        try:
            with span("checker", checker_type=type(self.checker).__name__, candidate_count=len(views)) as check_log:
                selected_id = await self.checker.select(text, self.context, final_plan.query, views)
                check_log["selected_candidate"] = selected_id
        except Exception as exc:
            selected_id = None
            self.event("checker_fallback", error=type(exc).__name__)
        if owner != self.turn or self.phase != "finalizing":
            raise RuntimeError("obsolete checker result")
        selected = next((c for c in candidates if c.id == selected_id), None)
        # Cancel only unselected retrievals; shared tasks must stay alive.
        for c in self.candidates:
            if c.builder and not c.builder.done():
                c.builder.cancel()
            if c.retrieval and (selected is None or c.retrieval is not selected.retrieval):
                if not c.retrieval.done():
                    c.retrieval.cancel()
        if selected:
            bundle.path = "reuse_ready" if selected.retrieval.done() else "reuse_wait"
            try:
                with span("selected_retrieval_wait", candidate=selected.id):
                    rows = await selected.retrieval
                if owner != self.turn or self.phase != "finalizing":
                    raise RuntimeError("obsolete retrieval completion")
                bundle.evidence.append(Evidence(selected.plan.query, rows))
                self.event("candidate_accepted", candidate=selected.id)
                return bundle
            except Exception as exc:
                self.event("candidate_failed", error=type(exc).__name__)
        bundle.path = "demand"
        try:
            with span("demand_retrieval"):
                rows = await self.search(final_plan.query)
            bundle.evidence.append(Evidence(final_plan.query, rows))
        except Exception as exc:
            bundle.evidence.append(Evidence(final_plan.query, [], type(exc).__name__))
            bundle.path = "retrieval_error"
        return bundle

    @timed("answer_total")
    async def answer(self, bundle):
        if bundle.turn != self.turn or self.phase != "ready":
            raise RuntimeError("answer does not belong to the current turn")
        self.phase = "answering"
        try:
            bundle.answer = await self.bounded(self.answer_loop(bundle), self.answer_timeout)
        except Exception as exc:
            self.event("answer_error", error=type(exc).__name__)
            bundle.answer = "本次未能取得可验证的回答，请稍后重试。"
        finally:
            self.phase = "idle"
        self.event("answer_done", rewrites=bundle.rewrites)
        return bundle.answer

    async def answer_loop(self, bundle):
        for attempt in range(self.max_rewrites + 1):
            with span("answer_llm", attempt=attempt):
                action = await self.answerer.respond(bundle.text, bundle.context, bundle.evidence,
                                                    can_rewrite=attempt < self.max_rewrites)
            if bundle.turn != self.turn or self.phase != "answering":
                raise RuntimeError("obsolete answer completion")
            if action["action"] == "answer":
                return action["text"]
            query = action["query"]
            if any(e.query == query for e in bundle.evidence):
                return "现有资料不足以回答；重复相同查询不会补充信息。"
            bundle.rewrites += 1
            self.event("answer_rewrite", query=query.json())
            try:
                with span("rewrite_retrieval", attempt=attempt):
                    rows = await self.search(query)
                bundle.evidence.append(Evidence(query, rows))
            except Exception as exc:
                bundle.evidence.append(Evidence(query, [], type(exc).__name__))
        return "现有资料不足以回答，已达到本轮重新检索次数限制。"

    @timed("pipeline_cleanup")
    async def close(self, timeout=1.0):
        self.phase = "closed"
        self.stop_dispatch()
        self.cancel_candidates()
        tasks = set(self.tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            _, pending = await asyncio.wait(tasks, timeout=timeout)
            return len(pending)
        return 0
