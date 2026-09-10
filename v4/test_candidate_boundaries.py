"""Control-flow checks; scripted dependencies measure calls, not retrieval quality."""
import asyncio
import pytest
from rag_poc.models import Plan, Query
from test_triggers import make, until


@pytest.mark.asyncio
@pytest.mark.parametrize('policy', ['time', 'text', 'hybrid'])
async def test_duplicate_query_shares_inflight_search_even_after_eviction(policy):
    p = make(trigger_policy=policy, min_interval=0, change_threshold=1, max_candidates=1)
    gate = asyncio.Event()
    calls = []
    async def build(text, context, previous, *, final):
        calls.append((text, final))
        return Plan('retrieve', Query(name='Chang'))
    async def search(query):
        p.retriever.calls.append(query)
        await gate.wait()
        return [{'product_name': 'Chang'}]
    p.builder.build, p.retriever.search = build, search
    try:
        p.start_turn([])
        first = p.observe('Chang price')
        await first.builder
        await until(lambda: len(p.retriever.calls) == 1)
        second = p.observe('Chang stock')
        await second.builder
        assert first.superseded and not second.superseded
        assert first.retrieval is second.retrieval
        assert not second.retrieval.cancelled()
        finishing = asyncio.create_task(p.finish('Chang stock'))
        await asyncio.sleep(0)
        gate.set()
        bundle = await asyncio.wait_for(finishing, 1)
        assert bundle.path in ('reuse_ready', 'reuse_wait')
        assert len(calls) == 2 and len(p.retriever.calls) == 1
        assert bundle.evidence[0].query.name == 'Chang'
    finally:
        gate.set()
        assert await p.close() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('policy', ['time', 'text', 'hybrid'])
async def test_partial_wait_is_not_a_checker_candidate(policy):
    p = make(trigger_policy=policy, min_interval=0, change_threshold=1)
    seen = []
    original = p.checker.select
    async def select(text, context, query, views):
        seen.append(views)
        return await original(text, context, query, views)
    p.checker.select = select
    try:
        p.start_turn([])
        wait = p.observe('um')
        await wait.builder
        ready = p.observe('Chang')
        await ready.builder
        bundle = await p.finish('Chang')
        assert wait.retrieval is None
        assert [[v['id'] for v in views] for views in seen] == [[ready.id]]
        assert p.builder_requests == 2
        assert bundle.evidence[0].query.name == 'Chang'
    finally:
        assert await p.close() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('policy', ['time', 'text', 'hybrid'])
async def test_final_wait_skips_checker_even_with_existing_query(policy):
    p = make(trigger_policy=policy, min_interval=0, change_threshold=1)
    async def forbidden(*args):
        pytest.fail('Checker must not receive a final wait')
    p.checker.select = forbidden
    try:
        p.start_turn([])
        candidate = p.observe('Chang')
        await candidate.builder
        bundle = await p.finish('um')
        assert bundle.path == 'no_query' and not bundle.evidence
    finally:
        assert await p.close() == 0
