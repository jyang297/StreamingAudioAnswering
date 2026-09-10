import asyncio
import pytest
from rag_poc.pipeline import Pipeline, changed_units
from test_pipeline import Builder, DB, Answer
from rag_poc.endpoints import ExactChecker


def make(**kwargs):
    return Pipeline(Builder(),ExactChecker(),DB(),Answer(),**kwargs)

async def until(predicate):
    async with asyncio.timeout(1):
        while not predicate(): await asyncio.sleep(.002)


def test_change_units_include_equal_length_revision_and_chinese():
    assert changed_units('Chai','Chao') == 1
    assert changed_units('有库存','无库存') == 1
    assert changed_units('a b','a') == 1

@pytest.mark.asyncio
async def test_time_coalesces_updates_without_losing_latest():
    p=make(trigger_policy='time',min_interval=.025)
    try:
        p.start_turn([])
        p.observe('a');p.observe('b');p.observe('latest')
        await until(lambda:len(p.builder.calls)==1)
        assert p.builder.calls[0][0]=='latest'
        await asyncio.sleep(.03)
        assert len(p.builder.calls)==1
    finally: assert await p.close()==0

@pytest.mark.asyncio
async def test_text_revisions_and_short_input_wait_until_final():
    p=make(trigger_policy='text',change_threshold=2)
    try:
        p.start_turn([]);p.observe('Chai')
        await asyncio.sleep(.02)
        assert not p.builder.calls
        result=await p.finish('Chai')
        assert p.builder.calls[0][1] is True
        assert result.evidence[0].query.name=='Chai'
    finally: assert await p.close()==0

@pytest.mark.asyncio
async def test_hybrid_flushes_short_input_on_deadline():
    p=make(trigger_policy='hybrid',change_threshold=5,min_interval=.02)
    try:
        p.start_turn([]);p.observe('Stock?')
        await until(lambda:len(p.builder.calls)==1)
        assert p.builder.calls[0][1] is False
    finally: assert await p.close()==0

@pytest.mark.asyncio
async def test_single_builder_and_only_latest_pending():
    p=make(trigger_policy='text',change_threshold=1)
    gate=asyncio.Event(); original=p.builder.build
    async def build(text,*args,**kwargs):
        if text=='first':await gate.wait()
        return await original(text,*args,**kwargs)
    p.builder.build=build
    try:
        p.start_turn([]);p.observe('first');await asyncio.sleep(0)
        p.observe('middle');p.observe('latest')
        assert len(p.candidates)==1
        gate.set()
        await until(lambda:len(p.builder.calls)==2)
        assert [c[0] for c in p.builder.calls]==['first','latest']
    finally:gate.set();assert await p.close()==0

@pytest.mark.asyncio
async def test_eot_adopts_matching_builder_and_drops_pending():
    p=make(trigger_policy='text',change_threshold=1,builder_grace=.1)
    original=p.builder.build
    async def build(*args,**kwargs):
        await asyncio.sleep(.015)
        return await original(*args,**kwargs)
    p.builder.build=build
    try:
        p.start_turn([]);p.observe('Chai');await asyncio.sleep(0)
        p.observe('pending')
        result=await p.finish('Chai')
        assert len(p.builder.calls)==1 and p.builder.calls[0][1] is False
        assert result.evidence[0].query.name=='Chai'
        await asyncio.sleep(.02);assert len(p.builder.calls)==1
    finally:assert await p.close()==0

@pytest.mark.asyncio
async def test_wait_does_not_exhaust_effective_candidate_quota():
    p=make(trigger_policy='text',change_threshold=1,max_candidates=1,max_builder_calls=3)
    try:
        p.start_turn([]);p.observe('um')
        await until(lambda:len(p.builder.calls)==1)
        p.observe('Chai')
        await until(lambda:len(p.retriever.calls)==1)
        result=await p.finish('Chai')
        assert result.path.startswith('reuse') and len(p.builder.calls)==2
    finally:assert await p.close()==0

@pytest.mark.asyncio
async def test_timer_cannot_publish_into_next_turn():
    p=make(trigger_policy='time',min_interval=.02)
    try:
        p.start_turn([]);p.observe('old')
        p.start_turn([]);p.observe('new')
        await until(lambda:len(p.builder.calls)==1)
        assert p.builder.calls[0][0]=='new'
    finally:assert await p.close()==0

@pytest.mark.asyncio
async def test_equal_length_replacement_triggers_text_policy():
    p=make(trigger_policy='text',change_threshold=1)
    try:
        p.start_turn([]);p.observe('Chai')
        await until(lambda:len(p.retriever.calls)==1)
        p.observe('Chao')
        await until(lambda:len(p.retriever.calls)==2)
        assert [c[0] for c in p.builder.calls]==['Chai','Chao']
    finally:assert await p.close()==0

@pytest.mark.asyncio
async def test_builder_budget_bounds_actual_requests():
    p=make(trigger_policy='text',change_threshold=1,max_builder_calls=2)
    try:
        p.start_turn([])
        for i,text in enumerate(['a','b']):
            p.observe(text);await until(lambda:len(p.builder.calls)==i+1)
        p.observe('c');await asyncio.sleep(.01)
        assert len(p.builder.calls)==2
        result=await p.finish('c')
        assert len(p.builder.calls)==3 and result.evidence[0].query.name=='c'
    finally:assert await p.close()==0

@pytest.mark.asyncio
async def test_same_text_handoff_timeout_cannot_publish_late():
    p=make(trigger_policy='text',change_threshold=1,builder_grace=.005)
    release=asyncio.Event();original=p.builder.build
    async def resistant(text,context,previous,*,final):
        if not final:
            try:await release.wait()
            except asyncio.CancelledError:await release.wait()
        return await original(text,context,previous,final=final)
    p.builder.build=resistant
    try:
        p.start_turn([]);old=p.observe('Chai');await asyncio.sleep(0)
        result=await p.finish('Chai')
        release.set();await asyncio.sleep(.01)
        assert result.path=='demand' and old.superseded and old.retrieval is None
        assert len(p.retriever.calls)==1
    finally:release.set();assert await p.close()==0
