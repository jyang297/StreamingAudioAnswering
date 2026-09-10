"""Arithmetic/contract tests use explicit numeric vectors, NOT semantic-quality evidence."""
import math
import pytest
from rag_poc.semantic import cosine, query_text, SemanticChecker
from rag_poc.models import Query, ContractError


def test_cosine_arithmetic_only():
    assert cosine([1,0], [0,1]) == 0
    assert cosine([2,0], [1,0]) == 1
    assert cosine([1,0], [-1,0]) == -1
    for a,b in [([0,0],[1,0]),([1],[1,2]),([math.nan],[1])]:
        with pytest.raises(ContractError): cosine(a,b)


def test_representation_preserves_changes():
    a = query_text(Query(name='Chai', in_stock=True, min_price=10, limit=5))
    b = query_text(Query(name='Chang', in_stock=False, min_price=11, limit=6))
    assert a != b
    assert 'in_stock: True' in a and 'min_price: 10' in a and 'limit: 5' in a

@pytest.mark.parametrize('threshold', [float('nan'),-1.1,1.1])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError): SemanticChecker(None, threshold=threshold)

@pytest.mark.asyncio
async def test_no_candidates_never_infers():
    checker=SemanticChecker(None,threshold=.99)
    assert await checker.select('Chai',[],Query(name='Chai'),[]) is None
    assert checker.metrics[-1]['scores'] == []
