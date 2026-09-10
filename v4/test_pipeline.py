import asyncio

import pytest

from rag_poc.endpoints import ExactChecker
from rag_poc.models import Plan, Query
from rag_poc.pipeline import Pipeline


class Builder:
    def __init__(self):
        self.calls = []

    async def build(self, text, context, previous, *, final):
        self.calls.append((text, final, context))
        return Plan("wait", None) if text == "um" else Plan("retrieve", Query(name=text))


class DB:
    def __init__(self):
        self.calls = []

    async def search(self, query):
        self.calls.append(query)
        return [{"product_name": query.name}]


class Answer:
    async def respond(self, text, context, evidence, *, can_rewrite):
        return {"action": "answer", "text": evidence[-1].rows[0]["product_name"] if evidence else "No data"}


@pytest.fixture
def parts():
    return Builder(), ExactChecker(), DB(), Answer()


async def drain(candidate):
    await asyncio.wait_for(candidate.builder, 1)
    if candidate.retrieval:
        await asyncio.wait_for(candidate.retrieval, 1)


@pytest.mark.asyncio
async def test_regular_baseline_builds_once_and_retrieves_once(parts):
    b, c, db, a = parts
    p = Pipeline(b, c, db, a, speculate=False)
    try:
        p.start_turn([])
        assert p.observe("Chai") is None
        bundle = await p.finish("Chai")
        assert bundle.path == "demand"
        assert await p.answer(bundle) == "Chai"
        assert len(b.calls) == len(db.calls) == 1
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_ready_match_reuses_builder_and_retrieval(parts):
    b, c, db, a = parts
    p = Pipeline(b, c, db, a, min_interval=0)
    try:
        p.start_turn([])
        await drain(p.observe("Chai"))
        bundle = await p.finish("Chai")
        assert bundle.path == "reuse_ready"
        assert await p.answer(bundle) == "Chai"
        assert len(b.calls) == len(db.calls) == 1
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_inflight_match_waits_only_for_selected_task(parts):
    b, c, db, a = parts
    gate = asyncio.Event()

    async def slow(query):
        db.calls.append(query)
        await gate.wait()
        return [{"product_name": query.name}]

    db.search = slow
    p = Pipeline(b, c, db, a)
    try:
        p.start_turn([])
        candidate = p.observe("Chai")
        await candidate.builder
        task = asyncio.create_task(p.finish("Chai"))
        await asyncio.sleep(0.01)
        assert not task.done()
        gate.set()
        bundle = await task
        assert bundle.path == "reuse_wait"
        assert len(db.calls) == 1
    finally:
        gate.set()
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_correction_does_not_wait_for_irrelevant_retrieval(parts):
    b, c, db, a = parts
    cancelled = asyncio.Event()

    async def search(query):
        db.calls.append(query)
        if query.name == "Chai":
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        return [{"product_name": query.name}]

    db.search = search
    p = Pipeline(b, c, db, a)
    try:
        p.start_turn([])
        await p.observe("Chai").builder
        bundle = await asyncio.wait_for(p.finish("Chang"), 1)
        assert bundle.path == "demand"
        assert bundle.evidence[-1].rows == [{"product_name": "Chang"}]
        await asyncio.wait_for(cancelled.wait(), 1)
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_shared_query_task_is_not_cancelled_with_unselected_alias(parts):
    b, c, db, a = parts
    original = b.build

    async def build(text, context, previous, *, final):
        return await original("Chai", context, previous, final=final)

    b.build = build
    p = Pipeline(b, c, db, a, min_interval=0)
    try:
        p.start_turn([])
        first = p.observe("chai price")
        await drain(first)
        second = p.observe("Chai cost")
        await second.builder
        assert first.retrieval is second.retrieval
        bundle = await p.finish("Chai cost")
        assert bundle.path == "reuse_ready"
        assert len(db.calls) == 1
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_checker_error_falls_back_to_final_query(parts):
    b, c, db, a = parts

    async def bad(*args):
        raise ValueError("malformed endpoint")

    c.select = bad
    p = Pipeline(b, c, db, a)
    try:
        p.start_turn([])
        await drain(p.observe("Chai"))
        bundle = await p.finish("Chang")
        assert bundle.path == "demand"
        assert bundle.evidence[-1].query.name == "Chang"
        assert any(e["event"] == "checker_fallback" for e in p.trace)
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_context_is_frozen_and_old_builder_cannot_publish(parts):
    b, c, db, a = parts
    gate, cancel_seen = asyncio.Event(), asyncio.Event()
    captured = []

    async def resistant(text, context, previous, *, final):
        captured.append(context)
        if text == "old":
            try:
                await gate.wait()
            except asyncio.CancelledError:
                cancel_seen.set()
                await gate.wait()
        return Plan("retrieve", Query(name=text))

    b.build = resistant
    p = Pipeline(b, c, db, a)
    context = [{"role": "user", "content": "original"}]
    try:
        p.start_turn(context)
        old = p.observe("old")
        await asyncio.sleep(0)
        context[0]["content"] = "changed"
        p.start_turn([])
        await asyncio.wait_for(cancel_seen.wait(), 1)
        gate.set()
        await old.builder
        bundle = await p.finish("new")
        assert captured[0][0]["content"] == "original"
        assert old.retrieval is None
        assert [q.name for q in db.calls] == ["new"]
        assert bundle.evidence[-1].query.name == "new"
    finally:
        gate.set()
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_no_query_and_timeout_do_not_reuse_prior_evidence(parts):
    b, c, db, a = parts
    p = Pipeline(b, c, db, a, final_timeout=0.01, builder_grace=0)
    try:
        p.start_turn([])
        first = await p.finish("Chai")
        await p.answer(first)
        p.start_turn([])
        second = await p.finish("um")
        assert second.path == "no_query" and not second.evidence
        await p.answer(second)

        async def stall(*args, **kwargs):
            await asyncio.Event().wait()

        b.build = stall
        p.start_turn([])
        third = await p.finish("Chang")
        assert third.path == "final_timeout" and not third.evidence
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_candidate_quota_and_duplicates_do_not_spend_unbounded_calls(parts):
    p = Pipeline(*parts, min_interval=0)
    try:
        p.start_turn([])
        assert p.observe("Chai")
        assert p.observe("Chai") is None
        assert p.observe("Chang")
        assert p.observe("other") is None
        assert len(p.candidates) == 2
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_answer_rewrites_once_without_calling_checker_again(parts):
    b, c, db, a = parts
    checker_calls = []
    answer_calls = []
    select = c.select

    async def select_count(*args):
        checker_calls.append(args)
        return await select(*args)

    async def respond(text, context, evidence, *, can_rewrite):
        answer_calls.append(can_rewrite)
        return ({"action": "retrieve", "query": Query(name="Chang")} if can_rewrite else
                {"action": "answer", "text": evidence[-1].rows[0]["product_name"]})

    c.select, a.respond = select_count, respond
    p = Pipeline(b, c, db, a, speculate=False)
    try:
        p.start_turn([])
        bundle = await p.finish("missing")
        before = len(checker_calls)
        assert await p.answer(bundle) == "Chang"
        assert len(checker_calls) == before
        assert answer_calls == [True, False]
        assert bundle.rewrites == 1
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
async def test_timeout_returns_while_resistant_dependency_is_still_pending(parts):
    b, c, db, a = parts
    release, cancelled = asyncio.Event(), asyncio.Event()

    async def resistant(*args, **kwargs):
        try:
            await release.wait()
        except asyncio.CancelledError:
            cancelled.set()
            await release.wait()
        return Plan("retrieve", Query(name="obsolete"))

    b.build = resistant
    p = Pipeline(b, c, db, a, final_timeout=0.01)
    try:
        p.start_turn([])
        result = await asyncio.wait_for(p.finish("Chai"), 1)
        assert result.path == "final_timeout"
        await asyncio.wait_for(cancelled.wait(), 1)
        release.set()
        await asyncio.sleep(0.01)
        assert not db.calls
    finally:
        release.set()
        assert await p.close() == 0
