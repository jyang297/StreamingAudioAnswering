import pytest
from rag_poc.database import PostgresCatalog

@pytest.mark.asyncio
async def test_close_timeout_terminates_pool(caplog):
    class Pool:
        terminated = False
        async def close(self):
            raise TimeoutError()
        def terminate(self):
            self.terminated = True
    pool = Pool()
    await PostgresCatalog(pool).close()
    assert pool.terminated
    assert "pool terminated" in caplog.text

@pytest.mark.asyncio
async def test_other_close_failure_remains_visible():
    class Pool:
        async def close(self):
            raise RuntimeError("unexpected")
    with pytest.raises(RuntimeError, match="unexpected"):
        await PostgresCatalog(Pool()).close()
