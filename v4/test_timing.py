import asyncio
import json
import logging
import pytest
from rag_poc.timing import span

@pytest.mark.asyncio
async def test_nested_concurrent_spans_keep_ownership_and_status(caplog):
    caplog.set_level(logging.INFO, logger="rag_poc.timing")
    records = []
    async def work(turn):
        with span("turn", sink=records, turn=turn):
            with span("child"):
                await asyncio.sleep(0)
    await asyncio.gather(work(1), work(2))
    for turn in [1, 2]:
        parent = next(r for r in records if r['turn'] == turn and r['step'] == 'turn')
        child = next(r for r in records if r['turn'] == turn and r['step'] == 'child')
        assert child['parent_span_id'] == parent['span_id']
        assert child['time_spent_ms'] >= 0
        assert parent['time_spent_ms'] >= child['time_spent_ms']
    with pytest.raises(asyncio.CancelledError):
        with span("cancel", sink=records):
            raise asyncio.CancelledError()
    assert records[-1]['status'] == 'cancelled'
    with pytest.raises(ValueError):
        with span("error", sink=records):
            raise ValueError("sensitive detail must not be logged")
    assert records[-1]['error_type'] == 'ValueError'
    assert 'sensitive detail' not in caplog.text
    assert all('time_spent_ms' in json.loads(r.message) for r in caplog.records)
